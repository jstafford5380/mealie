# Recipe context actions and nested dialogs

Sources: [menu wrapper](../frontend/app/components/Domain/Recipe/RecipeContextMenu/RecipeContextMenu.vue), [menu content](../frontend/app/components/Domain/Recipe/RecipeContextMenu/RecipeContextMenuContent.vue), [share dialog](../frontend/app/components/Domain/Recipe/RecipeDialogShare.vue), [shopping dialog](../frontend/app/components/Domain/Recipe/RecipeDialogAddToShoppingList.vue), [meal-plan dialog](../frontend/app/components/Domain/MealPlan/MealPlanAddRecipeDialog.vue), [print preferences](../frontend/app/components/Domain/Recipe/RecipeDialogPrintPreferences.vue).

## Functions: menu visibility and basic actions

- Load menu content asynchronously on first open, then retain it. Trigger prevents underlying card navigation. Preserve caller-specific includes, leading/appended events, positioning, and print-hidden controls.
- Default includes Edit, Delete, ZIP/PDF Download, Add to Plan/List, Print, Print Preferences, Share, and configured recipe actions; Duplicate defaults off. Public visibility applies only to entries marked public (Print/Print Preferences), and other entries require own-group context.
- Delete additionally requires administrator or recipe owner. Administrator deleting another owner's recipe sees distinct confirmation text. Confirm deletes, navigates to explorer when a slug is returned, and emits deleted; Cancel does not delete.
- Edit opens recipe route with `edit=true`. Duplicate reviews editable recipe name, calls duplicate endpoint, and navigates to returned slug.
- ZIP Download creates a share token for download access, handles missing-token failure, and downloads `{slug}.zip`. PDF shows Preparing PDF toast until download completes, closes the loader in finally, and names `{slug}.pdf`.
- Print emits to its parent. Print Preferences fetches complete recipe data if not already supplied, then opens preferences/preview.
- Configured recipe actions use the [action-data execution contract](pages/group--data--recipe-actions.md), including scale and share placeholders; Post adds sent/error feedback. The current executor requires `props.recipe`, not merely a fetched recipeRef.

## Sharing

- Before sharing, resolve recipe, group, and the recipe's own household (which may differ from current household). Plain-link eligibility requires matching group/household IDs, public group, public recipe-owning household, and public recipe setting.
- Fully public recipes use system share if supported, otherwise clipboard with success/failure/unsupported feedback. Plain URL omits private token and scale.
- Otherwise open Share Recipe. Each opening sets expiry to now plus 30 days, resets QR view, and refreshes all tokens for the recipe.
- Expiration field is read-only, opens a locale/household-week-start calendar, and closes that picker after date selection. New creates a token with ISO expiration and appends it.
- Token rows display expiration. Row click shares via system share or clipboard; separate Copy, Delete/revoke, and Show QR controls stop row propagation.
- Token URL is `{origin}/g/{groupSlug}/shared/r/{id}`. QR view renders that link, offers Back, scan guidance, and Download as a 1024px PNG named from the recipe.
- Preserve capability detection, clipboard errors, token refresh/revocation, and QR back navigation. Do not embed active credentials in planning screenshots; use revoked or explicitly synthetic fixtures when collecting result evidence.

## Add to meal plan

- Bottom-sheet dialog includes date picker, optional whole-week switch when preference mode is Weeks, and seven entry types: Breakfast, Lunch, Dinner (default), Side, Snack, Drink, Dessert.
- Date picker supports adjacent months, previous/next navigation, localized dates, and household first day. Fetch surrounding months' plans; distinguish days already planned for this entry type versus other types. Week entries do not count as a specific day's marker.
- Whole-week selection uses the household week boundary and displays start/end. Picking a date while range highlighting is active selects its containing week. API date/endDate are `yyyy-MM-dd`; a day entry sends null endDate.
- Confirm sends entry dates/type, recipe ID, caller scale, and empty title/text. HTTP 201 shows success with View action to planner; failure shows failure toast.

## Add to shopping list

- Fetch lists alphabetically and complete recipe ingredients as needed. Show All preference switches between current user's lists and all provided lists (the current filtering is by list user ID, not household slug).
- If exactly one visible list exists and Show All was not manually toggled, skip chooser and open ingredients. Otherwise show list cards, no-list state, Cancel, Show All, and New List.
- New List opens inline Name, Cancel, and Create; trim and require name, guard duplicate submission, show loading/failure. Enter submits. Success adds list to dialog and notifies parent so it remains available on reopen, then opens ingredients.
- Group ingredients by recipe and ingredient title; show parent-recipe tooltip for linked recipes and scale above one for multiple-recipe displays. Desktop uses two columns, small screens one; long contents scroll within 70vh.
- Expand referenced recipes recursively, applying parent ingredient quantity and recipe scale. Combine repeated top-level recipe slugs by increasing scale; subrecipe map keys use ID/slug and may overwrite repeated references—verify repeated/nested cases before altering consolidation.
- Household-on-hand foods start unchecked and move to the end of their ingredient section. Other ingredients start checked. Row click toggles; Check All/Uncheck All affect all sections.
- Add to List sends only checked ingredients per recipe with recipe ID and increment quantity/scale; omit sections with none selected. Show success with View link to target list or failure, then close/reset dialog state.
- On close reset selected list, sections, chooser mode, manual Show All marker, and new-list draft. Show All preference itself persists.

## Print preferences

- Persist mandatory image placement Left/Right/Hidden, Description, Notes, Nutrition, Include Linked Recipe Ingredients, Linked Ingredients, and Substitutions.
- Preview uses RecipePrintView in a 40vh scroll area; dialog width 70%, max 816px. Keep live preference response and complete print content during the recipe-page audit.

## Shadcn Vue replacement checklist

- [ ] Compose DropdownMenu, Dialog/Sheet, Calendar, Checkbox/Switch, Select, Button, QR/image preview, scrolling list, and feedback.
- [ ] Preserve every caller include, permission, scale, stored/requested recipe distinction, and public visibility check.
- [ ] Preserve token expiry/share/copy/revoke/QR, meal-plan markers/week boundaries, shopping ingredient grouping/selection, and print controls.
- [ ] Test keyboard focus through menu-to-dialog transitions, nested picker dismissal, async fetch failures, and return focus to the original card trigger.
