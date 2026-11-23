from base64 import b64encode
from collections.abc import Iterator
from contextlib import contextmanager
from io import BytesIO
from uuid import UUID

import httpx
import pytest
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from PIL import Image
from sqlalchemy import update

from mealie.db.models.recipe.ingredient import RecipeIngredientModel
from mealie.mcp.context import current_user_id
from mealie.mcp.recipes import register_recipe_tools
from mealie.pkgs import safehttp
from mealie.pkgs.safehttp import FetchResult
from mealie.repos.repository_generic import GroupRepositoryGeneric
from mealie.schema.recipe.recipe_ingredient import IngredientFoodAliasCreate, IngredientFoodSave, IngredientUnitSave
from mealie.schema.recipe.recipe_organizers import CategorySave, TagSave, ToolSave
from mealie.schema.recipe.recipe_timeline_events import RecipeTimelineEventCreate
from mealie.services.scraper import recipe_scraper
from tests.utils import api_routes
from tests.utils.factories import random_string
from tests.utils.fixture_schemas import TestUser


@contextmanager
def as_user(user: TestUser) -> Iterator[None]:
    token = current_user_id.set(user.user_id)
    try:
        yield
    finally:
        current_user_id.reset(token)


@pytest.fixture
def server() -> FastMCP:
    server = FastMCP()
    register_recipe_tools(server)
    return server


@pytest.mark.asyncio
async def test_structured_ingredient_round_trip_and_review(
    server: FastMCP, api_client: TestClient, unique_user: TestUser, g2_user: TestUser
) -> None:
    food = unique_user.repos.ingredient_foods.create(
        IngredientFoodSave(name="lemon", plural_name="lemons", group_id=unique_user.group_id)
    )
    unit = unique_user.repos.ingredient_units.create(
        IngredientUnitSave(name="gram", abbreviation="g", group_id=unique_user.group_id)
    )
    foreign_food = g2_user.repos.ingredient_foods.create(IngredientFoodSave(name="lemon", group_id=g2_user.group_id))
    with as_user(unique_user):
        _, units = await server.call_tool("list_units", {"search": "gram"})
        assert str(unit.id) in {item["id"] for item in units["items"]}
        _, created = await server.call_tool(
            "create_recipe",
            {
                "data": {
                    "name": random_string(),
                    "servings": 1,
                    "ingredients": [
                        "2 lemons",
                        {"quantity": 1, "text": "pinch of salt"},
                        {"quantity": 30, "food_id": str(food.id), "unit_id": str(unit.id)},
                    ],
                    "instructions": ["Mix the ingredients."],
                }
            },
        )
        recipe_id = created["id"]
        original = created["structured_ingredients"]
        assert original[2]["food"]["id"] == str(food.id)
        assert original[2]["unit"]["id"] == str(unit.id)
        recipe_path = api_routes.recipes_slug(created["slug"])
        native = api_client.get(recipe_path, headers=unique_user.token).json()
        native["recipeInstructions"][0]["ingredientReferences"] = [{"referenceId": original[0]["referenceId"]}]
        response = api_client.put(recipe_path, json=native, headers=unique_user.token)
        assert response.status_code == 200, response.text
        unique_user.repos.session.execute(
            update(RecipeIngredientModel)
            .where(RecipeIngredientModel.recipe_id == UUID(recipe_id), RecipeIngredientModel.position == 1)
            .values(reference_id=None)
        )
        unique_user.repos.session.commit()
        _, created = await server.call_tool("get_recipe", {"recipe": recipe_id})
        original = created["structured_ingredients"]
        assert created["instructions"][0]["ingredientReferences"] == [{"referenceId": original[0]["referenceId"]}]
        _, preview = await server.call_tool("preview_recipe_ingredient_normalization", {"recipe_id": recipe_id})
        proposal = preview["changes"][0]["proposed"]
        assert proposal["food_id"] == str(food.id)
        assert proposal["quantity"] == 2
        assert proposal["unit_id"] is None
        _, unchanged = await server.call_tool("get_recipe", {"recipe": recipe_id})
        assert unchanged == created

        args = {"recipe_id": recipe_id, "revision": preview["revision"], "changes": [proposal]}
        await server.call_tool(
            "update_recipe", {"recipe_id": recipe_id, "changes": {"description": "Keep this recipe description."}}
        )
        with pytest.raises(ToolError, match="changed after preview"):
            await server.call_tool("apply_recipe_ingredient_normalization", args)
        _, preview = await server.call_tool("preview_recipe_ingredient_normalization", {"recipe_id": recipe_id})
        args["revision"] = preview["revision"]
        with pytest.raises(ToolError, match="food was not found"):
            await server.call_tool(
                "apply_recipe_ingredient_normalization",
                {**args, "changes": [{**proposal, "food_id": str(foreign_food.id)}]},
            )
        _, result = await server.call_tool("apply_recipe_ingredient_normalization", args)
        updated = result["recipe"]["structured_ingredients"]
        assert [item["referenceId"] for item in updated] == [item["referenceId"] for item in original]
        assert updated[0]["originalText"] == "2 lemons"
        assert updated[0]["food"]["id"] == str(food.id)
        assert updated[1:] == original[1:]
        assert result["recipe"]["description"] == "Keep this recipe description."
        assert result["recipe"]["instructions"] == created["instructions"]
        with pytest.raises(ToolError, match="changed after preview"):
            await server.call_tool("apply_recipe_ingredient_normalization", args)
        _, next_preview = await server.call_tool("preview_recipe_ingredient_normalization", {"recipe_id": recipe_id})
        assert updated[0]["referenceId"] not in {line["reference_id"] for line in next_preview["changes"]}
        _, edited = await server.call_tool(
            "update_recipe",
            {
                "recipe_id": recipe_id,
                "changes": {
                    "ingredients": [
                        {"food_id": str(food.id), "reference_id": updated[0]["referenceId"], "quantity": 3},
                        "Salt to taste",
                        {"food_id": str(food.id), "reference_id": updated[2]["referenceId"]},
                    ]
                },
            },
        )
        assert edited["structured_ingredients"][0]["quantity"] == 3
        assert edited["structured_ingredients"][2] == updated[2]
        assert edited["instructions"] == created["instructions"]


@pytest.mark.asyncio
async def test_match_ingredient_keeps_alias_collisions(server: FastMCP, unique_user: TestUser) -> None:
    foods = [
        unique_user.repos.ingredient_foods.create(
            IngredientFoodSave(
                name=name,
                aliases=[IngredientFoodAliasCreate(name="pepper")],
                group_id=unique_user.group_id,
            )
        )
        for name in ("bell pepper", "black pepper")
    ]
    with as_user(unique_user):
        _, match = await server.call_tool("match_ingredient", {"text": "1 pepper"})
        _, ranged = await server.call_tool("match_ingredient", {"text": "1-2 peppers"})
    assert match["requires_review"]
    assert {candidate["id"] for candidate in match["food_candidates"]} == {str(food.id) for food in foods}
    assert ranged["requires_review"]
    assert ranged["quantity"] is None
    assert ranged["measurement_to_review"] == "1-2"


@pytest.mark.asyncio
async def test_list_foods_returns_group_ids_and_paginates(
    server: FastMCP, unique_user: TestUser, g2_user: TestUser
) -> None:
    marker = random_string()
    food = unique_user.repos.ingredient_foods.create(
        IngredientFoodSave(
            name=f"{marker} bell pepper",
            plural_name=f"{marker} bell peppers",
            aliases=[IngredientFoodAliasCreate(name="capsicum")],
            group_id=unique_user.group_id,
        )
    )
    second = unique_user.repos.ingredient_foods.create(
        IngredientFoodSave(name=f"{marker} onion", group_id=unique_user.group_id)
    )
    g2_user.repos.ingredient_foods.create(IngredientFoodSave(name=f"{marker} tomato", group_id=g2_user.group_id))
    with as_user(unique_user):
        _, first_page = await server.call_tool("list_foods", {"search": marker, "per_page": 1})
        assert first_page == {
            "items": [
                {"id": str(food.id), "name": food.name, "plural_name": food.plural_name, "aliases": ["capsicum"]}
            ],
            "total": 2,
            "next_page": 2,
        }
        _, second_page = await server.call_tool("list_foods", {"search": marker, "per_page": 1, "page": 2})
        assert second_page["items"][0]["id"] == str(second.id)
        assert second_page["next_page"] is None


@pytest.mark.asyncio
async def test_recipe_organizers_list_and_assign_existing_group_values(
    server: FastMCP, api_client: TestClient, unique_user: TestUser, g2_user: TestUser
) -> None:
    routes = {
        "categories": api_routes.organizers_categories,
        "tags": api_routes.organizers_tags,
        "tools": api_routes.organizers_tools,
    }
    foreign_organizers = {
        "categories": g2_user.repos.categories.create(CategorySave(name=random_string(), group_id=g2_user.group_id)),
        "tags": g2_user.repos.tags.create(TagSave(name=random_string(), group_id=g2_user.group_id)),
        "tools": g2_user.repos.tools.create(ToolSave(name=random_string(), group_id=g2_user.group_id)),
    }
    organizers = {}
    for field, route in routes.items():
        local = api_client.post(route, json={"name": f"Local {field} {random_string()}"}, headers=unique_user.token)
        assert local.status_code == 201
        organizers[field] = (local.json(), foreign_organizers[field].model_dump(mode="json"))

    category, foreign_category = organizers["categories"]
    tag, foreign_tag = organizers["tags"]
    tool, foreign_tool = organizers["tools"]
    draft = {
        "name": random_string(),
        "servings": 2,
        "ingredients": ["1 cup rice"],
        "instructions": ["Cook the rice."],
        "categories": [category["id"], category["slug"]],
        "tags": [tag["slug"]],
        "tools": [tool["id"]],
    }
    with as_user(unique_user):
        for field, (local, foreign) in organizers.items():
            _, listed = await server.call_tool(f"list_{field}", {})
            assert {key: local[key] for key in ("id", "name", "slug")} in listed["result"]
            assert foreign["id"] not in {item["id"] for item in listed["result"]}

        with pytest.raises(ToolError, match="Unknown category"):
            await server.call_tool("create_recipe", {"data": {**draft, "categories": [foreign_category["slug"]]}})
        _, recipe = await server.call_tool("create_recipe", {"data": draft})
        recipe_id = recipe["id"]
        for field, (local, _) in organizers.items():
            assert [item["id"] for item in recipe[field]] == [local["id"]]

        with pytest.raises(ToolError, match="Unknown tag"):
            await server.call_tool(
                "update_recipe", {"recipe_id": recipe_id, "changes": {"categories": [], "tags": [foreign_tag["id"]]}}
            )
        with pytest.raises(ToolError, match="Unknown tool"):
            await server.call_tool(
                "update_recipe", {"recipe_id": recipe_id, "changes": {"tools": [foreign_tool["id"]]}}
            )

        _, updated = await server.call_tool(
            "update_recipe", {"recipe_id": recipe_id, "changes": {"tags": [], "tools": [tool["slug"]]}}
        )
        assert updated["categories"] == recipe["categories"]
        assert updated["tags"] == []
        assert updated["tools"] == recipe["tools"]
        _, loaded = await server.call_tool("get_recipe", {"recipe": recipe_id})
        assert loaded == updated

    response = api_client.get(api_routes.recipes_slug(recipe["slug"]), headers=unique_user.token)
    assert response.status_code == 200
    assert [item["id"] for item in response.json()["recipeCategory"]] == [category["id"]]
    assert response.json()["tags"] == []
    assert [item["id"] for item in response.json()["tools"]] == [tool["id"]]


@pytest.mark.asyncio
async def test_recipe_tools_save_scale_and_patch(
    server: FastMCP, api_client: TestClient, unique_user: TestUser, g2_user: TestUser
) -> None:
    name = random_string()
    with as_user(unique_user):
        _, recipe = await server.call_tool(
            "create_recipe",
            {
                "data": {
                    "name": name,
                    "servings": 2,
                    "yield_quantity": 6,
                    "yield_unit": "slices",
                    "ingredients": [{"quantity": 2, "text": "cups apples"}, "Salt to taste"],
                    "instructions": ["Mix and bake."],
                    "nutrition": {
                        "values": {"calories": 240, "proteinContent": 4},
                        "estimated_fields": ["calories"],
                        "estimate_basis": "Estimated from two cups of apples",
                        "serving_basis": "per serving",
                    },
                }
            },
        )
        recipe_id = recipe["id"]
        assert recipe["name"] == name
        assert recipe["url"].endswith(f"/r/{recipe['slug']}")
        assert recipe["nutrition"]["proteinContent"] == "4"
        assert recipe["nutrition_provenance"]["calories"]["source"] == "estimated"

        _, scale = await server.call_tool("preview_recipe_scale", {"recipe": recipe_id, "target_servings": 4})
        assert scale["multiplier"] == 2
        assert scale["yield_quantity"] == 12
        assert scale["ingredients"][0]["quantity"] == 4
        assert scale["ingredients"][1]["unscaled"]
        assert scale["ingredients"][1]["text"] == "Salt to taste"

        response = api_client.get(api_routes.recipes_slug(recipe["slug"]), headers=unique_user.token)
        assert response.status_code == 200
        assert response.json()["notes"][0]["title"] == "Estimated nutrition"
        assert response.json()["nutrition"]["calories"] == "240"

        _, updated = await server.call_tool(
            "update_recipe",
            {
                "recipe_id": recipe_id,
                "changes": {"description": "A fall dessert", "nutrition": {"values": {"proteinContent": None}}},
            },
        )
        assert updated["description"] == "A fall dessert"
        assert updated["servings"] == 2
        assert updated["ingredients"] == recipe["ingredients"]
        assert updated["instructions"] == recipe["instructions"]
        assert updated["nutrition"]["proteinContent"] is None
        assert updated["nutrition_provenance"]["calories"]["serving_basis"] == "per serving"

        _, results = await server.call_tool("search_recipes", {"search": name})
        assert [item["id"] for item in results["items"]] == [recipe_id]

        _, by_slug = await server.call_tool("get_recipe", {"recipe": recipe["slug"]})
        assert by_slug == updated

        await server.call_tool(
            "update_recipe", {"recipe_id": recipe_id, "changes": {"nutrition": {"values": {"calories": None}}}}
        )
        response = api_client.get(api_routes.recipes_slug(recipe["slug"]), headers=unique_user.token)
        assert response.status_code == 200
        assert response.json()["notes"] == []

    with as_user(g2_user):
        with pytest.raises(ToolError, match="Recipe not found"):
            await server.call_tool("get_recipe", {"recipe": recipe_id})
        _, search = await server.call_tool("search_recipes", {"search": name})
        assert not search["items"]


@pytest.mark.asyncio
async def test_backfill_nutrition_through_advertised_tool_schema(server: FastMCP, unique_user: TestUser) -> None:
    schemas = {tool.name: Draft202012Validator(tool.inputSchema) for tool in await server.list_tools()}
    data = {"name": random_string(), "servings": 2, "ingredients": ["Oats"], "instructions": ["Cook."]}
    nutrition = {
        "values": {"calories": 200, "proteinContent": "6", "fatContent": 2.5},
        "estimated_fields": ["calories", "protein_content"],
        "serving_basis": "per serving",
        "estimate_basis": "Calculated from the ingredient label.",
    }
    schemas["create_recipe"].validate({"data": data | {"nutrition": nutrition}})
    for field in ("name", "servings"):
        args = {"recipe_id": "1b67fb45-4ad1-4713-9904-3080e152a239", "changes": {field: None}}
        assert not schemas["update_recipe"].is_valid(args)
        with pytest.raises(ToolError):
            await server.call_tool("update_recipe", args)

    with as_user(unique_user):
        _, recipe = await server.call_tool("create_recipe", {"data": data})
        assert recipe["nutrition_provenance"] == {}
        assert recipe["nutrition"]["calories"] is None

        args = {"recipe_id": recipe["id"], "changes": {"nutrition": nutrition}}
        schemas["update_recipe"].validate(args)
        _, updated = await server.call_tool("update_recipe", args)
        _, saved = await server.call_tool("get_recipe", {"recipe": recipe["id"]})

        assert updated == saved
        assert saved["nutrition"]["fatContent"] == "2.5"
        assert saved["nutrition_provenance"]["fat_content"]["source"] == "user_provided"
        assert saved["nutrition_provenance"]["protein_content"] == {
            "value": "6",
            "source": "estimated",
            "serving_basis": "per serving",
            "estimate_basis": nutrition["estimate_basis"],
        }
        assert saved["instructions"] == recipe["instructions"]
        assert saved["ingredients"] == recipe["ingredients"]

        for malformed, message in [
            ({"values": {"protein": 5}}, "Extra inputs are not permitted"),
            ({"values": {"calories": "7 kcal"}}, "number or numeric string without units"),
            ({"values": {"calories": -1}}, "finite and nonnegative"),
            ({"values": {"calories": 5}, "estimated_fields": ["fat"]}, "non-null amount"),
            ({"values": {"calories": 5}, "estimated_fields": ["calories"]}, "basis for estimated nutrition"),
        ]:
            with pytest.raises(ToolError, match=message):
                await server.call_tool(
                    "update_recipe", {"recipe_id": recipe["id"], "changes": {"nutrition": malformed}}
                )

        _, unchanged = await server.call_tool("get_recipe", {"recipe": recipe["id"]})
        assert unchanged == saved


@pytest.mark.asyncio
@pytest.mark.parametrize("image_available", [True, False])
async def test_import_preserves_source_nutrition_and_only_fills_gaps(
    server: FastMCP,
    api_client: TestClient,
    unique_user: TestUser,
    monkeypatch: pytest.MonkeyPatch,
    image_available: bool,
) -> None:
    async def fetch(url: str, *, public_only: bool, max_bytes: int) -> FetchResult:
        assert public_only and max_bytes > 0
        return FetchResult(
            content=b"""
                <script type="application/ld+json">
                {
                  "@context":"https://schema.org",
                  "@type":"Recipe",
                  "name":"Apple slices",
                  "image":"https://cdn.recipe.example/apple.png",
                  "recipeYield":"2 servings",
                  "recipeIngredient":["2 apples"],
                  "recipeInstructions":["Slice the apples."],
                  "nutrition":{
                    "@type":"NutritionInformation",
                    "calories":"95 calories",
                    "servingSize":"1 apple"
                  }
                }
                </script>
            """,
            status_code=200,
            url=url,
            headers=httpx.Headers({"content-type": "text/html"}),
            encoding="utf-8",
        )

    async def fetch_image(url: str, *, public_only: bool, max_bytes: int, allow_flaresolverr: bool) -> FetchResult:
        assert url == "https://cdn.recipe.example/apple.png"
        assert public_only and not allow_flaresolverr
        assert max_bytes == 5 * 1024**2
        if not image_available:
            raise safehttp.ResponseTooLargeError("Image exceeds the download limit")
        image = BytesIO()
        Image.new("RGB", (32, 32), "red").save(image, format="PNG")
        return FetchResult(
            content=image.getvalue(),
            status_code=200,
            url=url,
            headers=httpx.Headers({"content-type": "image/png"}),
            encoding="utf-8",
        )

    monkeypatch.setattr(recipe_scraper, "resilient_fetch", fetch)
    monkeypatch.setattr(safehttp, "resilient_fetch", fetch_image)
    with as_user(unique_user):
        _, recipe = await server.call_tool(
            "import_recipe_url",
            {
                "url": "https://recipe.example/apple-slices",
                "nutrition": {
                    "values": {"calories": "20", "fiberContent": "4"},
                    "estimated_fields": ["calories", "fiberContent"],
                    "estimate_basis": "Average nutrition of a whole medium apple",
                    "serving_basis": "per apple",
                },
            },
        )

    assert recipe["nutrition"]["calories"] == "95"
    assert recipe["nutrition_provenance"]["calories"]["source"] == "published"
    assert recipe["nutrition_provenance"]["calories"]["serving_basis"] == "per 1 apple"
    assert recipe["nutrition"]["fiberContent"] == "4"
    assert recipe["nutrition_provenance"]["fiber_content"]["source"] == "estimated"
    assert "protein_content" in recipe["missing_nutrients"]
    stored = api_client.get(api_routes.recipes_slug(recipe["slug"]), headers=unique_user.token)
    assert stored.status_code == 200
    if image_available:
        assert stored.json()["image"]
        media = api_client.get(
            api_routes.media_recipes_recipe_id_images_file_name(recipe["id"], "original.webp"),
            headers=unique_user.token,
        )
        assert media.status_code == 200
        assert media.headers["content-type"] == "image/webp"
    else:
        assert stored.json()["image"] is None


@pytest.mark.asyncio
async def test_import_rejects_private_url(server: FastMCP, unique_user: TestUser) -> None:
    with as_user(unique_user), pytest.raises(ToolError, match="public HTTP"):
        await server.call_tool("import_recipe_url", {"url": "http://127.0.0.1/recipe"})


@pytest.mark.asyncio
async def test_recipe_create_rolls_back_if_timeline_write_fails(
    server: FastMCP, unique_user: TestUser, monkeypatch: pytest.MonkeyPatch
) -> None:
    native_create = GroupRepositoryGeneric.create

    def fail_timeline_create(self, data):
        if isinstance(data, RecipeTimelineEventCreate):
            raise RuntimeError("Timeline write failed")
        return native_create(self, data)

    monkeypatch.setattr(GroupRepositoryGeneric, "create", fail_timeline_create)
    name = random_string()
    with as_user(unique_user):
        with pytest.raises(ToolError):
            await server.call_tool(
                "create_recipe",
                {"data": {"name": name, "servings": 1, "ingredients": ["Salt"], "instructions": ["Season."]}},
            )
        _, search = await server.call_tool("search_recipes", {"search": name})
        assert not search["items"]


@pytest.mark.asyncio
async def test_recipe_tools_upload_and_replace_images(
    server: FastMCP, api_client: TestClient, unique_user: TestUser, monkeypatch: pytest.MonkeyPatch
) -> None:
    image_url = "https://cdn.recipe.example/meal.png"

    def png(color: str) -> bytes:
        buffer = BytesIO()
        Image.new("RGB", (32, 32), color).save(buffer, format="PNG")
        return buffer.getvalue()

    async def fetch(url: str, *, public_only: bool, max_bytes: int, allow_flaresolverr: bool) -> FetchResult:
        assert url == image_url
        assert public_only and not allow_flaresolverr
        assert max_bytes == 5 * 1024**2
        return FetchResult(png("blue"), 200, url, httpx.Headers({"content-type": "image/png"}), "utf-8")

    monkeypatch.setattr(safehttp, "resilient_fetch", fetch)
    data = {
        "name": random_string(),
        "servings": 1,
        "ingredients": ["1 apple"],
        "instructions": ["Slice the apple."],
        "image_base64": b64encode(png("red")).decode(),
    }
    both = data | {"image_url": image_url}
    tool = next(tool for tool in await server.list_tools() if tool.name == "create_recipe")
    assert not Draft202012Validator(tool.inputSchema).is_valid({"data": both})

    with as_user(unique_user):
        with pytest.raises(ToolError):
            await server.call_tool("create_recipe", {"data": both})
        with pytest.raises(ToolError, match="valid image"):
            await server.call_tool("create_recipe", {"data": data | {"image_base64": "YWJj"}})
        assert unique_user.repos.recipes.get_one(data["name"]) is None

        _, recipe = await server.call_tool("create_recipe", {"data": data})
        recipe_route = api_routes.recipes_slug(recipe["slug"])
        image_route = api_routes.media_recipes_recipe_id_images_file_name(recipe["id"], "original.webp")
        stored = api_client.get(recipe_route, headers=unique_user.token).json()
        original = api_client.get(image_route, headers=unique_user.token)
        assert stored["image"]
        assert original.status_code == 200

        with pytest.raises(ToolError, match="valid image"):
            await server.call_tool(
                "update_recipe",
                {"recipe_id": recipe["id"], "changes": {"description": "Discard this", "image_base64": "YWJj"}},
            )
        assert api_client.get(recipe_route, headers=unique_user.token).json()["description"] == stored["description"]
        assert api_client.get(image_route, headers=unique_user.token).content == original.content

        await server.call_tool("update_recipe", {"recipe_id": recipe["id"], "changes": {"image_url": image_url}})
        assert api_client.get(recipe_route, headers=unique_user.token).json()["image"] != stored["image"]
        replaced = api_client.get(image_route, headers=unique_user.token)
        assert replaced.status_code == 200
        assert replaced.content != original.content
