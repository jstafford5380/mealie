<template>
  <div
    v-if="group"
    class="mx-auto flex w-full max-w-[760px] flex-col gap-8 px-4 pb-16 pt-3 font-sans sm:px-6 lg:pt-8"
  >
    <header class="mb-6">
      <h1 class="m-0 text-[26px] font-bold tracking-tight sm:text-[32px]">
        {{ $t("profile.group-settings") }}
      </h1>
      <p class="m-0 mt-1 max-w-[65ch] text-[15px] text-muted-foreground">
        {{ $t("profile.group-description") }}
      </p>
    </header>

    <form
      class="rounded-panel border bg-card p-5 sm:p-6"
      @submit.prevent="handlePrefsSubmit"
    >
      <h2 class="m-0 mb-4 text-xl font-bold tracking-tight">
        {{ $t('group.group-preferences') }}
      </h2>
      <GroupPreferencesEditor
        v-if="group.preferences"
        v-model="group.preferences"
      />
      <div class="mt-5 flex justify-end border-t pt-4">
        <Button type="submit">
          {{ $t("general.update") }}
        </Button>
      </div>
    </form>

    <form
      class="rounded-panel border bg-card p-5 sm:p-6"
      @submit.prevent="handleAISettingsSubmit"
    >
      <GroupAIProviderSettingsEditor
        v-if="group.aiProviderSettings"
        v-model="group.aiProviderSettings"
        @create="handleCreateProvider"
        @update="handleUpdateProvider"
        @delete="handleDeleteProvider"
      />
      <div class="mt-5 flex justify-end border-t pt-4">
        <Button type="submit">
          {{ $t("general.update") }}
        </Button>
      </div>
    </form>

    <section class="rounded-panel border bg-card p-5 sm:p-6">
      <GroupAIPromptEditor />
    </section>
  </div>
</template>

<script setup lang="ts">
import { Button } from "~/components/ui/button";
import GroupPreferencesEditor from "~/components/Domain/Group/GroupPreferencesEditor.vue";
import GroupAIProviderSettingsEditor from "~/components/Domain/Group/GroupAIProviderSettingsEditor.vue";
import GroupAIPromptEditor from "~/components/Domain/Group/GroupAIPromptEditor.vue";
import { useGroupSelf } from "~/composables/use-groups";
import { useAIProviders } from "~/composables/use-ai-providers";
import { alert } from "~/composables/use-toast";
import type { AIProviderCreate, AIProviderUpdate } from "~/lib/api/types/group";

definePageMeta({
  middleware: ["auth", "can-manage-only"],
});

const { group, actions: groupActions } = useGroupSelf();
const i18n = useI18n();

useSeoMeta({
  title: i18n.t("group.group"),
});

// useGroupSelf() caches data in a module-level singleton for the lifetime of the tab,
// so revisiting this page via client-side navigation can otherwise show stale
// preferences/AI settings if they were changed elsewhere (e.g. Admin Groups panel)
// in the same session. Force a revalidation whenever this page is entered.
onMounted(() => {
  groupActions.refresh();
});

async function handlePrefsSubmit() {
  if (!group.value?.preferences) {
    return;
  }

  const data = await groupActions.updatePreferences();
  if (data) {
    alert.success(i18n.t("settings.settings-updated"));
  }
  else {
    alert.error(i18n.t("settings.settings-update-failed"));
  }
}

async function handleAISettingsSubmit() {
  if (!group.value?.aiProviderSettings) {
    return;
  }

  const data = await groupActions.updateAIProviderSettings();
  if (data) {
    alert.success(i18n.t("settings.settings-updated"));
  }
  else {
    alert.error(i18n.t("settings.settings-update-failed"));
  }
}

const { createOne, updateOne, deleteOne } = useAIProviders();

async function handleCreateProvider(data: AIProviderCreate) {
  const result = await createOne(data);
  if (result.data) {
    await groupActions.refresh();
    alert.success(i18n.t("group.ai-provider-settings.provider-created"));
  }
  else {
    alert.error(i18n.t("group.ai-provider-settings.provider-create-failed"));
  }
}

async function handleUpdateProvider(id: string, data: AIProviderUpdate) {
  const result = await updateOne(id, data);
  if (result.data) {
    await groupActions.refresh();
    alert.success(i18n.t("group.ai-provider-settings.provider-updated"));
  }
  else {
    alert.error(i18n.t("group.ai-provider-settings.provider-update-failed"));
  }
}

async function handleDeleteProvider(id: string) {
  const result = await deleteOne(id);
  if (result.data) {
    await groupActions.refresh();
    alert.success(i18n.t("group.ai-provider-settings.provider-deleted"));
  }
  else {
    alert.error(i18n.t("group.ai-provider-settings.provider-delete-failed"));
  }
}
</script>

<style lang="css">
.preference-container {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-width: 600px;
}
</style>
