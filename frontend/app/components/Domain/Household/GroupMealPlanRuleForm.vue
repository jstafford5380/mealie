<template>
  <QueryFilterSummary
    v-if="readonly"
    :field-defs="fieldDefs"
    :query-filter="props.queryFilter"
  />
  <div
    v-else
    class="flex flex-col gap-4 font-sans"
  >
    <div class="grid gap-3 md:grid-cols-2">
      <SelectField
        v-model="day"
        :items="MEAL_DAY_OPTIONS"
        :label="$t('meal-plan.rule-day')"
        :hint="day === 'unset' ? '' : $t('meal-plan.weekday-rules-skip-week-entries')"
      />
      <SelectField
        v-model="entryType"
        :items="MEAL_TYPE_OPTIONS"
        :label="$t('meal-plan.meal-type')"
      />
    </div>

    <QueryFilterBuilder
      :field-defs="fieldDefs"
      :initial-query-filter="props.queryFilter"
      @input="handleQueryFilterInput"
    />

    <!-- TODO: proper pluralization of inputDay -->
    <p class="m-0 rounded-control bg-muted px-3 py-2 text-sm text-muted-foreground">
      {{ $t("meal-plan.this-rule-will-apply", {
        dayCriteria: day === "unset"
          ? $t("meal-plan.to-all-days")
          : $t("meal-plan.on-days", [$t("general." + day)]),
        mealTypeCriteria: entryType === "unset"
          ? $t("meal-plan.for-all-meal-types")
          : $t("meal-plan.for-type-meal-types", [$t("meal-plan." + entryType)]),
      }) }}
    </p>
  </div>
</template>

<script setup lang="ts">
import SelectField from "~/components/ui/field/SelectField.vue";
import QueryFilterBuilder from "~/components/Domain/QueryFilterBuilder.vue";
import QueryFilterSummary from "~/components/Domain/QueryFilterSummary.vue";
import { useRecipeFilterFields } from "~/composables/use-recipe-filter-fields";
import type { QueryFilterJSON } from "~/lib/api/types/non-generated";

interface Props {
  queryFilter?: QueryFilterJSON | null;
  showHelp?: boolean;
  readonly?: boolean;
}
const props = withDefaults(defineProps<Props>(), {
  queryFilter: null,
  showHelp: false,
  readonly: false,
});

const day = defineModel<string>("day", { default: "unset" });
const entryType = defineModel<string>("entryType", { default: "unset" });
const queryFilterString = defineModel<string>("queryFilterString", { default: "" });

const i18n = useI18n();

const MEAL_TYPE_OPTIONS = [
  { title: i18n.t("meal-plan.breakfast"), value: "breakfast" },
  { title: i18n.t("meal-plan.lunch"), value: "lunch" },
  { title: i18n.t("meal-plan.dinner"), value: "dinner" },
  { title: i18n.t("meal-plan.side"), value: "side" },
  { title: i18n.t("meal-plan.snack"), value: "snack" },
  { title: i18n.t("meal-plan.drink"), value: "drink" },
  { title: i18n.t("meal-plan.dessert"), value: "dessert" },
  { title: i18n.t("meal-plan.type-any"), value: "unset" },
];

const MEAL_DAY_OPTIONS = [
  { title: i18n.t("general.monday"), value: "monday" },
  { title: i18n.t("general.tuesday"), value: "tuesday" },
  { title: i18n.t("general.wednesday"), value: "wednesday" },
  { title: i18n.t("general.thursday"), value: "thursday" },
  { title: i18n.t("general.friday"), value: "friday" },
  { title: i18n.t("general.saturday"), value: "saturday" },
  { title: i18n.t("general.sunday"), value: "sunday" },
  { title: i18n.t("meal-plan.day-any"), value: "unset" },
];

function handleQueryFilterInput(value: string | undefined) {
  queryFilterString.value = value || "";
}

const fieldDefs = useRecipeFilterFields();
</script>
