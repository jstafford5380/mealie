<template>
  <div
    v-if="preferences"
    class="flex flex-col gap-3 font-sans"
  >
    <div>
      <CheckboxField
        v-model="local.privateHousehold"
        :label="$t('household.private-household')"
        :hint="$t('household.private-household-description')"
      />
      <DocLink
        class="ms-7"
        link="/documentation/getting-started/faq/#how-do-private-groups-households-and-recipes-work"
      />
    </div>
    <CheckboxField
      v-model="local.lockRecipeEditsFromOtherHouseholds"
      :label="$t('household.lock-recipe-edits-from-other-households')"
      :hint="`${$t('household.lock-recipe-edits-from-other-households-description')} ${$t('household.lock-recipe-edits-from-other-households-admin-note')}`"
    />
    <CheckboxField
      v-model="local.showAnnouncements"
      :label="$t('announcements.show-announcements-from-mealie')"
      :hint="$t('announcements.show-announcements-setting-description')"
    />
    <div class="max-w-xs">
      <SelectField
        v-model="local.firstDayOfWeek"
        :items="allDays"
        item-title="name"
        item-value="value"
        :label="$t('settings.first-day-of-week')"
      />
    </div>

    <section class="mt-4 flex flex-col gap-3 border-t pt-5">
      <header>
        <h3 class="m-0 text-base font-semibold">
          {{ $t("household.household-recipe-preferences") }}
        </h3>
        <p class="m-0 mt-1 text-sm text-muted-foreground">
          {{ $t("household.default-recipe-preferences-description") }}
        </p>
      </header>
      <CheckboxField
        v-for="p in recipePreferences"
        :key="p.key"
        :model-value="!!local[p.key]"
        :label="p.label"
        :hint="p.description"
        @update:model-value="(local as Record<string, unknown>)[p.key] = $event"
      />
    </section>
  </div>
</template>

<script setup lang="ts">
import CheckboxField from "~/components/ui/field/CheckboxField.vue";
import SelectField from "~/components/ui/field/SelectField.vue";
import type { HouseholdPreferencesOut } from "~/lib/api/types/household";

const preferences = defineModel<HouseholdPreferencesOut>({ required: true });
const local = reactive({ ...preferences.value });
watch(local, (newVal) => { preferences.value = { ...newVal }; });
watch(preferences, (newVal) => { if (newVal) Object.assign(local, newVal); });

const i18n = useI18n();

type Preference = {
  key: keyof HouseholdPreferencesOut;
  label: string;
  description: string;
};

const recipePreferences: Preference[] = [
  {
    key: "recipePublic",
    label: i18n.t("group.allow-users-outside-of-your-group-to-see-your-recipes"),
    description: i18n.t("group.allow-users-outside-of-your-group-to-see-your-recipes-description"),
  },
  {
    key: "recipeShowNutrition",
    label: i18n.t("group.show-nutrition-information"),
    description: i18n.t("group.show-nutrition-information-description"),
  },
  {
    key: "recipeShowAssets",
    label: i18n.t("group.show-recipe-assets"),
    description: i18n.t("group.show-recipe-assets-description"),
  },
  {
    key: "recipeLandscapeView",
    label: i18n.t("group.default-to-landscape-view"),
    description: i18n.t("group.default-to-landscape-view-description"),
  },
  {
    key: "recipeDisableComments",
    label: i18n.t("group.disable-users-from-commenting-on-recipes"),
    description: i18n.t("group.disable-users-from-commenting-on-recipes-description"),
  },
];

const allDays = [
  {
    name: i18n.t("general.sunday"),
    value: 0,
  },
  {
    name: i18n.t("general.monday"),
    value: 1,
  },
  {
    name: i18n.t("general.tuesday"),
    value: 2,
  },
  {
    name: i18n.t("general.wednesday"),
    value: 3,
  },
  {
    name: i18n.t("general.thursday"),
    value: 4,
  },
  {
    name: i18n.t("general.friday"),
    value: 5,
  },
  {
    name: i18n.t("general.saturday"),
    value: 6,
  },
];
</script>
