<template>
  <div
    v-if="providerSettings"
    class="flex flex-col gap-6 font-sans"
  >
    <header v-if="!hideHeader">
      <h2 class="m-0 flex items-center gap-2 text-xl font-bold tracking-tight">
        {{ $t('group.ai-provider-settings.ai-provider-settings') }}
      </h2>
      <p class="m-0 mt-1 max-w-[65ch] text-[15px] text-muted-foreground">
        {{ $t("group.ai-provider-settings.ai-provider-settings-description") }}
      </p>
    </header>

    <!-- providers first: the selects below choose among them -->
    <section class="flex flex-col gap-3">
      <div class="flex flex-wrap items-center gap-3">
        <h3 class="m-0 flex-1 text-base font-semibold">
          {{ $t('group.ai-provider-settings.providers') }}
        </h3>
        <Button
          variant="outline"
          @click="openCreate"
        >
          <PlusIcon class="size-4" />
          {{ $t('group.ai-provider-settings.create-provider') }}
        </Button>
      </div>
      <ul
        v-if="local.providers.length"
        class="m-0 flex list-none flex-col divide-y rounded-card border bg-card p-0"
      >
        <li
          v-for="provider in local.providers"
          :key="provider.id"
          class="flex items-center gap-3 py-1.5 ps-4 pe-1.5"
        >
          <MdiIcon
            :path="$globals.icons.robot"
            class="size-5 shrink-0 text-muted-foreground"
          />
          <span class="min-w-0 flex-1 truncate font-medium">{{ provider.name }}</span>
          <span
            v-if="provider.id === local.defaultProviderId"
            class="rounded-full bg-subtle px-2 py-0.5 text-xs font-semibold text-subtle-foreground"
          >{{ $t('group.ai-provider-settings.default-badge') }}</span>
          <button
            type="button"
            class="inline-flex size-9 items-center justify-center rounded-full text-muted-foreground hover:bg-highlight hover:text-foreground"
            :aria-label="$t('data-pages.edit-item', { name: provider.name })"
            :title="$t('general.edit')"
            @click="openEdit(provider.id)"
          >
            <PencilIcon class="size-4" />
          </button>
          <button
            type="button"
            class="inline-flex size-9 items-center justify-center rounded-full text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
            :aria-label="$t('data-pages.delete-item', { name: provider.name })"
            :title="$t('general.delete')"
            @click="$emit('delete', provider.id)"
          >
            <Trash2Icon class="size-4" />
          </button>
        </li>
      </ul>
      <p
        v-else
        class="m-0 rounded-card border border-dashed px-4 py-6 text-center text-sm text-muted-foreground"
      >
        {{ $t('group.ai-provider-settings.no-providers-yet') }}
      </p>
    </section>

    <section class="flex flex-col gap-1">
      <p
        v-if="noDefaultProviderWarning"
        class="m-0 mb-2 flex items-center gap-2 rounded-control border border-brand/50 bg-brand/10 px-3 py-2 text-sm"
      >
        <MdiIcon
          :path="$globals.icons.alert"
          class="size-4 shrink-0 text-brand-strong"
        />
        {{ $t('group.ai-provider-settings.no-default-provider-warning') }}
      </p>
      <div
        v-for="choice in providerChoices"
        :key="choice.key"
      >
        <FilterSelect
          v-model="local[choice.key]"
          :items="local.providers"
          item-value="id"
          :label="choice.label"
          :disabled="!local.providers.length"
        />
        <p class="m-0 mb-2 text-sm text-muted-foreground">
          {{ choice.description }}
        </p>
      </div>
      <CheckboxField
        v-model="local.enrichNonAiImports"
        :disabled="!local.defaultProviderId"
        :label="$t('group.ai-provider-settings.enrich-non-ai-imports')"
        :hint="$t('group.ai-provider-settings.enrich-non-ai-imports-description')"
      />
    </section>

    <GroupAIProviderDialog
      v-model="dialogOpen"
      :provider-id="editingProviderId ?? undefined"
      @create="(data) => $emit('create', data)"
      @update="(id, data) => $emit('update', id, data)"
    />
  </div>
</template>

<script setup lang="ts">
import { PencilIcon, PlusIcon, Trash2Icon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import CheckboxField from "~/components/ui/field/CheckboxField.vue";
import FilterSelect from "~/components/ui/field/FilterSelect.vue";
import { MdiIcon } from "~/components/ui/mdi-icon";
import type { AIProviderCreate, AIProviderUpdate } from "~/lib/api/types/group";
import type { AIProviderSettingsOut } from "~/lib/api/types/user";

const providerSettings = defineModel<AIProviderSettingsOut>({ required: true });

const props = withDefaults(defineProps<{
  hideHeader?: boolean;
}>(), {
  hideHeader: false,
});

const { hideHeader } = toRefs(props);

const local = reactive({ ...providerSettings.value });
watch(local, (newVal) => { providerSettings.value = { ...newVal }; });
// Sync back when the parent refreshes after create/update/delete
watch(providerSettings, (newVal) => { if (newVal) Object.assign(local, newVal); });

const i18n = useI18n();
const providerChoices = computed(() => [
  {
    key: "defaultProviderId" as const,
    label: i18n.t("group.ai-provider-settings.default-provider"),
    description: i18n.t("group.ai-provider-settings.default-provider-description"),
  },
  {
    key: "audioProviderId" as const,
    label: i18n.t("group.ai-provider-settings.audio-provider"),
    description: i18n.t("group.ai-provider-settings.audio-provider-description"),
  },
  {
    key: "imageProviderId" as const,
    label: i18n.t("group.ai-provider-settings.image-provider"),
    description: i18n.t("group.ai-provider-settings.image-provider-description"),
  },
]);

const noDefaultProviderWarning = computed(
  () => local.providers.length > 0 && !local.defaultProviderId,
);

defineEmits<{
  (e: "create", data: AIProviderCreate): void;
  (e: "update", id: string, data: AIProviderUpdate): void;
  (e: "delete", id: string): void;
}>();

const dialogOpen = ref(false);
const editingProviderId = ref<string | null>(null);

function openCreate() {
  editingProviderId.value = null;
  dialogOpen.value = true;
}

function openEdit(id: string) {
  editingProviderId.value = id;
  dialogOpen.value = true;
}
</script>
