# Shared data-management controls

Applies to page consumers of [GroupDataPage.vue](../frontend/app/components/Domain/Group/GroupDataPage.vue),
[CrudTable.vue](../frontend/app/components/global/CrudTable.vue), [AutoForm.vue](../frontend/app/components/global/AutoForm.vue),
and [BaseDialog.vue](../frontend/app/components/global/BaseDialog.vue).
Each data page adds its own fields, operations, and safety information.
Read both this contract and the page-specific contract before a replacement.

## Table functions

- Search the supplied records with the Search field.
- Show the configured columns and preserve custom cell renderers.
- When column selection is enabled, open the column menu and toggle each column independently.
- Preserve columns that start hidden, including record IDs.
- Keep the action column available independently of the selected data columns.
- Retain sortable columns, sort direction, pagination, page-size choices, item count, and empty-result presentation.
- The current table starts with 15 items per page.
- Keep row selection, Select All, and the partially selected state.
- Disable bulk Actions when no rows are selected.
- Send the selected records to the chosen bulk action and clear the selection afterward.
- Keep per-row Edit and Delete actions and their responsive button-group presentation.
- Download the full supplied data array as `export.json`; the source does not limit this to visible or selected records.
- Preserve page-specific actions in the top and bottom button slots.

Current-source audit notes:

- The Download button renders regardless of `tableConfig.canExport` in this source.
- `GroupDataPage` declares `initialSort` but does not pass it into `CrudTable`; do not infer a name sort from that unused prop.
- Record any corrected configuration behavior separately from the visual replacement.

## Create and edit dialogs

- Open the page-specific create or edit title and icon.
- Copy the selected record into the edit form.
- Render every field from the page's AutoForm definition.
- Disable Confirm until the corresponding form reports valid data.
- Emit the page's create or update operation with the complete form object.
- Cancel closes without the create/update request.
- Preserve any live previews and custom action slots supplied by the page.
- Do not assume Cancel clears the form values. The page owns its reset logic.

## Deletion review

- Single Delete shows a confirmation message and the record name, title, or ID.
- Bulk Delete shows all selected targets in a scrollable/virtualized review list.
- Preserve the page-specific safety content after the target list.
- Run any `onDeleteDialogOpen` callback before showing the review dialog.
- Cancel leaves the records unchanged.
- Only Confirm emits the deletion operation.

The [Categories page](pages/group--data--categories.md) includes captures of both deletion-review forms, column selection, and an empty search.
Do not remove these shared controls from another data page because its screenshots focus on specialized fields.

## Dialog and keyboard rules

- Use a bottom sheet at the smallest breakpoint when the page requests `bottom-sheet`.
- Other dialogs become fullscreen at the smallest breakpoint.
- Preserve title, icon, cancel action, confirm action, loading state, and width constraints.
- Escape and outside interaction emit Cancel. Closed dialogs emit Close for page cleanup.
- Enter confirms only when the confirm form is not disabled, unless the page disables Enter submission.
- Preserve `keepOpen` and loading-aware close behavior for submit/delete consumers.
- Retain custom action slots, focus trapping, and focus restoration.

## AutoForm field contract

- Preserve field name, model binding, label, section heading, explanation, hint, and column width.
- Support text, password, textarea, number, select, checkbox, and color fields.
- Preserve required and custom rules, input-time validation, disabled fields, and read-only fields.
- Respect create-only and update-only field restrictions.
- Preserve select value mapping and option text.
- Preserve numeric minimum, maximum, precision, and control configuration.
- Preserve checkbox help tooltips and persistent hints.
- Preserve auto-growing textareas and masked password fields.
- Replace the underlying primitives without changing the data shape expected by each consumer.

## Redesign (implemented)

All data pages share one layout now. Changes users will notice:

| Before | Now |
| --- | --- |
| A page banner with an illustration and a "Select data" dropdown button to switch between data types. | A "Data Management" heading with one row of tabs (Recipes, Recipe Actions · Foods, Units, Labels · Categories, Tags, Tools); it scrolls sideways on phones. |
| Section title with an icon; a gear button for columns, a disabled "Actions" menu until rows were picked, and an underlined search field. | Title with the record count; search, the page's own actions (outline buttons) and a primary "New …" button on one toolbar; a "…" menu holds the column toggles and "Download all as JSON". |
| Bulk actions lived in an overflow menu that stayed disabled with nothing selected. | Selecting rows shows a bar with "N selected", Clear, and each bulk action as its own button (Delete in red). Select All covers the current page and shows a dash when only some rows are picked. |
| Row Edit/Delete as a responsive button group. | Pencil and trash icon buttons at the end of each row, labelled with the record's name. |
| Vuetify footer pagination. | "1–15 of N", a Per page select (15, 30, 60, All) and previous/next buttons. Sort cycles ascending → descending → off. |
| Download sat in the table footer. | Download all as JSON is in the "…" menu; Seed sits in the footer as a quiet button. |
| Combine dialogs used Vuetify autocompletes. | Combine dialogs use searchable selects (accent- and case-insensitive) with the result spelled out before confirming. |
| Bulk delete listed targets in a virtual scroller. | A scrollable list of names. |
| Alias manager in a Vuetify grid. | One row per alias with a delete button and "Create alias" below, plus a line explaining what aliases do. |

The **Recipes** data page uses the same table (selection stays while its bulk dialogs are open), its own Export All button in the toolbar, and a plain exports table whose Purge button is disabled when there are no exports.

## Shared replacement checklist

- [x] Replace table rendering with Shadcn Vue Table/Data Table, Checkbox, Pagination, and menu primitives.
- [x] Replace create/edit dialogs with Dialog or Sheet, labeled fields, and explicit validation state.
- [x] Replace deletion review with Alert Dialog or an equivalent confirmation composition.
- [ ] Retain full target review and specialized deletion warnings.
- [ ] Preserve JSON download, column selection, sorting, searching, pagination, and bulk selection.
- [ ] Test empty data, a filtered-empty table, more than one page, and a long deletion target list.
- [ ] Test keyboard selection, Escape, Enter, mobile presentation, and restored focus.
