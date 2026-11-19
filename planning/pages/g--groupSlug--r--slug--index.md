# Recipe detail and editors

Route: `/g/:groupSlug/r/:slug`. Source: [route](../../frontend/app/pages/g/[groupSlug]/r/[slug]/index.vue).

## Functions: route and complete page contract

- Load the recipe through useRecipe for the current group and the public explore API for another group.
- Update the browser title from the recipe name. A failed public fetch returns to that group's explorer with redirect set to the requested full path.
- Render RecipePage only after data exists. Keep route slug, query parameters, group context, and shared model updates intact.
- Preserve every function in the [shared recipe-page contract](../shared-recipe-page.md). This document is part of the route contract, not optional background.
- Preserve [recipe actions](../shared-recipe-actions.md), [ingredient/date/scale controls](../shared-meal-plan.md), and [embedded timeline behavior](g--groupSlug--recipes--timeline.md).
- Cover View, Cook with and without linked ingredients, form Edit, JSON Edit, Parse, print, image gallery, comments, and all nested overlays.
- Edit access: owner; current-group admin; or unlocked recipe when household cross-edit preferences allow it. Deny other-group edit access.
- The page supports rating/favorite, last-made events, ingredient checks and substitutions, tools on hand, unit conversion, servings, organizers, nutrition, assets, notes, and source URL.
- Form Edit supports recipe metadata/settings/owner, image operations, ingredient/step order, references, Markdown, durations, notes, nutrition, assets, and advanced extras.
- Keep save validation, rename navigation, unsaved-draft review, floating Save, partial image/event errors, parser aliases, and local checked-state persistence.
- Screenshots use synthetic recipes and local test images. Parser captures end with Cancel; no parser result overwrites the fixture.

## Screenshots

### Reader, cooking, and actions

![full recipe](../screenshots/g--groupSlug--r--slug--index/01-full-recipe.jpg)
![cook mode columns](../screenshots/g--groupSlug--r--slug--index/02-cook-mode-columns.jpg)
![mobile cook mode full](../screenshots/g--groupSlug--r--slug--index/03-mobile-cook-mode-full.jpg)
![full action menu](../screenshots/g--groupSlug--r--slug--index/04-full-action-menu.jpg)
![print preferences](../screenshots/g--groupSlug--r--slug--index/05-print-preferences.jpg)
![i made this dialog](../screenshots/g--groupSlug--r--slug--index/06-i-made-this-dialog.jpg)

### Form, settings, image, JSON, and draft review

![full form editor](../screenshots/g--groupSlug--r--slug--index/07-full-form-editor.jpg)
![recipe settings](../screenshots/g--groupSlug--r--slug--index/08-recipe-settings.jpg)
![form with nutrition assets](../screenshots/g--groupSlug--r--slug--index/09-form-with-nutrition-assets.jpg)
![image menu](../screenshots/g--groupSlug--r--slug--index/10-image-menu.jpg)
![full recipe with image](../screenshots/g--groupSlug--r--slug--index/11-full-recipe-with-image.jpg)
![image lightbox](../screenshots/g--groupSlug--r--slug--index/12-image-lightbox.jpg)
![json editor](../screenshots/g--groupSlug--r--slug--index/13-json-editor.jpg)
![discard unsaved review](../screenshots/g--groupSlug--r--slug--index/14-discard-unsaved-review.jpg)

### Comments, mobile, substitutions, and linked content

![full recipe with comment](../screenshots/g--groupSlug--r--slug--index/15-full-recipe-with-comment.jpg)
![mobile full recipe](../screenshots/g--groupSlug--r--slug--index/16-mobile-full-recipe.jpg)
![rich recipe full page](../screenshots/g--groupSlug--r--slug--index/17-rich-recipe-full-page.jpg)
![ingredient substitutions](../screenshots/g--groupSlug--r--slug--index/18-ingredient-substitutions.jpg)
![step linked notes](../screenshots/g--groupSlug--r--slug--index/19-step-linked-notes.jpg)
![cook linked content](../screenshots/g--groupSlug--r--slug--index/20-cook-linked-content.jpg)

### Step and asset controls

![step edit menu](../screenshots/g--groupSlug--r--slug--index/21-step-edit-menu.jpg)
![step reference linker](../screenshots/g--groupSlug--r--slug--index/22-step-reference-linker.jpg)
![bulk add utilities](../screenshots/g--groupSlug--r--slug--index/23-bulk-add-utilities.jpg)
![new asset dialog](../screenshots/g--groupSlug--r--slug--index/24-new-asset-dialog.jpg)
![asset actions](../screenshots/g--groupSlug--r--slug--index/25-asset-actions.jpg)
![gallery asset](../screenshots/g--groupSlug--r--slug--index/26-gallery-asset.jpg)

### Parser stages

![parser summary](../screenshots/g--groupSlug--r--slug--index/27-parser-summary.jpg)
![parser missing food](../screenshots/g--groupSlug--r--slug--index/28-parser-missing-food.jpg)
![parser choice sheet](../screenshots/g--groupSlug--r--slug--index/29-parser-choice-sheet.jpg)
![parser final review](../screenshots/g--groupSlug--r--slug--index/30-parser-final-review.jpg)

### Sharing, timeline, and rich form

![share links](../screenshots/g--groupSlug--r--slug--index/31-share-links.jpg)
![share qr](../screenshots/g--groupSlug--r--slug--index/32-share-qr.jpg)
![recipe timeline](../screenshots/g--groupSlug--r--slug--index/33-recipe-timeline.jpg)
![rich full form](../screenshots/g--groupSlug--r--slug--index/34-rich-full-form.jpg)
![ingredient menu](../screenshots/g--groupSlug--r--slug--index/35-ingredient-menu.jpg)

## Migration validation and optional evidence

These additional cases remain for replacement validation. See the [handoff evidence decisions](../HANDOFF.md#evidence-decisions) for shared references, preview fixtures, and unexecuted branches.

- [ ] Verify public permissions, lock/cross-household edits, conversion, nested-recipe scale, parser creation/aliases, and save errors during replacement.
- [ ] Verify merge undo, image drop/upload failures, print pagination, keyboard gallery navigation, and touch/RTL interactions during replacement.

## Shadcn Vue replacement checklist

- [ ] Replace layout and action toolbar with semantic structure, Buttons, DropdownMenu, Dialog/Sheet, and accessible icon labels.
- [ ] Preserve form/JSON modes, unsaved-draft protection, ingredient/step editors, references, Markdown, durations, and parser flow.
- [ ] Preserve scaling/conversion, recipe permissions, ratings/favorites, timeline/comments, asset/lightbox interactions, and print preferences.
- [ ] Keep specialized sortable, crop, Markdown, JSON, file, wake-lock, and print capabilities through explicit integrations.
