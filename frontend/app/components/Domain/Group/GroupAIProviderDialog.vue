<template>
  <BaseDialog
    v-model="dialog"
    :title="isEdit ? $t('group.ai-provider-settings.edit-provider') : $t('group.ai-provider-settings.create-provider')"
    :icon="$globals.icons.robot"
    :loading="loading"
    can-submit
    :submit-icon="isEdit ? $globals.icons.save : $globals.icons.createAlt"
    :submit-text="isEdit ? $t('general.update') : $t('general.create')"
    :submit-disabled="submitDisabled"
    @submit="handleSubmit"
    @close="resetForm"
  >
    <div
      v-if="init"
      v-no-autofill
      class="flex max-h-[70vh] flex-col gap-1 overflow-y-auto px-6 pb-2"
    >
      <TextField
        v-model="formData.name"
        :label="$t('group.ai-provider-settings.provider-name')"
        :rules="[validators.required]"
      />
      <TextField
        v-model="formData.model"
        :label="$t('group.ai-provider-settings.model')"
        :hint="$t('group.ai-provider-settings.model-description')"
        :rules="[validators.required]"
      />
      <TextField
        v-model="formData.apiKey"
        type="password"
        autocomplete="off"
        :label="$t('group.ai-provider-settings.api-key')"
        :hint="$t(apiKeyHint)"
        :rules="apiKeyRequired ? [validators.required] : []"
      />
      <TextField
        v-model="formData.baseUrl"
        :label="$t('group.ai-provider-settings.base-url')"
        :hint="$t('group.ai-provider-settings.base-url-description')"
      />
      <NumberInputField
        v-model="formData.timeout"
        :label="$t('group.ai-provider-settings.request-timeout-seconds')"
        :min="0"
      />
      <p
        v-if="hiddenValuesNeedReentry"
        class="m-0 my-2 rounded-control border border-brand/50 bg-brand/10 px-3 py-2 text-sm"
      >
        {{ $t('group.ai-provider-settings.reenter-hidden-values') }}
      </p>
      <Collapsible
        :open="advancedPanel === 0"
        class="mt-2 rounded-card border"
        @update:open="advancedPanel = $event ? 0 : undefined"
      >
        <CollapsibleTrigger class="flex w-full items-center justify-between px-4 py-3 text-sm font-semibold">
          {{ $t('search.advanced') }}
          <ChevronDownIcon
            class="size-4 transition-transform"
            :class="advancedPanel === 0 && 'rotate-180'"
          />
        </CollapsibleTrigger>
        <CollapsibleContent class="flex flex-col gap-2 border-t px-4 py-3">
          <p class="m-0 text-sm font-semibold">
            {{ $t('group.ai-provider-settings.request-headers') }}
          </p>
          <BaseKeyValueEditor v-model="formData.requestHeaders" />
          <p class="m-0 mt-3 text-sm font-semibold">
            {{ $t('group.ai-provider-settings.request-params') }}
          </p>
          <BaseKeyValueEditor v-model="formData.requestParams" />
        </CollapsibleContent>
      </Collapsible>

      <p
        v-if="testResult"
        class="m-0 mt-3 rounded-control border px-3 py-2 text-sm"
        :class="testResult.success ? 'border-primary/40 bg-primary/10' : 'border-destructive/40 bg-destructive/10 text-destructive'"
        role="status"
      >
        {{ connectionMessage }}{{ imageSupportMessage }}
      </p>
    </div>
    <AppLoader v-else />

    <template #custom-card-action>
      <Button
        variant="ghost"
        :disabled="submitDisabled || testing"
        @click="handleTest"
      >
        <LoaderCircleIcon
          v-if="testing"
          class="size-4 animate-spin"
        />
        {{ $t('group.ai-provider-settings.test-connection') }}
      </Button>
    </template>
  </BaseDialog>
</template>

<script setup lang="ts">
import { ChevronDownIcon, LoaderCircleIcon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "~/components/ui/collapsible";
import NumberInputField from "~/components/ui/field/NumberInputField.vue";
import TextField from "~/components/ui/field/TextField.vue";
import { provideFieldGroup } from "~/composables/forms/use-field-validation";
import { useAIProviders } from "~/composables/use-ai-providers";
import { validators } from "~/composables/use-validators";
import type { AIProviderCreate, AIProviderTestResult, AIProviderUpdate } from "~/lib/api/types/group";

const props = withDefaults(defineProps<{
  providerId?: string;
}>(), {
  providerId: undefined,
});

const emit = defineEmits<{
  (e: "create", data: AIProviderCreate): void;
  (e: "update", id: string, data: AIProviderUpdate): void;
}>();

const dialog = defineModel<boolean>({ default: false });

const { $globals } = useNuxtApp();
const i18n = useI18n();
const { loading, getOne, testOne, testSavedOne } = useAIProviders();
const init = ref(false);

const form = provideFieldGroup();
const advancedPanel = ref<number | undefined>(undefined);

const isEdit = computed(() => !!props.providerId);

const defaultForm = () => ({
  name: "",
  model: "",
  apiKey: "",
  baseUrl: "",
  timeout: 300,
  requestHeaders: {} as Record<string, string>,
  requestParams: {} as Record<string, string>,
});

const formData = reactive(defaultForm());

// The API returns this in place of stored header and param values (REDACTED_VALUE in
// mealie/schema/group/ai_providers.py). Sending it back means "keep the stored value".
const REDACTED_VALUE = "********";

// Stored secrets are bound to the base URL they were saved with, so the backend only reuses
// them while the URL is unchanged. A new URL needs a new API key and every hidden value retyped.
const savedBaseUrl = ref<string | null>(null);
const baseUrlChanged = computed(() => isEdit.value && (formData.baseUrl || null) !== savedBaseUrl.value);
const apiKeyRequired = computed(() => !isEdit.value || baseUrlChanged.value);
const hiddenValuesNeedReentry = computed(() => baseUrlChanged.value && [
  ...Object.values(formData.requestHeaders),
  ...Object.values(formData.requestParams),
].includes(REDACTED_VALUE));

const apiKeyHint = computed(() => {
  if (!isEdit.value) return "group.ai-provider-settings.api-key-description-create";
  if (baseUrlChanged.value) return "group.ai-provider-settings.api-key-description-base-url-changed";
  return "group.ai-provider-settings.api-key-description-edit";
});

watch(hiddenValuesNeedReentry, (needsReentry) => {
  if (needsReentry) advancedPanel.value = 0;
});

const testing = ref(false);
const testResult = ref<AIProviderTestResult | null>(null);

const submitDisabled = computed(() => {
  return !formData.name?.trim()
    || !formData.model?.trim()
    || (apiKeyRequired.value && !formData.apiKey?.trim())
    || hiddenValuesNeedReentry.value;
});

const connectionMessage = computed(() => {
  const result = testResult.value;
  if (!result) return "";
  if (result.success) return i18n.t("group.ai-provider-settings.test-connection-succeeded");
  return result.message || i18n.t("group.ai-provider-settings.test-connection-failed");
});

// Capability info rather than a second pass/fail check - a text-only provider is a valid setup,
// it just can't be used as the image provider. Appended to the connection message above.
// supportsImages is null when image support wasn't checked (e.g. an audio-only provider that was
// tested by transcription), so there's nothing to say about images then.
const imageSupportMessage = computed(() => {
  const result = testResult.value;
  if (!result?.success || typeof result.supportsImages !== "boolean") return "";
  return result.supportsImages
    ? ` — ${i18n.t("group.ai-provider-settings.supports-images")}`
    : ` — ${i18n.t("group.ai-provider-settings.text-only-provider")}`;
});

// Fetch existing provider when editing; reset form for create mode
let requestToken = 0;

watch(
  () => [dialog.value, props.providerId] as const,
  async ([open, id]) => {
    // Bump the token even when bailing out below, so a fetch still in flight from a
    // previous provider/dialog state can never apply its (now stale) result afterward.
    const token = ++requestToken;
    if (!open) return;
    testResult.value = null;
    if (!id) {
      // Create mode — just show the empty form
      resetForm();
      init.value = true;
      return;
    }
    init.value = false;
    const { data } = await getOne(id);
    if (token !== requestToken) return;
    init.value = true;
    if (data) {
      formData.name = data.name;
      formData.model = data.model;
      formData.apiKey = "";
      formData.baseUrl = data.baseUrl ?? "";
      savedBaseUrl.value = data.baseUrl || null;
      formData.timeout = data.timeout ?? 300;
      formData.requestHeaders = { ...(data.requestHeaders ?? {}) };
      formData.requestParams = { ...(data.requestParams ?? {}) };
    }
  },
  { immediate: true },
);

function handleSubmit() {
  // The button is also disabled; this guards submit-on-enter.
  if (submitDisabled.value) return;

  if (isEdit.value && props.providerId) {
    const payload: AIProviderUpdate & { apiKey?: string } = {
      name: formData.name,
      model: formData.model,
      baseUrl: formData.baseUrl || null,
      timeout: formData.timeout,
      requestHeaders: Object.keys(formData.requestHeaders).length ? formData.requestHeaders : undefined,
      requestParams: Object.keys(formData.requestParams).length ? formData.requestParams : undefined,
    };
    if (formData.apiKey) {
      payload.apiKey = formData.apiKey;
    }
    emit("update", props.providerId, payload);
  }
  else {
    const createPayload = {
      name: formData.name,
      model: formData.model,
      apiKey: formData.apiKey,
      baseUrl: formData.baseUrl || null,
      timeout: formData.timeout,
      requestHeaders: Object.keys(formData.requestHeaders).length ? formData.requestHeaders : undefined,
      requestParams: Object.keys(formData.requestParams).length ? formData.requestParams : undefined,
    };
    emit("create", createPayload as AIProviderCreate);
  }
}

function resetForm() {
  Object.assign(formData, defaultForm());
  savedBaseUrl.value = null;
  form.reset();
  advancedPanel.value = undefined;
  testResult.value = null;
}

async function handleTest() {
  testing.value = true;
  testResult.value = null;
  try {
    let data: AIProviderTestResult | null;
    if (isEdit.value && props.providerId) {
      // Test the form's CURRENT values, not what's saved in the DB — the user may have just
      // changed the model/base_url. If they left the API key blank (meaning "keep the existing
      // one"), the backend falls back to the saved key since we don't have that value here.
      const overrides: AIProviderUpdate & { apiKey?: string } = {
        name: formData.name,
        model: formData.model,
        baseUrl: formData.baseUrl || null,
        timeout: formData.timeout,
        requestHeaders: Object.keys(formData.requestHeaders).length ? formData.requestHeaders : undefined,
        requestParams: Object.keys(formData.requestParams).length ? formData.requestParams : undefined,
      };
      if (formData.apiKey) {
        overrides.apiKey = formData.apiKey;
      }
      ({ data } = await testSavedOne(props.providerId, overrides));
    }
    else {
      ({ data } = await testOne({
        name: formData.name,
        model: formData.model,
        apiKey: formData.apiKey,
        baseUrl: formData.baseUrl || null,
        timeout: formData.timeout,
        requestHeaders: Object.keys(formData.requestHeaders).length ? formData.requestHeaders : undefined,
        requestParams: Object.keys(formData.requestParams).length ? formData.requestParams : undefined,
      } as AIProviderCreate));
    }

    testResult.value = data;
  }
  finally {
    testing.value = false;
  }
}
</script>
