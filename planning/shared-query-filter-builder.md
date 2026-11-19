# Recipe query filter builder

Sources: [QueryFilterBuilder.vue](../frontend/app/components/Domain/QueryFilterBuilder.vue), [use-query-filter-builder.ts](../frontend/app/composables/use-query-filter-builder.ts), [use-recipe-filter-fields.ts](../frontend/app/composables/use-recipe-filter-fields.ts), [RecipeTimeInput.vue](../frontend/app/components/Domain/Recipe/RecipeTimeInput.vue). Shared by cookbooks, finder, and meal-plan rules; each caller may exclude fields it handles elsewhere.

## Functions to preserve

- Start with a first field when no valid initial filter exists. Add Field appends another default field; Delete cannot remove the sole row. On small displays only the last row shows a delete control; preserve removal capability with a clear accessible alternative if redesigned.
- Drag handles reorder rows with a 250ms touch delay and animation; stable row IDs keep editor state attached. Close date pickers at moved indices after drag. Provide keyboard reorder alternatives.
- Each row selects a field, type-appropriate comparison, and value. Rows after the first choose AND/OR. Show Advanced adds left/right grouping selectors with zero through three parentheses per side.
- Emit debounced string and JSON filters after 500ms when valid; emit undefined otherwise. JSON retains field name, grouping, logical/relational operator, and typed value representation.
- Validity requires field/operator/value (except boolean false and NULL operators), nonempty organizer sets, and equal counts of opening/closing parentheses. Current string builder counts parentheses but does not validate prefix ordering; do not claim full expression syntax validation.
- Disabling Advanced excludes grouping from string construction. Watchers currently watch fields, not showAdvanced itself; verify toggling Advanced updates the emitted query immediately in the replacement.
- Changing field resets values when type or choices differ, preserving row ID. Date defaults to safe current day, relative date to `$NOW-30d`, duration to 1800 seconds.
- Initialize from saved JSON parts, validating known fields and numeric/date parsing. Hydrate organizer IDs from their stores, refreshing empty stores, and omit missing records. Invalid input resets to the first field and logs the problem.
- Saved grouping automatically enables Advanced. Booleans accept true/yes/1-style first characters; numbers/durations parse numerically; selected/organizer values normalize to arrays.

## Fields and value controls

| Field | API attribute | Value control |
| --- | --- | --- |
| Categories | `recipe_category.id` | Organizer multiselect |
| Tags | `tags.id` | Organizer multiselect |
| Ingredients | `recipe_ingredient.food.id` | Food multiselect |
| Food Label | `recipe_ingredient.food.label_id` | Label multiselect |
| Tools | `tools.id` | Tool multiselect |
| Households | `household_id` | Household multiselect |
| Users | `user_id` | User multiselect, full names |
| Rating | `rating` | Numeric input, 0–5, unrestricted precision |
| Total Time | `total_time_seconds` | Hours/minutes duration inputs |
| Last Made | `last_made` | Nonnegative integer days ago, serialized `$NOW-Nd` |
| Date Created | `created_at` | Read-only localized field opening date picker |
| Date Updated | `updated_at` | Same date control |

- Organizer selectors have normalized search, multiple removable chips, and no inline create/label/icon in this context. Sync their selected objects into string ID arrays.
- Generic builder also supports string Input, boolean Checkbox, and multi-choice Select fields when callers supply those definitions.
- Date pickers use household week start and locale; selecting a date stores its ISO date slice and closes the picker. Invalid display dates fall back to today's local midnight.
- Relative-date input shows a pluralized days-ago suffix, stores absolute nonnegative day offset, and defaults invalid/unrecognized encodings to 30.
- Duration input hides the optional free-text field and stores seconds. Hours are nonnegative integers capped below the signed 32-bit database limit; minutes are nonnegative integers and can exceed 59 while typing. Preserve leftover imported seconds and do not normalize 90 minutes mid-edit. Zero total becomes null.

## Comparison choices

| Type | Operators |
| --- | --- |
| Organizer / fixed choices | IN, NOT IN, CONTAINS ALL |
| String | =, <>, LIKE, NOT LIKE, IS NULL, IS NOT NULL |
| Number | =, <>, >, >=, <, <=, IS NULL, IS NOT NULL |
| Boolean | = (operator hidden) |
| Absolute date | =, <>, >, >=, <, <= |
| Relative date | <= (older than), >= (newer than), IS NULL, IS NOT NULL |
| Duration | <=, >=, <, >, IS NULL, IS NOT NULL |

- NULL comparisons hide the value editor and serialize NULL. Switching away from NULL restores a 30-day relative-date or 30-minute duration default when appropriate.
- String/date values and organizer IDs are quoted; selected values serialize as bracketed arrays. Boolean false is valid. Current string builder treats numeric zero as empty and does not escape arbitrary string quotes; verify these edge cases before changing the query format.
- The builder only emits drafts. Saving a cookbook/rule or running a finder search belongs to the caller.

## Shadcn Vue replacement checklist

- [ ] Compose Select/Combobox, Input, Checkbox, Number input, Popover/Calendar, grouped fields, and named add/delete/reorder controls.
- [ ] Preserve all twelve recipe fields, comparison sets, JSON/string contracts, debounce, organizer hydration, and per-type defaults.
- [ ] Preserve relative dates, duration seconds/precision, grouping, AND/OR, and responsive layout; validate current zero/grouping/date edge cases.
- [ ] Capture basic/advanced, organizer, numeric, date, duration, relative-date, and mobile states in the caller-page documents.
