"""Authenticated Streamable HTTP transport for the Mealie MCP tools."""

from hmac import compare_digest
from urllib.parse import urlsplit, urlunsplit
from uuid import UUID

import jwt
from mcp.server.transport_security import TransportSecuritySettings
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import Headers
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from starlette.types import ASGIApp, Receive, Scope, Send

from mealie.core.settings.settings import AppSettings
from mealie.mcp.audit import AuditedMCP
from mealie.mcp.context import current_user_id

MCP_PATH = "/mcp"
MCP_SCOPE = "mealie:mcp"
TUNNEL_HEADER = "X-Mealie-Tunnel-Token"


class PrivateTunnelRoute:
    def __init__(self, app: ASGIApp, token: str) -> None:
        self.app = app
        self.token = token.encode()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        supplied = Headers(scope=scope).get(TUNNEL_HEADER, "").encode()
        if not compare_digest(supplied, self.token):
            await Response(status_code=404)(scope, receive, send)
            return
        await self.app(scope, receive, send)


def _https_url(value: str | None, setting: str) -> str:
    if value and not any(char.isspace() or char in '"\\' for char in value):
        url = urlsplit(value)
        if url.scheme == "https" and url.hostname and not (url.username or url.password or url.query or url.fragment):
            return value
    raise ValueError(f"{setting} must be an HTTPS URL without credentials, a query, or a fragment")


class OAuthAccessTokenVerifier:
    def __init__(self, *, issuer: str, audience: str, jwks_url: str, subject: str) -> None:
        self.issuer = issuer
        self.audience = audience
        self.subject = subject
        self.keys = jwt.PyJWKClient(jwks_url, timeout=5)

    def verify(self, token: str) -> bool:
        try:
            header = jwt.get_unverified_header(token)
            key_id = header.get("kid")
            if header.get("alg") != "RS256" or not isinstance(key_id, str):
                return False

            # Use the JWKS cache even for an unknown kid, so invalid tokens can't force key fetches per request.
            signing_key = next(
                (key for key in self.keys.get_signing_keys() if key.key_id == key_id and key.algorithm_name == "RS256"),
                None,
            )
            if signing_key is None:
                return False

            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=self.issuer,
                subject=self.subject,
                options={"require": ["iss", "aud", "exp", "sub", "scope"]},
            )
            scope = claims["scope"]
            return isinstance(scope, str) and MCP_SCOPE in scope.split()
        except jwt.PyJWTError, OSError, ValueError, TypeError:
            return False


class AuthenticatedMCP:
    def __init__(
        self,
        app: ASGIApp,
        *,
        verifier: OAuthAccessTokenVerifier,
        user_id: UUID,
        metadata_url: str,
    ) -> None:
        self.app = app
        self.verifier = verifier
        self.user_id = user_id
        self.challenge = f'Bearer resource_metadata="{metadata_url}", scope="{MCP_SCOPE}"'

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return

        scheme, _, credential = Headers(scope=scope).get("authorization", "").partition(" ")
        if (
            scheme.lower() != "bearer"
            or not credential
            or not await run_in_threadpool(self.verifier.verify, credential)
        ):
            response = JSONResponse(
                {"error": "unauthorized"},
                status_code=401,
                headers={"WWW-Authenticate": self.challenge, "Cache-Control": "no-store"},
            )
            await response(scope, receive, send)
            return

        context_token = current_user_id.set(self.user_id)
        try:
            await self.app(scope, receive, send)
        finally:
            current_user_id.reset(context_token)


def build_mcp_server(settings: AppSettings) -> tuple[AuditedMCP, tuple[Route, Route]]:
    from mealie.mcp.meal_plan import register_meal_plan_tools
    from mealie.mcp.recipes import register_recipe_tools

    resource = _https_url(settings.MCP_RESOURCE_URL, "MCP_RESOURCE_URL")
    resource_parts = urlsplit(resource)
    if resource_parts.path != MCP_PATH:
        raise ValueError("MCP_RESOURCE_URL must use the /mcp path")

    issuer = _https_url(settings.MCP_OAUTH_ISSUER, "MCP_OAUTH_ISSUER")
    jwks_url = _https_url(settings.MCP_OAUTH_JWKS_URL, "MCP_OAUTH_JWKS_URL")
    audience = _https_url(settings.MCP_OAUTH_AUDIENCE or resource, "MCP_OAUTH_AUDIENCE")
    subject = settings.MCP_OAUTH_SUBJECT
    user_id = settings.MCP_USER_ID
    if not subject or not user_id:
        raise ValueError("MCP_OAUTH_SUBJECT and MCP_USER_ID are required when MCP_ENABLED is true")

    server = AuditedMCP(
        "Mealie",
        instructions=(
            "Manage recipes and household meal plans in Mealie. "
            "Use saved meal plan tools for reusable weeks in Meal Configurator. "
            "Write to the live calendar only when the user explicitly asks to schedule meals there. "
            "Scale previews are read-only. To persist a scale, update the meal-plan entry's multiplier. "
            "Keep estimated nutrition distinct from published values."
        ),
        streamable_http_path=MCP_PATH,
        stateless_http=True,
        json_response=True,
        transport_security=TransportSecuritySettings(
            allowed_hosts=[
                "localhost",
                "localhost:*",
                "127.0.0.1",
                "127.0.0.1:*",
                "[::1]",
                "[::1]:*",
                resource_parts.netloc,
                urlsplit(settings.BASE_URL).netloc,
            ],
            allowed_origins=["https://chatgpt.com"],
        ),
    )
    register_recipe_tools(server)
    register_meal_plan_tools(server)

    metadata_path = f"/.well-known/oauth-protected-resource{MCP_PATH}"
    metadata_url = urlunsplit((resource_parts.scheme, resource_parts.netloc, metadata_path, "", ""))
    tunnel_token = settings.MCP_TUNNEL_ACCESS_TOKEN
    if tunnel_token and tunnel_token.get_secret_value():
        metadata_url = f"http://127.0.0.1:{settings.API_PORT}{metadata_path}"

    async def metadata(_: Request) -> JSONResponse:
        return JSONResponse(
            {
                "resource": resource,
                "authorization_servers": [issuer],
                "scopes_supported": [MCP_SCOPE],
                "bearer_methods_supported": ["header"],
            }
        )

    endpoint: ASGIApp = AuthenticatedMCP(
        server.streamable_http_app(),
        verifier=OAuthAccessTokenVerifier(issuer=issuer, audience=audience, jwks_url=jwks_url, subject=subject),
        user_id=user_id,
        metadata_url=metadata_url,
    )
    metadata_route = Route(metadata_path, metadata)
    if tunnel_token and (token := tunnel_token.get_secret_value()):
        endpoint = PrivateTunnelRoute(endpoint, token)
        metadata_route = Route(metadata_path, PrivateTunnelRoute(metadata_route.app, token), methods=["GET"])
    return server, (Route(MCP_PATH, endpoint, methods=["GET", "POST", "DELETE"]), metadata_route)
