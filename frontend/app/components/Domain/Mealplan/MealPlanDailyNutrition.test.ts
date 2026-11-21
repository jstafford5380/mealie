import { mount } from "@vue/test-utils";
import { expect, test } from "vitest";
import { createI18n } from "vue-i18n";
import MealPlanDailyNutrition from "./MealPlanDailyNutrition.vue";
import messages from "~/lang/messages/en-US.json";
import { makePlanEntry, makeRecipeSummary } from "~/tests/factories";

test("adds per-serving nutrition for the planned portions and flags missing data", async () => {
  const recipe = makeRecipeSummary({
    recipeServings: 2,
    nutrition: { calories: "500 kcal", proteinContent: "30 g", carbohydrateContent: "25.5", fatContent: "0" },
  });
  const dinner = makePlanEntry({ recipe, recipeScale: 0.5 });
  const lunch = makePlanEntry({
    recipe: makeRecipeSummary({ recipeServings: 1, nutrition: { calories: "150", proteinContent: "10" } }),
  });
  const wrapper = mount(MealPlanDailyNutrition, {
    props: { meals: [dinner, lunch] },
    global: { plugins: [createI18n({ legacy: false, locale: "en-US", messages: { "en-US": messages } })] },
  });
  const values = () => wrapper.findAll("dd").map(value => value.text());

  expect(values()).toEqual(["650 kcal", "40g", "25.5g", "0g"]);
  expect(wrapper.text()).toContain(messages["meal-plan"]["daily-nutrition-incomplete"]);

  await wrapper.setProps({ meals: [{ ...dinner, recipeScale: 0.45 }] });
  expect(values()).toEqual(["450 kcal", "27g", "23g", "0g"]);
  expect(wrapper.text()).not.toContain(messages["meal-plan"]["daily-nutrition-incomplete"]);

  await wrapper.setProps({ meals: [] });
  expect(values()).toEqual(["—", "—", "—", "—"]);
});
