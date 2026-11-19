# Category browser

Route: `/g/:groupSlug/recipes/categories`. Source: [index.vue](../../frontend/app/pages/g/[groupSlug]/recipes/categories/index.vue).

## Functions to preserve

- Require authentication and own-group membership; set the localized Categories page title and icon.
- Render the category store using the entire [shared organizer browser contract](../shared-organizer-browser.md): URL-backed fuzzy search, clear, alphabetical grouping, responsive cards, recipe-filter links, Create, context Edit, and reviewed Delete.
- Delegate update/delete to category store actions. Create uses the category store from the shared dialog. Refresh and error feedback must remain visible.
- Category links use `categories={id}` on the group recipe explorer. Category create requires Category Name; update uses a copied Name draft.

## Screenshots

### Full category browser and card context menu

![Category browser](../screenshots/g--groupSlug--recipes--categories--index/01-full-page.jpg)
![Card context menu](../screenshots/g--groupSlug--recipes--categories--index/02-context-menu.jpg)

### Edit and create dialogs

![Category edit](../screenshots/g--groupSlug--recipes--categories--index/03-edit-dialog.jpg)
![Category create](../screenshots/g--groupSlug--recipes--categories--index/04-create-dialog.jpg)

### No-match search with URL query

![No matching categories](../screenshots/g--groupSlug--recipes--categories--index/05-search-empty.jpg)

### Category review, mobile, and recipe destination

![Category deletion review](../screenshots/g--groupSlug--recipes--categories--index/06-delete-review.jpg)
![Complete mobile category browser](../screenshots/g--groupSlug--recipes--categories--index/07-mobile-full-page.jpg)
![Category-filtered recipe](../screenshots/g--groupSlug--recipes--categories--index/08-filtered-recipes.jpg)

## Migration validation

- [ ] Verify keyboard navigation and focus return after the nested menu/dialog.

## Shadcn Vue replacement checklist

- [ ] Apply every shared organizer-browser replacement task.
- [ ] Preserve category-specific fields, icon, store calls, title, and explorer query key.
