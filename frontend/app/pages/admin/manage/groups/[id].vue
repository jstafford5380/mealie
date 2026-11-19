<template>
  <div
    v-if="group"
    class="mx-auto flex w-full max-w-[760px] flex-col gap-6 px-4 pb-16 pt-3 font-sans sm:px-6 lg:pt-8"
  >
    <div>
      <NuxtLink
        to="/admin/manage/groups"
        class="mb-3 inline-flex w-fit items-center gap-1 text-sm font-semibold text-muted-foreground no-underline hover:text-foreground"
      >
        <ChevronLeftIcon class="size-4 rtl:rotate-180" />
        {{ $t('group.group-management') }}
      </NuxtLink>
      <header class="mb-0">
        <h1 class="m-0 text-[26px] font-bold tracking-tight sm:text-[32px]">
          {{ group.name || $t('group.admin-group-management') }}
        </h1>
        <p class="m-0 mt-1 font-mono text-xs text-muted-foreground">
          {{ $t('group.group-id-value', [group.id]) }}
        </p>
      </header>
    </div>
    <form
      v-if="!userError"
      class="flex flex-col gap-6"
      @submit.prevent="handleSubmit"
    >
      <section class="rounded-panel border bg-card p-5 sm:p-6">
        <div class="max-w-md">
          <TextField
            v-model="group.name"
            :label="$t('group.group-name')"
          />
        </div>
        <h2 class="m-0 mt-4 mb-3 border-t pt-5 text-base font-semibold">
          {{ $t('group.group-preferences') }}
        </h2>
        <GroupPreferencesEditor
          v-if="group.preferences"
          v-model="group.preferences"
        />
      </section>
      <section class="rounded-panel border bg-card p-5 sm:p-6">
        <GroupAIProviderSettingsEditor
          v-if="group.aiProviderSettings"
          v-model="group.aiProviderSettings"
          @create="handleCreateProvider"
          @update="handleUpdateProvider"
          @delete="handleDeleteProvider"
        />
      </section>
      <div class="flex justify-end">
        <Button type="submit">
          {{ $t("general.update") }}
        </Button>
      </div>
    </form>
    <section
      v-if="!userError"
      class="rounded-panel border bg-card p-5 sm:p-6"
    >
      <GroupAIPromptEditor :group-id="group.id" />
    </section>
  </div>
</template>

<script setup lang="ts">
import { ChevronLeftIcon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import TextField from "~/components/ui/field/TextField.vue";
import GroupPreferencesEditor from "~/components/Domain/Group/GroupPreferencesEditor.vue";
import GroupAIProviderSettingsEditor from "~/components/Domain/Group/GroupAIProviderSettingsEditor.vue";
import GroupAIPromptEditor from "~/components/Domain/Group/GroupAIPromptEditor.vue";
import { useAdminApi } from "~/composables/api";
import { alert } from "~/composables/use-toast";
import type { AIProviderCreate, AIProviderUpdate } from "~/lib/api/types/group";

definePageMeta({
  layout: "admin",
});
const route = useRoute();

const i18n = useI18n();

const groupId = computed(() => route.params.id as string);

// ==============================================
// New User Form

const adminApi = useAdminApi();

const userError = ref(false);

const { data: group, refresh } = useLazyAsyncData(`get-household-${groupId.value}`, async () => {
  if (!groupId.value) {
    return null;
  }
  const { data, error } = await adminApi.groups.getOne(groupId.value);

  if (error?.response?.status === 404) {
    alert.error(i18n.t("user.user-not-found"));
    userError.value = true;
  }
  return data;
}, { watch: [groupId] });

async function handleSubmit() {
  if (!group.value) {
    return;
  }

  const { response, data } = await adminApi.groups.updateOne(group.value.id, group.value);
  if (response?.status === 200 && data) {
    if (group.value.slug !== data.slug) {
      // the slug updated, which invalidates the nav URLs
      window.location.reload();
    }
    group.value = data;
    alert.success(i18n.t("settings.settings-updated"));
  }
  else {
    alert.error(i18n.t("settings.settings-update-failed"));
  }
}

async function handleCreateProvider(data: AIProviderCreate) {
  if (!group.value) return;
  const result = await adminApi.aiProviders.createProvider(group.value.id, data);
  if (result.data) {
    await refresh();
    alert.success(i18n.t("group.ai-provider-settings.provider-created"));
  }
  else {
    alert.error(i18n.t("group.ai-provider-settings.provider-create-failed"));
  }
}

async function handleUpdateProvider(id: string, data: AIProviderUpdate) {
  if (!group.value) return;
  const result = await adminApi.aiProviders.updateProvider(group.value.id, id, data);
  if (result.data) {
    await refresh();
    alert.success(i18n.t("group.ai-provider-settings.provider-updated"));
  }
  else {
    alert.error(i18n.t("group.ai-provider-settings.provider-update-failed"));
  }
}

async function handleDeleteProvider(id: string) {
  if (!group.value) return;
  const result = await adminApi.aiProviders.deleteProvider(group.value.id, id);
  if (result.data) {
    await refresh();
    alert.success(i18n.t("group.ai-provider-settings.provider-deleted"));
  }
  else {
    alert.error(i18n.t("group.ai-provider-settings.provider-delete-failed"));
  }
}
</script>
