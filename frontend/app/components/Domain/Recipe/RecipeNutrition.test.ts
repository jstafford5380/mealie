import { mount } from "@vue/test-utils";
import { createI18n } from "vue-i18n";
import { expect, test } from "vitest";
import RecipeNutrition from "./RecipeNutrition.vue";
import messages from "~/lang/messages/en-US.json";

test("displays saved per-serving nutrition with units", () => {
  const i18n = createI18n({ legacy: false, locale: "en-US", messages: { "en-US": messages } });
  const wrapper = mount(RecipeNutrition, {
    props: {
      edit: false,
      modelValue: {
        calories: "503",
        proteinContent: "37",
        carbohydrateContent: "59",
        fatContent: "13",
        fiberContent: "7",
        sodiumContent: null,
      },
    },
    global: { plugins: [i18n] },
  });

  expect(wrapper.get("h2").text()).toContain(messages.recipe["per-serving"]);
  expect(wrapper.findAll("dd").map(value => value.text())).toEqual([
    "503" + messages.recipe["calories-suffix"],
    "59" + messages.recipe.grams,
    "13" + messages.recipe.grams,
    "7" + messages.recipe.grams,
    "37" + messages.recipe.grams,
  ]);
});
