# Shared organizer browser

Applies to category, tag, and tool browsing pages. Source: [RecipeOrganizerPage.vue](../frontend/app/components/Domain/Recipe/RecipeOrganizerPage.vue), [RecipeOrganizerDialog.vue](../frontend/app/components/Domain/Recipe/RecipeOrganizerDialog.vue), [ContextMenu.vue](../frontend/app/components/global/ContextMenu.vue).

## Functions to preserve

- Autofocused, clearable search binds to `q` in the route. Replace the current query while preserving other query keys; do not add a browser-history entry per keystroke.
- Trim only the search expression, then use Fuse name matching with ignoreLocation, threshold 0.2, and minimum one character. A blank/whitespace query returns every item.
- Sort filtered records by locale name ordering and group by the uppercased first character. Show letter headings and responsive cards: full width through small, two columns at medium, three at large, four at extra large.
- A card navigates to `/g/{groupSlug}?{itemType}={itemId}`. Its context-menu button prevents navigation and offers Delete and Edit.
- Create opens a nested organizer dialog with a required translated name field. Tool creation additionally shows On Hand. Disable Create for an empty name; closing clears the name, while the component's On Hand ref is not explicitly reset.
- Create calls the appropriate category/tag/tool store with name and onHand, then closes. The shared creation dialog does not emit a new page-level mutation; store reactivity supplies the updated list.
- Edit deep-copies the selected item before opening. It contains Name and, for tools, On Hand. Confirm emits the complete draft; Cancel discards it. Unlike the create field, the update field has no explicit required validator in this component.
- Delete captures the target and opens a bottom-sheet confirmation containing the organizer type, warning, and target name. Confirm emits its ID; Cancel keeps it.
- Preserve the shared dialog's asynchronous/focus behavior and store mutation error feedback.
- No-match search currently leaves an empty card area with heading/Create/search still present; it does not render a dedicated empty-results message. A redesign can improve that feedback while keeping the clear-search recovery.
- Category/tag/tool routes all require authentication and the authenticated user's own group slug; `group-only` redirects a different group to `/`.

## Known accessibility issue to improve

The card context button has an icon without an accessible name, and its contents are nested inside a linked card. In captures it can be absent from the accessibility tree until opened. Use a named button with independent keyboard focus and retain the prevention of card navigation.

## Redesign (implemented)

| Before | Now |
| --- | --- |
| Outlined search field above a toolbar row holding the icon, title and Create. | Heading (the organizer type) with Create beside it, then a search field. |
| Letter sections with Vuetify card links; a context-menu button inside each card. | Letter headings over a grid of rows (1–4 columns by width); each row links to the filtered recipes and has its own labelled "…" menu with Edit and Delete. |
| No results left an empty area. | "No results" (or "Nothing here yet") appears when the list is empty. |
| Delete confirmation as a bottom sheet. | The standard dialog, with the target name highlighted. |


## Shadcn Vue replacement checklist

- [ ] Use Input with clear control, Card links, separately focusable DropdownMenu triggers, Dialog/Sheet, and Checkbox.
- [ ] Preserve `q` URL synchronization, query preservation, Fuse behavior, grouping, and responsive card counts.
- [ ] Preserve deep-copied edit drafts, store-driven creation, delete review, and own-group access.
- [ ] Add names to icon buttons and test focus return, Escape, Enter, and linked-card menu interactions.
