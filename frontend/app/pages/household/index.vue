<template>
  <div
    v-if="household"
    class="mx-auto flex w-full max-w-[760px] flex-col px-4 pb-16 pt-3 font-sans sm:px-6 lg:pt-8"
  >
    <header class="mb-6">
      <h1 class="m-0 text-[26px] font-bold tracking-tight sm:text-[32px]">
        {{ $t("profile.household-settings") }}
      </h1>
      <p class="m-0 mt-1 max-w-[65ch] text-[15px] text-muted-foreground">
        {{ $t("profile.household-description") }}
      </p>
    </header>

    <form
      class="rounded-panel border bg-card p-5 sm:p-6"
      @submit.prevent="handleSubmit"
    >
      <h2 class="m-0 mb-4 text-xl font-bold tracking-tight">
        {{ $t('household.household-preferences') }}
      </h2>
      <HouseholdPreferencesEditor
        v-if="household.preferences"
        v-model="household.preferences"
      />
      <div class="mt-5 flex justify-end border-t pt-4">
        <Button type="submit">
          {{ $t("general.update") }}
        </Button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { Button } from "~/components/ui/button";
import HouseholdPreferencesEditor from "~/components/Domain/Household/HouseholdPreferencesEditor.vue";
import { useHouseholdSelf } from "~/composables/use-households";
import { alert } from "~/composables/use-toast";

definePageMeta({
  middleware: ["auth", "can-manage-household-only"],
});

const { household, actions: householdActions } = useHouseholdSelf();
const i18n = useI18n();

useSeoMeta({
  title: i18n.t("household.household"),
});

// useHouseholdSelf() caches data in a module-level singleton for the lifetime of the tab,
// so revisiting this page via client-side navigation can otherwise show stale
// preferences if they were changed elsewhere (e.g. Admin Households panel) in the
// same session. Force a revalidation whenever this page is entered.
onMounted(() => {
  householdActions.refresh();
});

async function handleSubmit() {
  if (!household.value?.preferences) {
    return;
  }

  const data = await householdActions.updatePreferences();
  if (data) {
    alert.success(i18n.t("settings.settings-updated"));
  }
  else {
    alert.error(i18n.t("settings.settings-update-failed"));
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
