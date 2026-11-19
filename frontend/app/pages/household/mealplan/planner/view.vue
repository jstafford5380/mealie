<template>
  <MealPlanBoard
    :mealplans="mealplans"
    :actions="actions"
  />
</template>

<script setup lang="ts">
import MealPlanBoard from "~/components/Domain/Mealplan/MealPlanBoard.vue";
import type { MealsByDate, useMealplans } from "~/composables/use-group-mealplan";

// View and Edit are one board now; both routes stay so existing links keep working.
defineProps<{
  mealplans: MealsByDate[];
  actions: ReturnType<typeof useMealplans>["actions"];
}>();
</script>
