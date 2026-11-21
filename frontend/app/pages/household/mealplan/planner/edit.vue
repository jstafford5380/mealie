<template>
  <MealPlanBoard
    :mealplans="mealplans"
    :batch-entries="batchEntries"
    :actions="actions"
  />
</template>

<script setup lang="ts">
import MealPlanBoard from "~/components/Domain/Mealplan/MealPlanBoard.vue";
import type { MealsByDate, useMealplans } from "~/composables/use-group-mealplan";
import type { PlanEntryOut } from "~/lib/api/types/meal-plan";

// View and Edit are one board now; both routes stay so existing links keep working.
defineProps<{
  mealplans: MealsByDate[];
  batchEntries: PlanEntryOut[];
  actions: ReturnType<typeof useMealplans>["actions"];
}>();
</script>
