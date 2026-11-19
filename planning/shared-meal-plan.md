# Shared meal-plan behavior

Read this contract with all four meal-plan page documents.
Sources: [meal-plan composable](../frontend/app/composables/use-group-mealplan.ts), [entry form](../frontend/app/components/Domain/Household/GroupMealPlanEntryDialog.vue), [planner board](../frontend/app/components/Domain/Mealplan/MealPlanBoard.vue) (replacing the day and layout components), [meal card](../frontend/app/components/Domain/Mealplan/MealPlanEntryCard.vue), [rule matching](../frontend/app/composables/use-mealplan-rules.ts).

## Dates, layout, and API actions

- Keep day entries and week entries distinct. A week entry has both date and endDate. A day entry has a null endDate.
- Derive weeks from household firstDayOfWeek. Parse API calendar dates as local dates, without UTC shifts.
- Fetch all entries in the visible range with include_week_entries=true. Refresh on range change and successful create, update, delete, or type change.
- Render each week across the full row, then its days. Group meals in Breakfast, Lunch, Dinner, Side, Snack, Drink, Dessert order.
- Omit empty meal-type sections. Highlight today and the week containing today. Retain older week boundaries after a household week-start change.
- Day columns span one, two, or three columns by breakpoint. Week recipe cards use a responsive grid with 340px minimum cells.
- Convert recipe entries to recipe summaries with their stored scale. Skip note entries when assembling shopping-list ingredients.

## Entry create and update

- Open a fresh draft with date, whole-week switch, meal type, Recipe/Note mode, selected recipe, scale, title, and text.
- Reset search filters and Ignore Planner Rules each time. Preserve an existing entry's dates, type, content, recipe, and scale.
- Recipe mode requires a selection. Note mode requires a trimmed nonempty title and permits multiline text. Enter does not submit.
- Show whole-week mode when user preferences select Weeks or the existing entry already spans a week.
- Whole-week mode highlights the full household week. Selecting a day chooses that day's week. Day mode selects only one date.
- The calendar shows existing plan markers, month navigation, neighboring dates, localized labels, and household week start.
- Recipe search has clearable text, category/tag multiselects, selected chip removal, active result, loading indicator, and empty results.
- Fetch the first 40 recipes, then 20 per page within the results scroll container. Sort by name ascending.
- Debounce selector filters by 300ms. Discard superseded responses. Reset selector filters when the entry dialog opens.
- Combine all applicable rule filters with AND and parentheses. Day entries match weekday or Any rules and matching type or Any rules.
- Week entries match only Any-day rules. Do not combine unrelated weekday rules for week entries.
- Ignore Planner Rules bypasses the combined filter. Disable it when no rule applies. Offer it in the rule-filtered empty state.
- Recipe changes reset scale to one. Use servings, yield quantity, or one as the recipe's base quantity.
- Recipe submit clears note title/text. Note submit clears recipeId and sets scale one. Update preserves ID, groupId, and userId.
- Emit create/update payloads through parent actions. Preserve failure recovery and feedback from the API and BaseDialog.

## Serving scale

- Show localized scaled servings. Open a numeric servings popover, increment/decrement servings, and reset to the base quantity.
- Disable decrement at one serving. Allow fractional quantities. Reject invalid scale calculations through the shared calculation helper.
- Display 1.5x or another nondefault multiplier in edit cards. Recipe links carry the scale query parameter.
- View-card scale edits debounce saves for 400ms. Preserve pending edits during refresh and flush them on scope disposal.
- Preserve scale when moving entries, changing type, and assembling shopping-list ingredients.

## Day and week actions

- View headers open a menu: Add Day/Week to List, New, Random Dinner, Random Side, and Random Meal submenu.
- Random Meal includes Breakfast, Lunch, Side, Snack, Drink, and Dessert. Dinner has its own direct action.
- Disable list actions with no recipes. Preserve the [ingredient selection workflow](shared-recipe-actions.md) and entry scales.
- New opens the shared entry form with the header date and optional week end date.
- Random meal sends date, optional endDate, and type, then refreshes on success. Server rules restrict its pool.
- Edit mode places New and random actions inline. Keep keyboard alternatives for all drag and nested-menu actions.

## Calendar feed

Source: [calendar dialog](../frontend/app/components/Domain/Household/GroupMealPlanCalendarDialog.vue).

- Refresh household feed token each time the dialog opens. Show loading, off state, or enabled controls.
- Only household managers see Turn On, Reset, and Turn Off. Explain that anyone with the URL can view the household plan.
- Enabled controls include multiselect meal types, removable type chips, Include Notes, and one time input per selected type.
- Show duration only when any selected type has a time. Accept 1–1440 minutes; default is 60.
- Include browser timezone for timed entries. Omit empty times and default duration from URL parameters.
- Provide customizable event title and multiline description templates, help text, change warning, and documentation link.
- Blank templates use defaults. Include nondefault nonblank templates in URL parameters.
- Build a read-only feed URL with locale, selected types, notes option, times, timezone, duration, and templates. Include Copy.
- Empty or complete type selection omits type parameters. Notes defaults true. Preserve these URL semantics.
- Turn On/Reset creates a token. Turn Off deletes it. Update the displayed token after success.
- The catalog captures the off state. It does not create or expose a feed credential.
