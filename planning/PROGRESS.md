# Catalog progress

Catalog preparation is complete for redesign. Runtime migration validation remains open.

## Delivered

- 66 route source files, each with a page document, source references, function contract, screenshots, and replacement checklist.
- Separate Nuxt error-page contract.
- All 169 Vue components inventoried with nested page consumers.
- 423 JPEG screenshots, all referenced by Markdown documents.
- Shared contracts for layouts/navigation/search/announcements, data management, administrative user forms, group and household settings, query filters, recipe cards/actions/reader/editor, meal planning, and shopping synchronization.
- A component replacement plan, page index, route/component manifests, and inventory/link/JPEG checker.
- Explicit evidence limits, preview labels, known baseline defects, and optional branch/migration tests in HANDOFF.md and individual page checklists.

## Capture environment and cleanup

- Source baseline: 884f5ff40.
- Captures used detached checkout /tmp/mealie-ui-catalog with separate Aspire data volumes and synthetic catalog records.
- Captured application ports were 60741 and 60742; synthetic HTTP fixture port was 60345. All three are no longer reachable after cleanup.
- Only the capture AppHost was stopped, with its explicit apphost path. The remaining containers were verified to mount the user's original checkout and were left running.
- The synthetic recipe share token was revoked.
- Setup, registration, API-token, invitation, and reset-link preview initializers were restored. The temporary local HTTP allow-list override was restored.
- The capture checkout has a clean Git status.
- Catalog fixture server session 51407 was stopped.
- Main-checkout changes are confined to planning/. No application source was modified for this catalog.

## Reproducible fixture references

- scripts/fixture-server.mjs serves synthetic recipe HTML and local diagnostic failures.
- fixtures/catalog-myrecipebox.csv is the successful CSV migration input.
- fixtures/catalog-lentil-soup.zip is a synthetic Mealie recipe export used for successful ZIP import.
- fixtures/catalog-records.json identifies catalog-only organizer and label records.
- Preview helpers accept only /tmp/mealie-ui-catalog and provide --apply / --restore operations. Preview screenshots are labeled and do not prove a credential or account operation completed.

## Validation

Run node planning/scripts/inventory.mjs, then node planning/scripts/check.mjs --complete.
The structural checker verifies source coverage, local links, reviewed statuses, and JPEG signatures.
It does not prove semantic completeness, image quality, or migrated runtime behavior.

See HANDOFF.md for evidence decisions and the suggested instruction for Claude.
