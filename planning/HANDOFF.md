# Redesign handoff

Start with [README](README.md), [all 66 page contracts](PAGES.md), [component tasks](component-inventory.md), and [replacement order](component-migration-plan.md).

The catalog contains 423 screenshots, 66 route documents, a Nuxt error-page document, and an inventory of all 169 Vue components. Every screenshot is linked from a contract. Long pages have full-page references; important menus, dialogs, nested forms, results, mobile layouts, and readable sections have additional images. Wrapper and redirect routes deliberately reference their rendered destination instead of inventing a separate screen.

For each page, read its function list and every linked shared contract before redesigning it. Screenshots explain presentation; source references explain permissions, payloads, validation, state transitions, and functions hidden by the current fixture. A function remains required even when it is not visible in the screenshot. Keep the page's replacement checklist open until the migrated behavior passes validation.

## Evidence decisions

- Shared controls are documented once and referenced by consumers. The category data manager captures shared table columns, target reviews, and selection behavior. Foods and Units add selected merge examples, nested forms, aliases, and affected-recipe reviews. These references also apply to the corresponding tag, tool, label, and action managers; their page contracts specify the differences.
- Recipe reader/editor, cards/actions, query filters, meal planning, and shopping synchronization each have separate shared contracts. The recipe page alone has 35 linked states. Do not substitute its initial reader screenshot for its editor or Cook modes.
- Setup's later steps, registration confirmation, API-token results, invitation results, and reset-link results include explicitly labeled source-rendered previews. Their temporary initializers were used only in the isolated capture checkout and restored. They show actual templates with synthetic values, not proof that an account or credential operation completed.
- Successful and failed imports have live local-fixture evidence. Provider diagnostics demonstrate a local failure. Successful external AI extraction, OIDC/reverse-proxy providers, and every response-message permutation are specified from source and remain migration tests; they are not claimed as executed workflows.
- Permission variants, offline/reconnect conflicts, touch/RTL behavior, large-page pagination, destructive restore/cleanup, and credential changes have source contracts and explicit validation tasks. The catalog is a redesign reference, not certification that all runtime combinations passed.
- Remaining page-level evidence requests are retained as migration validation or optional additional references. Capture them when exercising those branches during replacement. They do not authorize omitting the associated functions.

## Baseline defects and limits

- The mobile shopping quick-add drawer clips Save at 390×844; scrolling inside it did not reveal the control. Fix reachability while preserving Save.
- Some mobile tables overflow horizontally. Desktop references show the remaining columns; preserve their data and provide a usable narrow-screen presentation.
- Raw HTML/JSON failure handling can trigger a Vue i18n syntax overlay because the English generic message contains unescaped linked-format markers. The page document records the observed failure.
- Several handlers do not await validation, some loading refs never drive visible progress, and several drafts do not reset as expected. The contracts distinguish observed baseline behavior from the validation intent. Correct defects deliberately and record behavior changes.
- A native time-picker popup was accessible to automation but absent from browser screenshots. The webhook contract records the limit rather than labeling an invisible popup as captured.

## Suggested instruction for Claude

> Read planning/README.md, planning/HANDOFF.md, planning/PAGES.md, and planning/component-migration-plan.md. Work through the component and page checklists. For each page, inspect every linked screenshot and shared contract, then read its source and child components. Redesign with Shadcn Vue while preserving every documented function, permission, validation rule, navigation path, and API/state contract. Keep implementation validation tasks open until tested. Record deliberate behavior fixes separately from visual changes.

Run `node planning/scripts/inventory.mjs` after source moves and `node planning/scripts/check.mjs --complete` to check catalog structure. These commands check coverage, links, statuses, and JPEG signatures; they cannot establish functional parity or visual quality.
