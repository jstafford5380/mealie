# Shopping-list state, order, and synchronization

Sources: [page coordinator](../frontend/app/composables/shopping-list-page/use-shopping-list-page.ts), [queue](../frontend/app/composables/shopping-list-page/sub-composables/use-shopping-list-item-actions.ts), [data refresh](../frontend/app/composables/shopping-list-page/sub-composables/use-shopping-list-data.ts), [CRUD](../frontend/app/composables/shopping-list-page/sub-composables/use-shopping-list-crud.ts).

## Local changes and remote synchronization

- Keep create, update, and delete queues per list in localStorage under shopping-list-queue. Validate queue shape; replace invalid storage with an empty queue.
- New edits update the UI immediately and remain queued until remote success. Assign local timestamps so checked items appear at the top immediately.
- Merge remote items with pending create/update items by ID and latest updatedAt. Exclude queued deletions from the merged view.
- An update to an unsaved new item stays in the create queue. Deleting an unsaved new item removes its create entry.
- Process delete, update, then create bulk requests sequentially because the server can merge ingredients.
- Clear only IDs in a successful request snapshot. Preserve newer queued changes and failed writes.
- Keep failed writes queued for retry. For rejected multi-item 4xx requests, retry items individually so one invalid item cannot block the others.
- Treat 401, 408, and 429 as transient for this split decision. Unexpected processing exceptions clear that operation queue in the current source.
- Track failed writes and show Changes Not Saved once per failure streak. Do not make optimistic state appear durably saved without this feedback.
- Compare server list.updatedAt against queue.lastUpdate plus five minutes. Clear an excessively stale queue according to current conflict rules.
- Refresh processes queued operations before fetching the list. Keep existing state when a fetch fails or returns nothing.
- Do not replace list state while offline or while a loading counter remains nonzero. Preserve local changes and update local order instead.
- Poll every five seconds after initial population. Pause while busy or after five minutes of inactivity. Stop the interval on unmount.
- Stop after 17,280 unsuccessful attempts; reset attempts when a list exists. Preserve reconnection and retry behavior.

## Order, labels, and item actions

- Group unchecked items by food name or free-text note, then order by position and creation time. Keep checked items separate.
- A manual drag switches to explicit position order. Rebuild the unchecked sequence across label groups and queue each changed position.
- Checked items sort by updatedAt descending, then position descending for equal timestamps.
- Unlabeled items appear first. Follow list.labelSettings order for named groups. Use label color in section headers.
- Preserve items with missing label records; verify this edge because the current grouping code can omit them.
- Reorder Labels pauses polling and exposes sortable label settings with 250ms touch delay. Assign contiguous positions and save through updateLabelSettings.
- Cancel restores list settings and resumes polling. Verify draft aliasing and loading-counter balance on Save, Cancel, and failure.
- Check All and Uncheck All change matching checked flags across the entire list after review. Delete Checked queues each checked deletion after review.
- Item creation rejects empty food/note, assigns list ID, UUID, end position, and local timestamps, then queues creation and resets the form.
- Item save replaces its local object, updates checked arrays/order, and queues the update. Item delete removes it optimistically and queues deletion.

## Search, copy, and recipe references

- Offer search only above 20 total items. Retain the toggle while the field is open even if the list shrinks.
- Search food name, plural name, aliases, note, unit name/abbreviation, and label name across checked and unchecked items.
- Preserve label/item order while hiding unmatched items. Use the shared deterministic search tiers with fuzzy threshold zero.
- Closing search clears its query. Clearing the field restores all items. Empty matches show No Results Found.
- Search expands the checked section and shows its matched count. Bind item edits to original arrays, not temporary filtered copies.
- Disable bulk check/uncheck/delete and drag while searching because they affect items outside the visible matches.
- Copy uses unchecked items grouped by label. Text uses [Label] headings; Markdown uses # Label and unchecked task lines.
- Omit the heading when the only group is No Label. Separate multiple groups with blank lines. Use each item's display string.
- Copy currently uses all unchecked items even during search. Preserve or explicitly review this behavior.
- Map linked recipes by ID. Show per-item recipe references on demand and the complete linked recipe list below items.
- Linked recipe plus/minus updates ingredient references through addRecipes/removeRecipe and refreshes on success. Guard concurrent reference requests.
- Disable linked recipe navigation/reference changes while offline. Preserve recipe quantity and ingredient attribution.
