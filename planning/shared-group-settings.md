# Group preferences, AI connections, and prompts

Sources: [GroupPreferencesEditor](../frontend/app/components/Domain/Group/GroupPreferencesEditor.vue), [GroupAIProviderSettingsEditor](../frontend/app/components/Domain/Group/GroupAIProviderSettingsEditor.vue), [GroupAIProviderDialog](../frontend/app/components/Domain/Group/GroupAIProviderDialog.vue), [GroupAIPromptEditor](../frontend/app/components/Domain/Group/GroupAIPromptEditor.vue), [use-ai-providers](../frontend/app/composables/use-ai-providers.ts).

## Functions: preferences and provider selection

- Group Preferences contains Private Group (overrides individual public visibility), its documentation link, and Show Announcements with explanation of the user's additional opt-out.
- Editors copy the model into reactive local state, emit model changes, and sync fresh parent data back. Preserve synchronization after API refreshes.
- AI settings selects searchable/clearable Default, Audio, and Image providers by ID while showing names. Preserve the descriptions distinguishing general AI, transcription, and image capabilities.
- Enrich Non-AI Imports is disabled without a default provider. Existing providers without a default produce a warning tooltip beside the section header.
- Provider list shows each name and independent Edit/Delete controls; Create Provider opens an empty connection dialog. Delete emits directly without a confirmation in this component.
- Provider selection/enrichment belongs to the enclosing settings save; individual provider create/update/delete events invoke separate operations.

## Connection dialog and advanced rows

- Create fields: required Provider Name, Model, and API Key; optional Base URL; numeric timeout (minimum zero, default 300 seconds); Advanced accordion with Request Headers and Request Parameters key/value editors.
- Keys already in the map are read-only, values editable, and each entry removable. New rows add by button, Enter in either input, or focus leaving the two-field row. Trim new keys, permit empty values, replace an existing matching key, and clear the new-row draft after adding. Null maps act as empty maps.
- Keep anti-autofill behavior and password masking for API Key. Use a bounded 70vh scroll region for long advanced forms.
- Edit loads the saved provider and leaves API Key empty. An unchanged Base URL permits omitted API Key to preserve the stored secret. Changing Base URL requires a new API key; do not send an existing secret to a new endpoint.
- Stored sensitive header/parameter values arrive as `********`. This sentinel means retain the stored value only while Base URL is unchanged. A changed URL with hidden sentinel values opens Advanced automatically, warns to reenter them, and disables submit/test until corrected.
- Disable submit when trimmed name/model is blank, required key is blank, or hidden values need reentry; guard the handler too. Base URL empty is sent as null. Empty header/parameter maps are omitted; nonempty maps are sent.
- Create/update emit to the caller; no automatic close occurs in the submit handler. Close resets draft, advanced state, saved URL, test result, and form state.
- A request token prevents a delayed provider fetch from overwriting a later dialog/provider state. Preserve this concurrency protection.
- Test Connection evaluates current form values. In edit mode use the saved-provider test endpoint with overrides and omit an empty key. Loading disables duplicate test; finally clears testing.
- Result reports connection success or returned/fallback failure. Successful tests additionally distinguish image-capable versus text-only providers when capability is boolean; null means no image capability statement, not failure.
- The shared dialog's get/test composable uses current-group user endpoints even inside an admin group-detail parent. Cross-group edit/test behavior requires verification; admin parent mutations themselves use explicit target-group admin endpoints.

## Prompt editor

- Load prompts with the optional explicit admin group ID; without one use current-group endpoints. If an admin target ID is absent, do not fall back to the administrator's own group.
- Global Instructions apply to recipe-data tasks, not system prompts. Save is disabled when trimmed draft equals the server value. Nonempty trimmed text saves the `global` prompt in append mode; empty text resets it.
- List prompts in an accordion: Build Recipe, Add Step Details, Parse Ingredients, Recipe from Video, Assign Organizers, Translate Recipe, Read Source Material, and Transcribe Audio in the current fixture. Resolve localized title/description from the name, falling back to the raw name and empty description for unknown tasks.
- Display System, Appended, or Overridden badges and a warning icon if the built-in default changed.
- Expanded tasks explain their purpose; system tasks show a warning that global instructions do not apply. A changed built-in default displays its own warning.
- Mandatory modes: Default, Append, Override. Append has its own text draft and explanation. Override starts from the built-in default when its draft is blank, has an information warning, and uses a larger editable textarea.
- View/Hide Default Prompt toggles a read-only, auto-growing built-in prompt preview independent of draft mode.
- Keep append/override drafts independently when switching modes. Default is dirty only when a saved customization exists; customized mode is dirty only for nonblank content different in mode or text from the server.
- Save Default resets that task; save Append/Override sends exact content and selected mode. Show success/error feedback and refresh only the saved task's draft, preserving unsaved changes in other tasks and the default-preview visibility.
- Global and per-task saves are independent of the enclosing group Update button. Preserve loading state and failure recovery.

## Shadcn Vue replacement checklist

- [ ] Compose Checkbox, Combobox, Dialog/Sheet, Input, Number input, Accordion, key/value rows, Alert, Badge, ToggleGroup, Textarea, Tooltip, and feedback.
- [ ] Preserve three separate persistence boundaries: enclosing preferences, provider CRUD, prompt saves.
- [ ] Preserve URL-bound secret handling, redacted sentinels, stale-request guards, admin target scope, and unsaved task drafts.
- [ ] Verify create/edit/test, image/audio capability messaging, empty-map semantics, and keyboard/focus behavior for nested controls.
