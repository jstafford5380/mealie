# UI overhaul tasks

## Catalog completion

Source contracts and visual references are reviewed for redesign. Runtime parity tests and optional branch captures remain in the page checklists; see [handoff](HANDOFF.md).

- [x] Inventory all 66 page source files.
- [x] Create a separate local application for catalog data and screenshots.
- [x] Catalog all existing Vue components and their page consumers in the static inventory.
- [x] Document shared layouts, navigation, toasts, and cross-page overlays.
- [x] Complete the authentication and onboarding page documents and state captures.
- [x] Complete recipe browsing, search, taxonomy, favorites, and cookbook documents and state captures.
- [x] Complete every recipe creation method and its progress, result, and error states.
- [x] Complete recipe details, edit modes, ingredients, steps, durations, scaling, sharing, and dialogs.
- [x] Complete shopping lists, item controls, filters, ordering, and dialogs.
- [x] Complete meal planning, date ranges, week and day modes, edit modes, and configuration.
- [x] Complete profile, account preferences, tokens, and invitation workflows.
- [x] Complete household settings, members, webhooks, and notifiers.
- [x] Complete group settings, data managers, reports, and migrations.
- [x] Complete admin settings, setup, users, groups, households, backups, maintenance, and debug tools.
- [x] Record redirect, wrapper, not-found, and server documentation surfaces.
- [x] Review every page's child component closure for undocumented actions.
- [x] Review every conditional branch for missing state captures.
- [x] Verify all Markdown screenshot links and source links.
- [x] Reconcile the final route inventory with the current source tree.

## Replacement order

- [ ] Establish Shadcn Vue, Tailwind, theme tokens, icon usage, and accessible interaction rules.
- [ ] Replace shared primitives before their page consumers: buttons, fields, cards, alerts, separators, badges, and loaders.
- [ ] Replace forms, validation, comboboxes, selects, file inputs, and date controls.
- [ ] Replace dialogs, confirmation flows, menus, popovers, tooltips, tabs, accordions, drawers, and toasts.
- [ ] Replace data tables, pagination, filtering, bulk actions, and responsive list views.
- [ ] Replace the application shell and permission-aware navigation.
- [ ] Replace each page against its own function and state checklist.
- [ ] Preserve specialized functionality: drag and drop, image crop, Markdown, JSON, wake lock, durations, and print styles.
- [ ] Verify recipe and shopping-list workflows across page boundaries.
- [ ] Verify public, authenticated, advanced, organizer, manager, household-manager, and admin views.
- [ ] Verify PWA share targets, remembered sessions, OIDC, reverse-proxy authentication, and safe redirects.
- [ ] Verify dark mode, localization, right-to-left layout, keyboard access, touch input, and narrow screens.
- [ ] Remove remaining Vuetify components, composables, directives, styles, theme references, and the Nuxt module.
- [ ] Remove Vuetify dependencies only after the source and runtime audit passes.
- [ ] Run the repository frontend checks and the relevant end-to-end workflows.

Catalog status and migration status are separate. A documented page is not a completed UI replacement.
