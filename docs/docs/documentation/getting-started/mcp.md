# Connect Mealie to ChatGPT

Mealie can expose an authenticated MCP endpoint for one ChatGPT user. The tools can look up recipes and meals, create and edit recipes with nutrition, and schedule or update meals from your recipe library. Scaling can preview ingredient quantities or save a multiplier on a planned meal. Estimated nutrition is labeled in the recipe.

URL imports need a public page with structured recipe data. They save the recipe and its published nutrition when available. For pages without structured recipe data, supply the ingredients and instructions directly.

## Before you begin

- Confirm that your ChatGPT account supports adding custom MCP servers and selecting an OpenAI Secure MCP Tunnel. Use the personal Platform organization for that account and associate the tunnel with the ChatGPT context where you will install the plugin.
- Create a dedicated non-admin Mealie user in the household you want ChatGPT to manage. Sign in as that user and read its `id` from `GET /api/users/self`.
- Choose an [OAuth provider compatible with ChatGPT](https://developers.openai.com/plugins/build/auth). Register the ChatGPT OAuth client with the exact redirect URI shown in the plugin management screen. Enable authorization code with PKCE (S256), publish OAuth discovery metadata, and configure the provider to issue RS256 JWT access tokens with the `mealie:mcp` scope. Your OAuth provider must be reachable independently of the tunnel.

## Enable MCP in Mealie

Set these environment variables on the Mealie backend and restart it.

| Variable | Value |
| --- | --- |
| `MCP_ENABLED` | `true` to enable the routes. The default is `false`. |
| `MCP_RESOURCE_URL` | The canonical HTTPS URL that identifies your private Mealie MCP endpoint, with the `/mcp` path. |
| `MCP_OAUTH_AUDIENCE` | The exact audience the provider puts in the access token. Secure MCP Tunnel rewrites the advertised resource URL for ChatGPT. When the provider uses that rewritten resource as the audience, configure the tunnel-facing HTTPS value here, typically `https://api.openai.com/v1/mcp/<tunnel_id>`. Defaults to `MCP_RESOURCE_URL`. |
| `MCP_OAUTH_ISSUER` | The exact HTTPS `issuer` advertised by the OAuth provider, including any trailing slash. |
| `MCP_OAUTH_JWKS_URL` | The provider's HTTPS JWKS URL used to verify access token signatures. |
| `MCP_OAUTH_SUBJECT` | The exact `sub` claim for the OAuth user who may use the integration. |
| `MCP_USER_ID` | The dedicated Mealie user's UUID. |

The OAuth identity must present a valid access token on every MCP request. Tool discovery can still succeed if the mapped Mealie user is later removed, locked, or made an administrator. Data tools check the account on each call and refuse access in those cases.

## Connect the tunnel

1. Create a tunnel and its restricted runtime key in [OpenAI Platform tunnel settings](https://platform.openai.com/settings/organization/tunnels). The [Secure MCP Tunnel guide](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels) documents permissions, installation, and key configuration.
2. Run `tunnel-client` alongside Mealie. Create an OAuth-enabled HTTP profile and point it at the private listener. If using a private HTTPS proxy, preserve an allowed host such as the host in `BASE_URL` and route both `/mcp` and `/.well-known/oauth-protected-resource/mcp` to Mealie. For local development with `http://127.0.0.1:9000/mcp`, the services must share a network namespace and the tunnel client must set `HARPOON_ALLOW_PLAINTEXT_HTTP=true`. Deny both MCP paths at existing public Mealie proxies.
3. Initialize the profile using the tunnel ID and private HTTPS endpoint. Set the runtime key as described in the tunnel guide. Check the profile and keep the client running during discovery and use.

    ```sh
    tunnel-client init --sample sample_mcp_with_dcr --profile mealie \
      --tunnel-id "$MEALIE_TUNNEL_ID" --mcp-server-url "$MEALIE_PRIVATE_MCP_URL"
    tunnel-client doctor --profile mealie --explain
    tunnel-client run --profile mealie
    ```

4. In ChatGPT on the web, open Plugins and choose **Add custom MCP server**. Select **Tunnel**, choose your tunnel, and configure **OAuth** with the registered client. Create and install the plugin.
5. Ask ChatGPT to list recipes. In a test household, ask it to create a test recipe and add it to a planned meal. Confirm both records in Mealie.

If ChatGPT reports a timeout on a write, verify the recipe or meal in Mealie before asking it to try again. Weekly plans are saved one entry at a time, so a partially successful plan can be completed by adding just the missing entries.

## Coolify Compose

The `docker/docker-compose.coolify.yml` file includes an optional `mealie-tunnel` service. It uses Mealie's network namespace to reach the app through loopback.

Set `OPENAI_MCP_TUNNEL_ID` to the tunnel ID. Set `OPENAI_MCP_TUNNEL_KEY` to the restricted runtime key. Generate a separate random secret for `MCP_TUNNEL_ACCESS_TOKEN`. Store both secrets as runtime-only values in Coolify. The shared token makes MCP and its discovery route return 404 unless the request includes the token. OAuth still protects the tools.

Set `COMPOSE_PROFILES=mcp-tunnel` in the environment that runs Compose after you configure the secrets and the OAuth values. Set `MCP_ENABLED=true` and deploy. Check the tunnel logs for successful polling before you submit the ChatGPT form.
