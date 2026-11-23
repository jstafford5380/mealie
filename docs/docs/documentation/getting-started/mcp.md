# Connect Mealie to ChatGPT

Mealie can expose an authenticated MCP endpoint for one ChatGPT user. The tools can look up recipes and meals, create and edit recipes with nutrition, and schedule or update meals from your recipe library. Scaling can preview ingredient quantities or save a multiplier on a planned meal. Estimated nutrition is labeled in the recipe.

URL imports need a public page with structured recipe data. They save the recipe and its published nutrition when available. For pages without structured recipe data, supply the ingredients and instructions directly.

Use `list_categories`, `list_tags`, and `list_tools` to find existing recipe organizers in your Mealie group. Pass their IDs or exact slugs in the `categories`, `tags`, and `tools` arrays when calling `create_recipe` or `update_recipe`. On update, each supplied array replaces that recipe's corresponding assignments. Omit an array to keep its assignments, or send `[]` to clear them. To add one tag while keeping the others, read the recipe first and include its current tags alongside the new one.

Use `list_foods` to look up canonical ingredient IDs by name or browse your group's food catalog. Results include the stored name, plural name, and aliases. Follow `next_page` for more results.

### Structured ingredients

`get_recipe` returns the existing `ingredients` string array and a `structured_ingredients` array in the same order. The structured records include the native `referenceId`, `quantity`, `food`, `unit`, `note`, `originalText`, and `display` fields.

Use `list_units` to find unit IDs and any standard conversion mappings. Use `match_ingredient` to parse an ingredient and see exact food and unit candidates, including aliases. Review ambiguous matches before choosing IDs.

Pass strings, legacy objects with `quantity` and `text`, or canonical objects in the same recipe ingredient array. This example shows the arguments to `create_recipe` using an illustrative food ID.

```json
{
  "data": {
    "name": "Lemon dressing",
    "servings": 2,
    "ingredients": [
      {
        "quantity": 1,
        "food_id": "c9052338-d59c-4069-9df2-dbe1175e0a49",
        "unit_id": null,
        "note": "juiced",
        "original_text": "1 lemon, juiced"
      },
      "Salt to taste"
    ],
    "instructions": ["Mix and season to taste."]
  }
}
```

On update, omit `ingredients` to keep the list. A supplied array replaces it. Include the saved `referenceId` as `reference_id` on a retained canonical ingredient to preserve its instruction links. Strings and legacy quantity-and-text objects create new ingredient rows.

Call `preview_recipe_ingredient_normalization` with a recipe ID to review its current ingredients, proposals, and unresolved lines. The preview is read-only. To save reviewed changes, call `apply_recipe_ingredient_normalization` with the same `recipe_id`, the preview's `revision`, and a `changes` array containing only approved rows. Each change supplies `reference_id`, `food_id`, `quantity` (or null), and `unit_id` (or null for a unitless ingredient). Include a `note` if you want to replace the existing note. Use IDs from the current group. If the recipe changes after preview, request a fresh preview before applying.

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

If ChatGPT reports a timeout on a write, verify the recipe or meal in Mealie before asking it to try again. Live calendar tools write one entry at a time. The saved-plan tools write a complete reusable week in Meal Configurator.

## Plan full batches and leftovers

The meal's scale tracks how much is **eaten**. For a recipe that makes four servings, a scale of `0.25` plans one serving. The daily nutrition total counts that one serving whether the meal cooks a full batch, cooks a scaled portion, or uses leftovers.

### Live Meal Planner

1. Find the recipe and its base servings. Call `create_meal_plan_entry` with the date, meal type, and portion multiplier. For a full batch, also supply a fresh UUID in `recipe_batch_id`. A four-serving recipe with a meal scale of `0.25` leaves three servings. To cook only the planned portion, omit both batch fields.
2. Before using leftovers, call `list_leftover_batches` with the destination `date` and `entry_type`. Optionally filter by `recipe_id`. The result gives a `batch_id`, `base_servings`, and `remaining_servings` after accounting for portions already allocated to other meals, including future meals.
3. Create the later meal for the same recipe with the batch's `batch_id` as `leftover_batch_id`. Set `recipe_scale` to the desired servings divided by `base_servings`. To use the entire remainder, divide `remaining_servings` by `base_servings`. Using one serving from the four-serving recipe at `0.25` leaves two servings after the first meal.

Batch links apply to entries assigned to a specific day. When editing an existing meal, `update_meal_plan_entry` preserves an omitted batch ID and clears one sent as `null`. To switch between cooking a batch and using leftovers, clear the previous ID in the same update. Read what is already planned before retrying a timed-out write.

### Meal Configurator

Use `create_saved_meal_plan` for a reusable week. On the source weekday, set a fresh `recipeBatchId` and the portion eaten as `recipeScale`. On later weekdays, use the same `recipeId` and set `leftoverBatchId` to the source UUID. The portion multipliers across the source and its leftover meals must add up to at most `1.0`. For example, Monday dinner and Tuesday lunch can each use `recipeScale: 0.25` and leave half of the batch unallocated.

Use `get_saved_meal_plan` before `update_saved_meal_plan`, which replaces the full list. Keep the source and consumer links for entries you want to preserve. Batch IDs in a saved plan belong to that plan, and importing it into the calendar gives each batch a new ID.

Use `copy_saved_meal_plan` with the source `plan_id` to create an independent reusable week. Supply an optional `name` or use the default name with `(copy)` appended. The result includes the copy's new `id`, meals, and nutrition totals. Use that ID for edits to the copy.

Example request for ChatGPT. “Create a reusable week in Meal Configurator. Cook the full four-serving chicken recipe Monday, plan one serving for Monday dinner, then use one serving from the same batch for Tuesday lunch.”

### Read nutrition totals

`list_meal_plan` and `get_saved_meal_plan` include nutrition for each planned portion and totals for the full date range or saved week. Live calendar pages repeat the same totals, so use them once. Whole-week entries count once. Each portion uses the recipe's stored per-serving nutrition multiplied by the planned servings, even when the meal cooks a full batch or uses leftovers.

Values use kcal for calories, mg for sodium and cholesterol, and g for other nutrients. The totals add available amounts and mark nutrients that are missing from at least one entry, including meals entered as notes.

## Manage shopping lists

Use `list_shopping_lists` to find a household list and `get_shopping_list` to read its items, quantities, and checked states. Use `create_shopping_list` for a new list. Include both `start_date` and `end_date` to add ingredients from the live meal plan for that inclusive range.

List items include canonical `food_id` and `unit_id` when available, plus their recipe references and scales. The existing numeric `quantity` reflects Mealie's stored total. For a recipe-linked item with a stored total of zero, `measured_quantity` is null because Mealie stores missing recipe quantities as zero. Native consolidation uses food IDs and same or compatible units with configured standard conversions.

Use `add_shopping_list_items` to add groceries by name and quantity. Use `add_recipes_to_shopping_list` to add ingredients by recipe ID and scale. Use `update_shopping_list_item` with `checked: true` to mark an item as purchased. Supply only the fields you want to change.

Use `rename_shopping_list` to change its name and `remove_shopping_list_items` to remove specific entries by ID. Confirm the intended list before calling `delete_shopping_list`. If an add or create call times out, read the list before retrying.

## Coolify Compose

The `docker/docker-compose.coolify.yml` file includes an optional `mealie-tunnel` service. It uses Mealie's network namespace to reach the app through loopback.

Set `OPENAI_MCP_TUNNEL_ID` to the tunnel ID. Set `OPENAI_MCP_TUNNEL_KEY` to the restricted runtime key. Generate a separate random secret for `MCP_TUNNEL_ACCESS_TOKEN`. Store both secrets as runtime-only values in Coolify. The shared token makes MCP and its discovery route return 404 unless the request includes the token. OAuth still protects the tools.

Set `COMPOSE_PROFILES=mcp-tunnel` in the environment that runs Compose after you configure the secrets and the OAuth values. Set `MCP_ENABLED=true` and deploy. Check the tunnel logs for successful polling before you submit the ChatGPT form.
