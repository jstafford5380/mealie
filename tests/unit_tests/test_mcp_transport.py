from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from json import loads
from time import time
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import FastAPI
from jsonschema import Draft202012Validator
from pydantic import SecretStr
from starlette.testclient import TestClient

from mealie.core.config import get_app_settings
from mealie.mcp.context import current_user_id
from mealie.mcp.server import MCP_SCOPE, TUNNEL_HEADER, OAuthAccessTokenVerifier, build_mcp_server
from tests.utils import TestUser

ISSUER = "https://identity.example.com/"
RESOURCE = "https://mealie-mcp.example.com/mcp"
JWKS = f"{ISSUER}.well-known/jwks.json"
SUBJECT = "approved-user"


@pytest.fixture(scope="module")
def signing_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture
def sign_token(signing_key: rsa.RSAPrivateKey, monkeypatch: pytest.MonkeyPatch) -> Callable[..., str]:
    public_key = jwt.PyJWK.from_dict(
        {**jwt.algorithms.RSAAlgorithm.to_jwk(signing_key.public_key(), as_dict=True), "kid": "test-key"}
    )
    monkeypatch.setattr(jwt.PyJWKClient, "get_signing_keys", lambda _: [public_key])

    def sign(**overrides: Any) -> str:
        return jwt.encode(
            {
                "iss": ISSUER,
                "aud": RESOURCE,
                "sub": SUBJECT,
                "scope": MCP_SCOPE,
                "exp": int(time()) + 60,
                **overrides,
            },
            signing_key,
            algorithm="RS256",
            headers={"kid": "test-key"},
        )

    return sign


@pytest.mark.parametrize(
    "overrides",
    [
        {"iss": "https://other.example.com/"},
        {"aud": "https://other.example.com/mcp"},
        {"sub": "unapproved-user"},
        {"scope": "mealie:other"},
        {"exp": 0},
    ],
)
def test_rejects_invalid_access_token(sign_token: Callable[..., str], overrides: dict[str, Any]) -> None:
    verifier = OAuthAccessTokenVerifier(issuer=ISSUER, audience=RESOURCE, jwks_url=JWKS, subject=SUBJECT)

    assert verifier.verify(sign_token())
    assert not verifier.verify(sign_token(**overrides))


def test_mcp_http_authenticated_read_and_write(
    sign_token: Callable[..., str],
    unique_user: TestUser,
) -> None:
    user_id = unique_user.user_id
    tunnel_audience = "https://api.openai.com/v1/mcp/tunnel_test"
    tunnel_headers = {TUNNEL_HEADER: "test-tunnel-token"}
    settings = get_app_settings().model_copy(
        update={
            "MCP_RESOURCE_URL": RESOURCE,
            "MCP_OAUTH_AUDIENCE": tunnel_audience,
            "MCP_OAUTH_ISSUER": ISSUER,
            "MCP_OAUTH_JWKS_URL": JWKS,
            "MCP_OAUTH_SUBJECT": SUBJECT,
            "MCP_USER_ID": user_id,
            "MCP_TUNNEL_ACCESS_TOKEN": SecretStr(tunnel_headers[TUNNEL_HEADER]),
        }
    )
    server, routes = build_mcp_server(settings)

    @server.tool()
    def check_user_context() -> str:
        return str(current_user_id.get())

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        async with server.session_manager.run():
            yield

    app = FastAPI(lifespan=lifespan)
    app.router.routes.extend(routes)

    with TestClient(app, base_url="http://localhost:9000") as client:
        metadata_path = "/.well-known/oauth-protected-resource/mcp"
        assert client.get(metadata_path).status_code == 404
        assert client.post("/mcp").status_code == 404
        metadata = client.get(metadata_path, headers=tunnel_headers)
        assert metadata.status_code == 200
        assert metadata.json()["resource"] == RESOURCE

        headers = {"Accept": "application/json, text/event-stream", **tunnel_headers}
        init = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-11-25",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1"},
            },
        }
        refused = client.post("/mcp", json=init, headers=headers)
        assert refused.status_code == 401
        assert metadata_path in refused.headers["WWW-Authenticate"]

        headers["Authorization"] = f"Bearer {sign_token()}"
        assert client.post("/mcp", json=init, headers=headers).status_code == 401

        headers["Authorization"] = f"Bearer {sign_token(aud=tunnel_audience)}"
        initialized = client.post("/mcp", json=init, headers=headers)
        assert initialized.status_code == 200
        assert initialized.json()["result"]["serverInfo"]["name"] == "Mealie"
        headers["MCP-Protocol-Version"] = initialized.json()["result"]["protocolVersion"]

        listed = client.post("/mcp", json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, headers=headers)
        assert listed.status_code == 200
        tools = {tool["name"]: tool for tool in listed.json()["result"]["tools"]}
        reads = {
            "search_recipes",
            "get_recipe",
            "preview_recipe_scale",
            "list_categories",
            "list_tags",
            "list_tools",
            "list_meal_plan",
            "list_leftover_batches",
            "list_saved_meal_plans",
            "get_saved_meal_plan",
        }
        writes = {
            "create_recipe",
            "import_recipe_url",
            "update_recipe",
            "create_meal_plan_entry",
            "update_meal_plan_entry",
            "create_saved_meal_plan",
            "update_saved_meal_plan",
            "copy_saved_meal_plan",
        }
        assert tools.keys() == reads | writes | {"check_user_context"}
        assert all(tools[name]["annotations"]["readOnlyHint"] is True for name in reads)
        assert all(tools[name]["annotations"]["readOnlyHint"] is False for name in writes)

        for name, envelope in (("create_recipe", "data"), ("update_recipe", "changes")):
            tool = tools[name]
            schema = tool["inputSchema"]
            assert "NutritionInput" in schema["$defs"]
            assert "values" in schema["$defs"]["NutritionInput"]["required"]
            validator = Draft202012Validator(schema)
            example = loads(tool["description"].split("Example request:\n", 1)[1])
            validator.validate(example)

            values = example[envelope]["nutrition"]["values"]
            values["proteinContent"] = 37
            validator.validate(example)
            values["protein_content"] = values.pop("proteinContent")
            assert not validator.is_valid(example)

        def call(request_id: int, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
            response = client.post(
                "/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "method": "tools/call",
                    "params": {"name": name, "arguments": arguments},
                },
                headers=headers,
            )
            assert response.status_code == 200
            result = response.json()["result"]
            assert not result.get("isError"), result
            return result["structuredContent"]

        assert call(3, "check_user_context", {}) == {"result": str(user_id)}
        recipe = call(
            4,
            "create_recipe",
            {
                "data": {
                    "name": "MCP test toast",
                    "servings": 2,
                    "ingredients": [{"quantity": 2, "text": "slices of bread"}],
                    "instructions": ["Toast the bread."],
                },
            },
        )
        assert call(5, "get_recipe", {"recipe": recipe["id"]})["id"] == recipe["id"]
        entry = call(
            6,
            "create_meal_plan_entry",
            {"date": "2030-03-28", "entry_type": "dinner", "recipe_id": recipe["id"], "recipe_scale": 2},
        )
        assert entry["recipe_scale"] == 2
        assert call(7, "list_meal_plan", {"start_date": "2030-03-28", "end_date": "2030-03-28"})["entries"] == [entry]
