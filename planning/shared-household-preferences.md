# Household preference editor

Source: [HouseholdPreferencesEditor.vue](../frontend/app/components/Domain/Household/HouseholdPreferencesEditor.vue).

## Functions to preserve

- Private Household overrides individual public-recipe options; keep its explanation and privacy documentation link.
- Lock Recipe Edits from Other Households restricts editing household-owned recipes; retain its explanatory text and administrator exception tooltip.
- Show Announcements is a household preference with explanation of user opt-out.
- First Day of the Week offers localized Sunday through Saturday, persisting integers 0 through 6. This affects meal-plan week boundaries.
- Household Recipe Preferences are defaults for newly created recipes, individually overridable in the recipe settings menu. Preserve all five booleans and explanations: public visibility, nutrition, assets, landscape view, and disabled comments.
- Nutrition/assets descriptions explain that unavailable data is not displayed. Comment preference hides and disables recipe comments.
- Copy the supplied model into reactive local state, propagate changes to the parent, and sync refreshed parent data back.
- The editor has no save button/API of its own; the enclosing page owns persistence.

## Shadcn Vue replacement checklist

- [ ] Preserve eight checkboxes, seven day options, all descriptions/documentation, and administrator tooltip.
- [ ] Use Checkbox, Select, Tooltip, semantic group headings, and responsive layout.
- [ ] Verify persistence through each enclosing page and changed meal-plan week start after revisiting the planner.
