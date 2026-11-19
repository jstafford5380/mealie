<template>
  <BaseDialog
    v-model="mealplannerDialog"
    :title="$t('recipe.add-recipe-to-mealplan')"
    :icon="$globals.icons.calendar"
    can-confirm
    @confirm="addRecipeToPlan"
  >
    <div class="flex flex-col gap-4 px-6 pb-2 font-sans">
      <MealPlanDatePicker
        v-model="pickerModel"
        :multiple="pickerMultiple"
        :entry-type="newMealType"
      />
      <label
        v-if="mealPlanPreferences.mode === 'weeks'"
        class="flex cursor-pointer items-center justify-between gap-3"
      >
        <span>
          <span class="block text-[15px] font-medium">{{ $t("meal-plan.plan-for-the-whole-week") }}</span>
          <span
            v-if="isWeekEntry"
            class="block text-sm text-muted-foreground"
          >{{ $d(weekRange.start, "short") }} – {{ $d(weekRange.end, "short") }}</span>
        </span>
        <Switch v-model="isWeekEntry" />
      </label>
      <SelectField
        v-model="newMealType"
        :items="planTypeOptions"
        :label="$t('recipe.entry-type')"
        item-title="text"
        item-value="value"
      />
    </div>
  </BaseDialog>
</template>

<script setup lang="ts">
import SelectField from "~/components/ui/field/SelectField.vue";
import { Switch } from "~/components/ui/switch";
import { useUserApi } from "~/composables/api";
import { useMealPlanEntryDates } from "~/composables/use-group-mealplan";
import { alert } from "~/composables/use-toast";
import { useUserMealPlanPreferences } from "~/composables/use-users/preferences";
import type { PlanEntryType } from "~/lib/api/types/meal-plan";

const props = withDefaults(defineProps<{
  recipeId: string;
  recipeScale?: number;
}>(), {
  recipeScale: 1,
});

const mealplannerDialog = defineModel<boolean>({
  default: false,
});

const i18n = useI18n();
const api = useUserApi();
const planTypeOptions = usePlanTypeOptions();
const router = useRouter();

const mealPlanPreferences = useUserMealPlanPreferences();
const newMealType = ref<PlanEntryType>("dinner");
const { isWeekEntry, weekRange, entryDatesPayload, pickerModel, pickerMultiple } = useMealPlanEntryDates();

async function addRecipeToPlan() {
  const { response } = await api.mealplans.createOne({
    ...entryDatesPayload.value,
    entryType: newMealType.value,
    title: "",
    text: "",
    recipeId: props.recipeId,
    recipeScale: props.recipeScale,
  });

  if (response?.status === 201) {
    alert.success(i18n.t("recipe.recipe-added-to-mealplan"), null, {
      action: {
        message: i18n.t("general.view"),
        onClick: () => router.push("/household/mealplan/planner/view"),
      },
    });
  }
  else {
    alert.error(i18n.t("recipe.failed-to-add-recipe-to-mealplan"));
  }
}
</script>
