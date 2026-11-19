# Shared recipe cards and paged sections

Sources: [RecipeCardSection](../frontend/app/components/Domain/Recipe/RecipeCardSection.vue), [desktop card](../frontend/app/components/Domain/Recipe/RecipeCard.vue), [compact card](../frontend/app/components/Domain/Recipe/RecipeCardMobile.vue), [favorite](../frontend/app/components/Domain/Recipe/RecipeFavoriteBadge.vue), [rating](../frontend/app/components/Domain/Recipe/RecipeCardRating.vue), [image](../frontend/app/components/Domain/Recipe/RecipeCardImage.vue), [chips](../frontend/app/components/Domain/Recipe/RecipeChips.vue).

## Functions to preserve

- Toolbar may include title/icon, Random, Sort, and desktop Toggle View context menu. Caller flags can hide toolbar or sort; explorer supplies its own sort and disables the section sort.
- Random is disabled when the current recipe array is empty; otherwise request one matching recipe and navigate to its slug. Keep query restrictions and group context.
- Sort supports Alphabetical, Rating, Created, Updated, Last Made (own group only), Total Time, and Random. Repeating a sort toggles direction; first use defaults alphabetical/time ascending, rating/date/last-made descending. Random refreshes the seed.
- Persist sort, direction, icon, and compact-view preference. Public-group views replace an inherited Last Made sort with Created and hide that sort choice.
- Total Time puts missing values last in either direction. Other sorts default null placement based on direction unless the caller overrides it. Existing `filterNull` preference is not applied as a filter in this component.
- Compact cards are automatic through small screens, or chosen by desktop Toggle View. Desktop grid uses two medium/small, three large, four extra-large columns; compact supports single-column callers.
- First fetch requests 64 recipes, then subsequent 32-item pages using a 500ms-throttled intersection trigger. Preserve has-more/loading guards, query-change reset, stable random seed across pages, and append/replace events.
- Restore saved page and scroll position keyed by route path. When more than two pages were saved, preload the saved span before restoring position; disconnect observers/timeouts on unmount.
- Display loading recipes and scroll-to-top. No dedicated empty-results card is rendered by this shared section; callers may provide one.
- Own-group requests use authenticated API; other group requests use public explore API. Public/private route errors and safe login redirect follow useLazyRecipes.

## Card contents and interaction

- Name/image link to `/g/{groupSlug}/r/{slug}`. Missing recipe ID/slug suppresses the recipe route and actionable contents.
- Show versioned thumbnail at requested size; no image version skips the fetch and uses Mealie icon fallback. Failed load also falls back; changing ID/version retries.
- Desktop hover reveals sanitized Markdown description (bounded to eight lines). Compact cards show it inline, can use vertical image layout, and retain blank-description spacing.
- Show at most two tag chips. Chip click prevents card navigation and emits the tag/filter type; callers choose whether to apply a filter. Compact labels truncate; desktop chip CSS truncates long labels to available width.
- Own-group favorite control adds/removes current user's favorite and refreshes ratings, without opening the card. Keep its stateful tooltip and accessible name.
- Card stars are read-only. Prefer user's nonzero rating, otherwise group average in a distinct gray style. Render five full/half/empty stars, rounding a remainder of at least 0.25 to half. Provide a numeric accessible equivalent.
- Own-group card menus offer Download ZIP/PDF, Add to Plan, Add to List, and Share. Edit/Delete/Print/Print Preferences are explicitly off in card consumers. Their partial useItems object also does not enable custom recipe actions by default.
- Compact cards can carry recipe scale into their route query and action menu (e.g. meal-plan entries); selected-card mode suppresses normal navigation and emits selection.
- Preserve custom action slots and leading/appended context-menu entries for consumers such as meal plans.
- Full context-menu and nested dialog contracts: [shared recipe actions](shared-recipe-actions.md).

## Shadcn Vue replacement checklist

- [ ] Compose Card/linked article, Button, DropdownMenu, Tooltip, Badge, read-only rating output, Skeleton, and accessible compact/list alternatives.
- [ ] Preserve query scope, pagination/scroll restoration, sorting/null placement, seeded random order, and responsive preference.
- [ ] Preserve favorites, thumbnails/fallback, tag filter events, sanitized descriptions, scale propagation, and action configuration.
- [ ] Give favorite/menu/compact-toolbar icons names and avoid nested interactive elements inside an undifferentiated card link.
