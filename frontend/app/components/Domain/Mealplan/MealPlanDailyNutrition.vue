<script setup lang="ts">
import type { PlanEntryOut } from "~/lib/api/types/meal-plan";
import { parseNutritionValue, useNutritionLabels } from "~/composables/recipes";
import { getBaseServings } from "~/composables/use-mealplan-batches";

const props = defineProps<{ meals: PlanEntryOut[] }>();
const { labels } = useNutritionLabels();
const nutrients = ["calories", "proteinContent", "carbohydrateContent", "fatContent"] as const;

const totals = computed(() => {
  const portions = props.meals.map(({ recipe, recipeScale }) => ({
    nutrition: recipe?.nutrition,
    servings: getBaseServings(recipe) * (recipeScale ?? 1),
  }));

  return nutrients.map((key) => {
    let value = 0;
    let count = 0;
    for (const portion of portions) {
      const amount = parseNutritionValue(portion.nutrition?.[key]);
      if (amount !== null) {
        value += amount * portion.servings;
        count++;
      }
    }
    return {
      key,
      ...labels[key]!,
      total: count > 0 ? value : null,
      incomplete: count < portions.length,
    };
  });
});
</script>

<template>
  <footer class="text-xs">
    <p class="m-0 font-semibold">
      {{ $t("meal-plan.daily-nutrition") }}
    </p>
    <dl class="mt-1 grid grid-cols-[1fr_auto] gap-x-2 gap-y-0.5 tabular-nums">
      <template v-for="nutrient in totals" :key="nutrient.key">
        <dt class="text-muted-foreground">
          {{ nutrient.label }}
        </dt>
        <dd class="m-0 text-end">
          <template v-if="nutrient.total === null">
            —
          </template>
          <template v-else-if="nutrient.key === 'calories'">
            {{ $t("meal-plan.daily-nutrition-kcal", { amount: $n(nutrient.total, { maximumFractionDigits: 0 }) }) }}
          </template>
          <template v-else>
            {{ $n(nutrient.total, { style: "unit", unit: "gram", unitDisplay: "narrow", maximumFractionDigits: 1 }) }}
          </template>
        </dd>
      </template>
    </dl>
    <p v-if="totals.some(nutrient => nutrient.incomplete)" class="mb-0 mt-1 text-muted-foreground">
      {{ $t("meal-plan.daily-nutrition-incomplete") }}
    </p>
  </footer>
</template>
