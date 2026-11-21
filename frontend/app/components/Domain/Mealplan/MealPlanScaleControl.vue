<template>
  <RecipeScaleEditButton
    v-model="scale"
    :recipe-servings="recipeServings"
    compact
    edit-scale
  />
</template>

<script setup lang="ts">
import RecipeScaleEditButton from "~/components/Domain/Recipe/RecipeScaleEditButton.vue";
import type { MealBoardActions } from "~/composables/use-group-mealplan";
import { useMealPlanScale } from "~/composables/use-mealplan-scale";
import type { PlanEntryOut } from "~/lib/api/types/meal-plan";

const props = defineProps<{
  meal: PlanEntryOut;
  actions: Pick<MealBoardActions, "updateOne">;
  configurator?: boolean;
}>();

const { scale, recipeServings } = useMealPlanScale(
  () => props.meal,
  payload => props.actions.updateOne(payload),
  props.configurator ? 0 : undefined,
);
</script>
