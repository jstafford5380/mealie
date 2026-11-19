<template>
  <div
    v-if="household"
    class="mx-auto flex w-full max-w-[760px] flex-col px-4 pb-16 pt-3 font-sans sm:px-6 lg:pt-8"
  >
    <NuxtLink
      to="/admin/manage/households"
      class="mb-3 inline-flex w-fit items-center gap-1 text-sm font-semibold text-muted-foreground no-underline hover:text-foreground"
    >
      <ChevronLeftIcon class="size-4 rtl:rotate-180" />
      {{ $t('household.household-management') }}
    </NuxtLink>
    <header class="mb-6">
      <h1 class="m-0 text-[26px] font-bold tracking-tight sm:text-[32px]">
        {{ household.name || $t('household.admin-household-management') }}
      </h1>
      <p class="m-0 mt-1 font-mono text-xs text-muted-foreground">
        {{ $t('household.household-id-value', [household.id]) }}
      </p>
    </header>
    <form
      v-if="!userError"
      class="rounded-panel border bg-card p-5 sm:p-6"
      @submit.prevent="handleSubmit"
    >
      <div class="grid gap-x-4 sm:grid-cols-2">
        <SelectField
          v-if="groups"
          v-model="household.groupId"
          disabled
          :items="groups"
          item-title="name"
          item-value="id"
          :label="$t('group.user-group')"
        />
        <TextField
          v-model="household.name"
          :label="$t('household.household-name')"
          :rules="[validators.required]"
        />
      </div>
      <div class="mt-4 border-t pt-5">
        <HouseholdPreferencesEditor
          v-if="household.preferences"
          v-model="household.preferences"
        />
      </div>
      <div class="mt-5 flex justify-end border-t pt-4">
        <Button type="submit">
          {{ $t("general.update") }}
        </Button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ChevronLeftIcon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import SelectField from "~/components/ui/field/SelectField.vue";
import TextField from "~/components/ui/field/TextField.vue";
import HouseholdPreferencesEditor from "~/components/Domain/Household/HouseholdPreferencesEditor.vue";
import { useGroups } from "~/composables/use-groups";
import { useAdminApi } from "~/composables/api";
import { alert } from "~/composables/use-toast";
import { validators } from "~/composables/use-validators";

definePageMeta({
  layout: "admin",
});

const route = useRoute();
const i18n = useI18n();

const { groups } = useGroups();
const householdId = computed(() => route.params.id as string);

// ==============================================
// New User Form

const adminApi = useAdminApi();

const userError = ref(false);

const { data: household } = useAsyncData(`get-household-${householdId.value}`, async () => {
  if (!householdId.value) {
    return null;
  }
  const { data, error } = await adminApi.households.getOne(householdId.value);

  if (error?.response?.status === 404) {
    alert.error(i18n.t("user.user-not-found"));
    userError.value = true;
  }
  return data;
}, { watch: [householdId] });

async function handleSubmit() {
  if (household.value === null) {
    return;
  }

  const { response, data } = await adminApi.households.updateOne(household.value.id, household.value);
  if (response?.status === 200 && data) {
    household.value = data;
    alert.success(i18n.t("settings.settings-updated"));
  }
  else {
    alert.error(i18n.t("settings.settings-update-failed"));
  }
}
</script>
