from collections.abc import Iterator
from contextlib import contextmanager

import httpx
import pytest
from fastapi.testclient import TestClient
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from mealie.mcp.context import current_user_id
from mealie.mcp.recipes import register_recipe_tools
from mealie.pkgs.safehttp import FetchResult
from mealie.repos.repository_generic import GroupRepositoryGeneric
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
                        "values": {"calories": "240", "proteinContent": "4"},
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
        assert updated["nutrition"]["proteinContent"] is None
        assert updated["nutrition_provenance"]["calories"]["serving_basis"] == "per serving"

        _, results = await server.call_tool("search_recipes", {"search": name})
        assert [item["id"] for item in results["items"]] == [recipe_id]

        _, by_slug = await server.call_tool("get_recipe", {"recipe": recipe["slug"]})
        assert by_slug == updated

    with as_user(g2_user):
        with pytest.raises(ToolError, match="Recipe not found"):
            await server.call_tool("get_recipe", {"recipe": recipe_id})
        _, search = await server.call_tool("search_recipes", {"search": name})
        assert not search["items"]


@pytest.mark.asyncio
async def test_import_preserves_source_nutrition_and_only_fills_gaps(
    server: FastMCP, unique_user: TestUser, monkeypatch: pytest.MonkeyPatch
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

    monkeypatch.setattr(recipe_scraper, "resilient_fetch", fetch)
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
