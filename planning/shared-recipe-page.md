# Shared recipe page

This contract covers RecipePage and both ordinary/shared recipe routes. The page documents identify remaining evidence checks.

## Redesign: reader and Cook mode (implemented)

The reader (View) and Cook mode are rebuilt on the new design. RecipePage.vue still owns modes, drafts, saving, scaling and conversion. The editor (Edit, JSON, Parse) keeps its current components inside the page and is redesigned in its own pass. Changes users will notice:

| Before | Now |
| --- | --- |
| Header card with a separate action bar (favourite, timeline, edit, ⋮) above the image; title, description and time cards beneath. | One header: recipe name in the serif, description, a facts row (total, prep, cook, yield), rating, owner, source site, Last made. The photo sits beside the text on desktop and above it on phones or with the landscape setting. Tap the photo for the lightbox. |
| "Cook Mode" button tucked into the Instructions heading. | **Cook Mode** is the main button in the header, next to favourite, timeline, edit and the ⋮ menu. |
| "Original URL" button at the bottom of the page. | The source site shows by name in the header (for example "example.com ↗"). Edit still has the Original URL field. |
| Servings shown as a chip opening a menu with a number field and ± buttons. | Servings is a − / "Serves N" / + stepper. Tap the label to type an exact number or reset. Recipes that can't scale show a plain "Serves N" label. The meal planner's scale control uses the same component. |
| Unit system as a toggle button. | Unit system is a dropdown ("As written", Metric, US) with the current choice marked. |
| Ingredient list items with a checkbox; substitutions on hover. | Checkbox rows: tap anywhere on the row; checked rows dim and are struck through. Section titles become small headings. Substitutions open in a popover on tap (works on phones). |
| Required tools in a list with checkboxes. | Same, as checkbox rows; checking marks the tool on hand as before. |
| Instruction cards; tapping the card header collapsed it with a check icon; section headers were coloured bars. | A numbered method. Tap a step (or its number) to mark it done; done steps fold to one line with a check. Tap a section heading to fold the whole section. Durations are chips; linked notes open in a bottom sheet. |
| Done steps reset whenever the page reloaded or the instructions changed. | Done steps are kept for the browser tab (like checked ingredients), shared with Cook mode, and cleared when you finish cooking. |
| Categories and tags in cards; nutrition in a card list; assets in a card list. | Categories and tags as chips under small headings; nutrition as a compact table; assets as a simple list (images open the lightbox, other files open in a new tab). On desktop these sit under the ingredients; on smaller screens after the method. |
| Notes in plain card text. | Notes as highlighted callouts. |
| Comments in outlined cards with a Vuetify textarea. | A comment thread: avatar, name, date, text; Delete beside your own (or any, for admins). The Submit button appears once you type; Ctrl/⌘+Enter also submits. |
| Cook mode: two scrolling columns, or every step with its linked ingredients inline when links exist. Floating × in the corner. | Cook mode is a full-screen, one-step-at-a-time view: large step text, a progress bar (tap a segment to jump), Previous / Next (arrow keys too) and **Finish** on the last step. A side panel (below the step on phones) shows the step's linked ingredients, or all ingredients and tools; a "This step / All ingredients" switch appears when the recipe has links, and unlinked ingredients are listed under the step's. Linked notes appear as callouts under the step. Servings, units and Keep screen awake stay available. It reopens on the first unfinished step. |
| Floating save button: only appeared if the page loaded in edit mode. | Appears whenever the editor toolbar scrolls out of view, however edit mode was opened. |

## Redesign: editor frame (implemented)

Edit mode opens in the same page frame as the reader. The ingredient, method, organizer and asset editors still use their earlier controls inside the new sections; they are redesigned next. Changes users will notice:

| Before | Now |
| --- | --- |
| Edit kept the reader's header card on top, with Delete / JSON / Close / Save buttons floating over it and a floating Save button after scrolling. | A sticky editor bar: Cancel (×), the recipe name, a Form / JSON switch, a ⋮ menu (Parse ingredients, Delete recipe) and Save. Save is always in reach, so the floating Save button is gone. On phones the Form / JSON switch moves into the ⋮ menu. |
| One long column of fields, cards and buttons. | Titled sections — Basics, Ingredients, Instructions, Organize, Note, Nutrition, Assets, Source, Recipe Settings — with a jump list beside them on desktop. Nutrition and Assets appear only when turned on in the recipe settings. |
| "Image" button opening a menu (upload, URL, delete). | The photo sits in Basics: tap it to upload or replace, "Use an image URL" to fetch one, Remove (with confirmation) to delete it. |
| "Settings" button opening a menu of switches. | Recipe Settings is a section with labelled switches; the public-visibility note shows under its switch instead of in a tooltip. |
| Original URL and API extras at the very bottom. | A Source section: Original URL, plus API extras for advanced users. |
| Name could be left empty and only failed on the server. Only the step fields were checked before saving. | Save checks every field (including the required name) and shows the error in place. |
| Time inputs: hour and minute spinners plus an unlabelled text field. | Hour and minute boxes with units, and a "Note" box (for example "plus overnight"). |
| Notes and nutrition editors in Vuetify cards. | Note cards with Title, Note and a remove button, plus "Add note". Nutrition as a grid of number boxes with units. |

### Ingredient editor (implemented)

| Before | Now |
| --- | --- |
| Rows of filled Vuetify fields with an up/down drag icon, a trash icon and a ⋮ group. | Compact rows: a grip handle, Quantity, Unit, Food (or Recipe) and Notes boxes, then ⋮ and Delete. On phones the row wraps (Quantity + Unit, then Food, then Notes) and Delete moves into the ⋮ menu. |
| Unit and food autocompletes; creating meant typing a name and pressing Enter (or a small Create button in the list). | Searchable pickers that list matches as you type, with a "Create “…”" option whenever nothing matches exactly. Enter picks the highlighted option, so Enter on a name with no match still creates it. A clear (×) button appears on hover or focus. |
| Parser warnings as a coloured icon with a tooltip. | A marigold outline and warning icon on the unit or food the parser couldn't match (the message is read out to screen readers). |
| "Toggle Recipe" in the row menu. | The row menu says what it will do: "Use a recipe instead" / "Use a food instead". |
| Section title as an underlined text field above the row. | A heading-style input above the row; still added and cleared from the row menu. |
| A split "Add ▾" button (Add Food / Add Recipe / Bulk Add). | Three visible buttons: Bulk add, Add recipe, Add food. |
| Empty ingredient list showed a grey skeleton. | An empty list says so and points to Add food and Bulk add. |
| "Ingredients aren't parsed" as a Vuetify alert. | A tinted notice with a Parse button. |

The same row is used in the parser dialog, and the substitution editor (also shared with the food manager's substitution dialog) uses the same pickers.

### Method editor (implemented)

| Before | Now |
| --- | --- |
| Elevated instruction cards with a large summary field, up/down drag icon and a ⋮ button group; section titles as coloured bars. | Step cards: grip handle, the step number in the recipe serif, a summary box ("Step N" until named), a duration box, ⋮ and Delete. Section titles are heading-style inputs above the step that starts the section. |
| Duration as a Vuetify number field with a label. | A compact "Minutes" box with a clock icon; the note about leftover seconds still appears when relevant. |
| Linked ingredients and notes listed as plain lines under the text editor. | Linked ingredients show as chips and linked notes as marigold-edged chips under the step, with a "Link references" (or "Edit") button right there; the same action stays in the ⋮ menu. |
| Link dialog with Vuetify checkboxes. | Same groups (Not linked yet / Linked to other step, by ingredient section, then Notes) as checkbox rows, with Cancel, Auto, Save and Next step. |
| Merge above offered on the first step (doing nothing). Ctrl+Z only. | Merge above appears from the second step on; Ctrl+Z or ⌘+Z undoes the last merge. |
| "Add" and "Bulk Add" buttons below the method. | "Bulk add" and "Add step" buttons inside the method section; an empty method says so. |
| Bulk add dialog: textarea plus a list of utilities with play buttons. | Textarea, a "Clean up" row of labelled buttons (Trim whitespace, Remove first character, Split numbered lines; descriptions on hover), and a live line count. |
| Image drop target: grey overlay with white text. | A dashed primary outline with "Drop image" while dragging; the upload shows a thin progress bar. |

### Organizers and assets (implemented)

| Before | Now |
| --- | --- |
| Categories, tags and tools as Vuetify multi-autocompletes with a floating label, label-style chips and a "+" append icon. | Chip pickers: selected items as removable chips, a search box inside the field, a list with checkmarks, and "Create “…”" when nothing matches exactly. Backspace in an empty search box removes the last chip. The "+" button beside the field still opens the create dialog (with On Hand for tools). Used the same way in the query filter builder, the recipe data page and bulk import. |
| Assets editor: a card with its own title, a list with a ⋮ menu (View, Download, Copy, Delete) and a "+" icon in the header. | A plain list inside the Assets section with the same ⋮ actions, an empty state, and a "New Asset" button. The reader's asset list has a Download button on each row again. |
| New asset dialog: name, an icon select, and an icon-only upload button. | "Choose file" with the chosen file name shown, then Name (defaults to the file name) and Icon. Create stays disabled until a file is chosen. |

### Parser and JSON mode (implemented)

| Before | Now |
| --- | --- |
| Parser screens built from Vuetify cards, chips, alerts and checkboxes. | Same three steps in the app's style: an intro with a result summary (auto-parsed / to review pills), one ingredient at a time (original text in the recipe serif, confidence score, the ingredient row, "Delete item" and the create-missing / add-as-alias buttons), then the full review list. Choosing a parser closes the picker and re-runs the parse. |
| JSON mode: the stock editor theme at a fixed 1500px height. | The editor uses the app's colours and fonts (including dark mode) and fills the window under the editor bar. |

## Page mode, draft, and save

Source: [RecipePage](../frontend/app/components/Domain/Recipe/RecipePage/RecipePage.vue).

- Keep View, form Edit, JSON Edit, Parse, and Cook modes distinct. Child form editors mutate the same recipe model.
- Hydrate edit=true and parse=true only for the current group. Hydrate a positive finite scale query and cook-mode query.
- Clear edit/parse parameters when those modes close. Preserve rename navigation without a conflicting query cleanup.
- Take a deep snapshot of the loaded/saved recipe. Compare the full model for unsaved changes.
- Close or route exit with unsaved edits opens Discard Changes. Cancel stays in the editor; Confirm restores the snapshot and completes the pending route or returns to View.
- Validate the instruction form before form-mode Save. JSON mode skips this form validation.
- Update by route slug. Keep edit mode on error. On data success, replace recipe/snapshot and navigate to its new slug when renamed.
- Parsed ingredients replace the ingredient array and save. Close Parse and restore form Edit when parsing started there.
- Delete navigates to the group explorer only after the API returns a slug.
- Track header intersection and show a floating Save button when an edit toolbar leaves view. Disconnect the observer on unmount.
- Clear shared page state and browser navigation warning on unmount.
- Display unit conversion only outside Edit. Keep the original model by identity inside editors so converted copies never enter saved data.
- Hide comments when household or recipe preferences disable them. Show comments outside form Edit and Cook; current JSON mode still shows comments.
- Default to landscape header layout on small screens or when recipe settings request it.

## Header, actions, image, and settings

Sources: [reader header](../frontend/app/components/Domain/Recipe/RecipePage/RecipePageParts/RecipeReaderHeader.vue), [editor bar](../frontend/app/components/Domain/Recipe/RecipePage/RecipePageParts/RecipeEditorBar.vue), [editor basics](../frontend/app/components/Domain/Recipe/RecipePage/RecipePageParts/RecipeEditorBasics.vue) (replacing the earlier header, info card and action menu).

- Display name, user/group rating, current-group owner avatar/name, sanitized Markdown description, scaled yield, Last Made, and available prep/cook/total times.
- Show recipe image above the header in landscape or beside it otherwise. Use small image URLs on small screens and full URLs on desktop.
- Hide failed image content, reset failure on URL changes, and open hero plus image-assets lightbox on click. Hero height is 200px at xs and 400px otherwise.
- Use recipe permissions, household context, and page user for Edit access. Keep favorite and timeline buttons in the current group.
- Preserve [shared context actions](shared-recipe-actions.md). The full page enables Print and Print Preferences, plus authenticated ZIP/PDF, duplicate, meal plan, shopping list, share, delete, and custom actions.
- Editor toolbar offers Delete review, JSON/form toggle, Close, and Save. Small screens show icon-only variants with accessible names.
- Info editor fields: required name, nonnegative fractional servings/yield quantity, yield text, total/prep/cook times, and multiline description.
- Time controls preserve textual or seconds forms and imported remainder seconds according to the shared time-input contract.
- Image menu offers file upload, Delete with confirmation, and URL fetch with loading and error handling. Disable Get without a saved slug and show the save-first message.
- Image upload/delete/URL operations act on the backend immediately; they do not wait for recipe Save. Update image model and refresh key after success.
- Settings switches: Public Recipe with visibility help, Show Nutrition, Show Assets, Landscape View, Disable Comments, and Locked. Only the owner can change Locked.
- Owner selector shows group users with household subtitles. Enable owner changes only for recipe owner or admin.

## Rating and ingredient reader

Sources: [rating](../frontend/app/components/Domain/Recipe/RecipeRating.vue), [ingredients](../frontend/app/components/Domain/Recipe/RecipeIngredients.vue), [ingredient row](../frontend/app/components/Domain/Recipe/RecipeIngredientListItem.vue), [unit selector](../frontend/app/components/Domain/Recipe/RecipeUnitSystemButton.vue).

- User ratings use whole stars and clear when the current star repeats. Keep local updates during pending writes; do not overwrite them with a stale refetch.
- Public/read-only rating falls back to a nonzero group average with half-stars and muted styling. Hover feedback requires a fine pointer with hover support.
- Display scaled quantity, unit, food or referenced-recipe link, and sanitized Markdown note. Free-text ingredients render their note as the primary text.
- Ingredient sections have headings and dividers. Copy Ingredients includes section headings in brackets and scaled plain-text rows.
- Click row or checkbox to toggle checked state without double toggles. Store by referenceId, with index fallback, in recipe-specific session storage.
- Share ingredient checked state between normal and Cook views. Use transient state only when no storage key exists.
- Substitutions open on click/tap. Show recipe-specific substitutions first and common food substitutions second with reduced emphasis.
- Substitute names follow the ingredient's scaled plurality. Food substitutions can include Markdown notes; note-only substitutions remain primary content.
- Required Tools shows on-hand checkboxes. Update the current household's tool association only for a current-group signed-in user.
- Servings controls appear outside Edit. Enable scale edits only when at least one ingredient has a food or unit; use servings/yield/one fallback.
- Unit menu offers As Written, Metric, and Imperial (stored as us). Disable conversion when no ingredient has convertible standardization data.
- Apply display conversion consistently to ingredient list, Cook, and Print. Keep conversion separate from saved data.

## Ingredient editor

Sources: [parent editor](../frontend/app/components/Domain/Recipe/RecipePage/RecipePageParts/RecipePageIngredientEditor.vue), [row editor](../frontend/app/components/Domain/Recipe/RecipeIngredientEditor.vue), [substitution editor](../frontend/app/components/Domain/Recipe/RecipeIngredientSubstitutionEditor.vue).

- Offer Parse when ingredients exist but none has a food/unit. Show an empty skeleton when no ingredient exists.
- Drag ingredients by handle with a 250ms touch delay. Preserve stable reference IDs and order.
- Add creates a UUID row with empty note/title, zero quantity, and autofocus quantity. Select initial zero on first autofocus only.
- Split menu offers Add Food, Add Recipe, and Bulk Add. Bulk creates a note-only row per supplied line.
- Add Recipe starts quantity one and a recipe-specific row type. Toggle Recipe clears food/unit when entering recipe mode and clears referencedRecipe when leaving.
- Row fields: nonnegative fractional quantity, searchable/clearable unit, searchable/clearable food or recipe, note, optional section title, and substitutions.
- Prevent minus, plus, and exponent keys in quantity. Preserve autocomplete errors/tooltips from parser review and attached overlay targets.
- Unit and food selectors use shared search, auto-select-first, and explicit Create/Enter creation when no matching named object exists.
- Recipe search runs on focus/click and typed query. Preserve current-group/public API selection.
- Row menu offers Add/Clear Section, Toggle Recipe, Add/Clear Substitutions, Insert Above, and Insert Below. A separate delete action removes the row.
- Existing title/substitution data remains visible without a toggle. Clear actions remove its data, not only its display.
- Substitutions support an existing-food selector, optional note-only alternative, Add, and Delete. Clearing the last row keeps its editor open.
- Do not create new foods from the substitution selector. Keep accessible delete targets and responsive field layout.

## Organizers, nutrition, notes, and footer

- Categories/tags show linked chips in View and creatable organizer multiselects in Edit. Tools use their selector in Edit.
- Place organizers beside instructions on desktop and below them on smaller screens. Preserve [organizer management](shared-organizer-browser.md) contracts.
- Show Nutrition only when enabled and at least one value exists, or in Edit. Fields cover calories, carbohydrate, cholesterol, fat, fiber, protein, saturated fat, sodium, sugar, trans-fat, and unsaturated fat.
- Nutrition is per serving. Use nonnegative fractional inputs, proper unit suffixes, string/null persistence, and hide empty rows in View.
- Notes have title and Markdown text. Add creates a stable note referenceId; Delete removes that note. Preserve notes for instruction linking.
- Original URL opens only a valid HTTP URL in View; Edit has its text input. Hide the link in Cook mode.
- Advanced-only API Extras supports key/value fields, duplicate-key prevention, add-key reset, and key deletion.
- Keep Screen Awake follows supported-device preference and releases the wake lock on unmount.

## Comments

- Show signed-in avatar and multiline comment form. Disable Submit for whitespace-only input. Submit trims text and appends successful data.
- Clear the comment input after a request. Preserve error feedback so failed text does not disappear silently during replacement.
- Render author avatar/name, localized timestamp, and sanitized Markdown for each comment.
- Show Delete only for the author or admin. Remove locally only after HTTP 200. Current source deletes directly without review.

## Cook mode

- Without linked ingredients, show ingredient/tools and instructions in separate desktop scroll columns; stack on small screens.
- With linked ingredients, show each step's linked ingredients and notes alongside its instructions. Show unlinked ingredients below the steps.
- Keep scale/unit controls, ingredient state, required tools, and a fixed Close control. Preserve cook query synchronization.


## Instruction edit, references, and display

Source: [instructions](../frontend/app/components/Domain/Recipe/RecipePage/RecipePageParts/RecipeMethodEditor.vue).

- View steps show Markdown summary or step number, duration, Markdown instructions, optional linked-note button, and completed/collapsed state.
- Click a step to collapse/mark it complete; repeat to expand. Click a section header to collapse/expand its complete range until the next section.
- Edit supports summary, section title, Markdown content and preview, duration, drag order, and Delete.
- Menu actions: Add/Clear Section, Link References, Upload Image, Preview/Edit Markdown, Merge Above, Move to Top/Bottom, Insert Above/Below.
- Newly opened section title takes focus once. Clearing its text must not close its field while typing. Clear Section removes the title.
- New and bulk steps receive UUIDs, empty titles/summaries/reference arrays, and null duration. Bulk utilities trim lines, remove first character, and split numbered prefixes.
- Preserve merge history and Ctrl+Z undo for the last merge. Keep step content, titles, and references according to the merge helper.
- Link References opens the active step text and ingredients grouped by section, split into Unlinked and Linked to Other Step.
- Select ingredients and notes by stable referenceId. Show no-notes guidance. Auto matches ingredients from step text.
- Save applies both ingredient and note references. Next Step saves and opens the next step. Cancel leaves references unchanged.
- Editor shows selected ingredient text and note titles below Markdown. Public/cook display resolves references without enabling edit links.
- View linked notes opens a bottom sheet with title, count, Markdown notes, and Close. Cook mode displays them beside the step directly.
- Duration uses nonnegative whole minutes up to 35,791,394. Retain imported seconds until the minute value changes and show their exact duration hint.
- Zero duration stores null. Display localized hours/minutes/seconds next to the step summary.
- Drop a local image, upload from the step menu, or drop an HTTP image URL to create a recipe asset and embed its image HTML.
- Show upload progress per step. Report unsupported image URLs and URL-fetch failure. Keep the asset list and Markdown embed together.
- Preserve touch drag delay, stable step IDs, responsive linked-content columns, and nested-click prevention.

## Assets and lightbox

Sources: [assets](../frontend/app/components/Domain/Recipe/RecipeAssets.vue), [lightbox](../frontend/app/components/Domain/Recipe/RecipeImageLightbox.vue).

- Assets appear when enabled and nonempty, or while editing. Images show lazy thumbnails; other files show the selected icon.
- View image rows open a gallery. Other file rows open their URL in a new tab. Each view row has Download.
- Edit asset menu offers View, Download, Copy image embed HTML, and Delete from the model.
- Add Asset dialog contains Name, File/PDF/Image/Code/Recipe icon selector, and Upload. Require a selected file and report invalid submission.
- Default name from file base name. Use a trimmed custom name or full filename fallback; send extension, name, icon, and file.
- Successful creation appends the server asset; reset file/name/icon afterward. Asset upload occurs before recipe Save.
- Gallery order is hero then image assets in model order. Recognize png, jpg/jpeg, gif, webp, bmp, and avif; exclude other files.
- Open the clicked asset's index. Show previous/next only within bounds, plus label and index/total when multiple images exist.
- Arrow keys navigate without scrolling the underlying page. Ignore modified keys and text-input targets; remove listeners on close/unmount.
- Click image to toggle 2x zoom. Drag to pan within bounds. Suppress click zoom after drag. Hide navigation arrows while zoomed.
- Touch/pen horizontal swipe navigates at 50px. Separate it from zoom. Cancel pointer state cleanly.
- Reset zoom and natural/frame dimensions on image change. Preload adjacent images. Recalculate fit on load/resize.
- Background click or Close exits. Preserve theme-aware backdrop/caption contrast, image fit, focus, and scroll locking.

## Ingredient parser

Source: [parser state](../frontend/app/composables/recipes/use-parse-ingredients-dialog.ts).

- Opening Parse starts a fresh bulk parse with loading, optional explanation, low-confidence per-item review, then final review.
- Persist parser choice and Don't Show Again. Default NLP for English and Brute for other locales. Show the NLP language warning outside English.
- Offer AI parser only when group AI settings enable it. Retry current parser or select another parser and reparse.
- Skip referenced recipes during text parse. Restore section titles and stable ingredient reference IDs; retain referenced recipe rows.
- Review average confidence below 0.85 or missing food/unit IDs. Show original text, confidence, editable fields, and field-specific warnings.
- Missing food/unit can create a new record or add the missing text as an alias to a selected existing record.
- Keep independent food/unit loading states, permission errors, and lowercase caches to avoid repeated creations within a run.
- Delete Item marks the current ingredient for removal on Next. Otherwise Next advances through items needing review.
- Final review supports row edits, drag order, insert above/below, delete with at least one row, original text, and parser retry.
- Insert an empty UUID ingredient if final review becomes empty. Save emits ingredient rows and shows save loading.
- Reset current row, missing names, deletion flag, arrays, caches, and review state on each parse. Prevent overlapping bulk parse.
- Preserve parser error feedback and recovery instead of leaving the loading state stuck.

## I Made This and recipe timeline

- Last Made fetches the current household's value. I Made This accepts comment, local date, optional image/crop/removal, and selected child recipes.
- Reset date to today whenever the dialog opens. Use household week start. Enter does not submit.
- Create a comment event at the selected day's local 23:59:59. Derive its subject from the current user's display name.
- Update Last Made only for a newer event timestamp. For checked child recipes, create their event and update their newer Last Made independently.
- Upload event image after event creation. Distinguish total creation failure from event success with image failure; keep successful metadata.
- Reset the form, close, emit the created event, and show feedback. Preserve image crop/name state and separate partial failures.
- Timeline badge opens a recipe-scoped timeline with recipe.slug query. Preserve [timeline filtering/edit/image/delete behavior](pages/g--groupSlug--recipes--timeline.md).

## JSON and print

- JSON editor uses text mode, hides its main menu, and retains valid previous data when JSON parsing fails. Preserve line/column, editor scrolling, and form toggle.
- Print calls window.print and uses a dedicated print container with compact black-on-white output and removed app chrome.
- Print preferences include image left/right/hidden, description, notes, nutrition, child recipe expansion, linked ingredients, and substitutions.
- Render scaled servings/yield, times, Markdown description, ingredient sections in two columns, instruction sections with continuous step numbers, notes, and per-serving nutrition.
- Expand linked child ingredient arrays recursively when requested. Preserve scaling semantics and review nested recipe quantity handling.
- Print linked ingredient references with each step when selected. Render substitution text because paper has no popup.
- Keep section and ingredient cells together across print pages. Preserve safe HTML/Markdown and current image refresh keys.
- Print preparation currently assigns ingredient section titles while deriving sections. Verify print preview does not dirty the editable recipe.

## Exact helper semantics

- Merge Above concatenates source text with a space, unions ingredient/note references by ID, and removes the source step. It retains target metadata.
- Undo restores target text/reference arrays and reinserts the source at its original index. Undo merges in reverse order.
- Auto reference matching strips boundary punctuation, ignores short/common/numeric words, matches ingredient text case-insensitively, and deduplicates unused IDs.
- Organizer selectors support normalized search, removable multi-chips, clear search after selection, plus creation dialog, and Enter creation for unmatched names.
- Tool creation includes On Hand. New organizer dialog resets its name on close and appends the returned item to selected values.
- Bulk Add ignores blank lines. Its utilities trim whitespace, remove each line's first character, and split numbered prefixes; Enter remains multiline.
- Header yield combines scaled quantity and yield text. Time cards prefer formatted seconds with text fallback and wrap at mobile breakpoints.
