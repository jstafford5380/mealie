# Mealie ZIP recipe import

Route: `/g/:groupSlug/r/create/zip`.
Source: [zip.vue](../../frontend/app/pages/g/[groupSlug]/r/create/zip.vue).
Parent controls and access: [recipe creation](g--groupSlug--r--create.md).
Status: source contract and visual references reviewed; runtime validation remains in the checklists below.

## Functions to preserve

- Explain that this imports one recipe exported from another Mealie instance.
- Offer a clearable file field restricted to `.zip` selection.
- Show the selected filename and preserve long-filename handling.
- Keep the hint that ZIP files must come from a Mealie export.
- Disable Create when no file is selected.
- Upload the file as multipart field `archive` to `/api/recipes/create/zip`.
- Require HTTP `201` for success.
- Navigate to the returned recipe slug in the current route/session group.
- On upload or import failure, log the error and show the generic error toast.
- Clear the local loading state in `finally`.
- Retain the parent method menu and advanced-content migration link.

Current-source audit note: the button binds a loading ref, but this handler never sets it to true.
Do not assume the current UI prevents repeated upload requests while a request is active.

## Screenshot

![Mealie ZIP-import form](../screenshots/g--groupSlug--r--create--zip/01-file-form.jpg)

## Expanded file states

![Selected genuine export](../screenshots/g--groupSlug--r--create--zip/02-selected-file.jpg)
![Complete mobile file form](../screenshots/g--groupSlug--r--create--zip/03-mobile-selected-file.jpg)
![Cleared file state](../screenshots/g--groupSlug--r--create--zip/04-cleared-file.jpg)

![Successful ZIP import](../screenshots/g--groupSlug--r--create--zip/05-import-success.jpg)

The selected archive comes from the isolated catalog's synthetic soup recipe.
The importer creates Catalog Lentil Soup (1) and opens its recipe route.

## Migration validation

- [ ] Verify genuine single-recipe import, duplicate-name handling, and invalid archive feedback.
- [ ] Verify duplicate-submit protection and loading feedback; the baseline handler never sets loading true.

## Redesign (implemented)

| Before | Now |
| --- | --- |
| Each method was a flat card: title, paragraphs with cross-links, a rounded filled field, checkboxes stacked down the page and a centred pill Submit with the status text under it. | Each method is one panel: title and one-line explanation, labelled field, options in two columns, and a footer with the status on the left and a named action ("Import recipe", "Create recipe", "Debug") on the right. Links to the other methods sit under the panel. |
| Vuetify file input. | A "Choose .zip file" button with the chosen file name and a clear button. |


## Shadcn Vue replacement checklist

- [ ] Replace the FileInput, form layout, card sections, hint, icon, and Create button.
- [ ] Preserve `.zip` acceptance, filename display, clearing, and no-file gating.
- [ ] Preserve multipart field name, endpoint, success code, group route, and error toast.
- [ ] Test a genuine single-recipe Mealie export and an invalid archive.
