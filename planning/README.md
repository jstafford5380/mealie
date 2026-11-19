# UI replacement catalog

This catalog supports a complete Vuetify replacement with Shadcn Vue.
Preserve each page's functions, permissions, data scope, and navigation.
Use the current source as the behavior contract.
Screenshots show the current UI, not a proposed design.

## Scope and evidence

- Inventory all 66 Vue files in `frontend/app/pages`, including parent routes and redirects.
- Write a separate document for each file.
- Trace controls into child components and composables.
- Capture each page and enough additional states to explain its functions.
- Include long-page content, tabs, menus, dialogs, forms, and applicable empty or error states.
- List remaining capture work explicitly. A single screenshot does not prove page coverage.
- Cover shared layouts, navigation, notifications, and non-route overlays separately.
- Catalog every existing Vue component for replacement or an explicit retention decision.

`route-manifest.json` tracks source coverage and page document status.
`TODO.md` tracks the catalog and migration work.
Each page document includes its source references, function checklist, state coverage, and screenshots.

Start with the [handoff and evidence limits](HANDOFF.md), [page index](PAGES.md), [component inventory](component-inventory.md), and [shared shell](shared-shell.md).
Use the [component replacement plan](component-migration-plan.md) for replacement order and proposed primitive mappings.
Use the [shared data-manager contract](shared-data-management.md) with each data-manager page.
Read the [recipe-page contract](shared-recipe-page.md), [recipe actions](shared-recipe-actions.md), [meal-plan contract](shared-meal-plan.md), and [shopping synchronization](shared-shopping-list-state.md) with their page documents.

To refresh the static source inventories, run `node planning/scripts/inventory.mjs`.
To check local links, source coverage, and JPEG files, run `node planning/scripts/check.mjs`.
These checks do not prove that a page's function checklist or screenshots are complete.

## How to use a page document

1. Read the page document and its shared-shell references.
2. Open every linked screenshot.
3. Read the linked source and the referenced child components.
4. Replace the UI with Shadcn Vue while preserving the function checklist.
5. Check each permission, validation rule, query parameter, and data operation.
6. Test the page with populated data, empty data, errors, and narrow screens.
7. Check keyboard access, focus restoration, accessible labels, and dark mode.
8. Mark a migration task complete only after its acceptance checks pass.

Do not remove a function because the screenshot does not show it.
Do not treat current UI defects as required design decisions.
Record any proposed behavior change separately from the component replacement.
Keep generated API types and backend contracts intact.
Only change `en-US` when new translation strings become necessary.

## Capture environment

Source baseline: commit `884f5ff40`.
The catalog uses a separate local checkout at `/tmp/mealie-ui-catalog` and its own Aspire data volumes.
The user's original checkout and database remain separate.
Use synthetic data only. Do not include real credentials or service secrets in screenshots.
The default account credentials can appear in the first-login help banner.
Label screenshots with the page, state, and viewport when relevant.

The catalog contains 423 linked screenshots across all 66 route contracts and shared controls. It is ready as a redesign reference. The page-level migration validation and optional evidence tasks remain open; this catalog does not certify runtime parity.
