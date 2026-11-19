import { beforeEach, describe, expect, test, vi } from "vitest";
import { nextTick } from "vue";
import type { RecipeOut } from "~/lib/api/types/recipe";
import { useRecipeMethod } from "../use-recipe-method";

vi.mock("vue-i18n", async importOriginal => ({
  ...(await importOriginal<typeof import("vue-i18n")>()),
  useI18n: () => ({ t: (key: string, values?: Record<string, unknown>) => `${key}:${JSON.stringify(values ?? {})}` }),
}));

function makeRecipe(): RecipeOut {
  return {
    id: "recipe-1",
    slug: "test",
    recipeIngredient: [
      { referenceId: "a", note: "Flour" },
      { referenceId: "b", note: "Eggs" },
      { referenceId: "c", note: "Salt" },
    ],
    notes: [{ referenceId: "n1", title: "Tip", text: "Rest the dough" }],
    recipeInstructions: [
      { id: "s1", title: "Dough", text: "Mix", ingredientReferences: [{ referenceId: "b" }, { referenceId: "a" }] },
      { id: "s2", title: "", text: "Knead", noteReferences: [{ referenceId: "n1" }] },
      { id: "s3", title: "Bake", text: "Bake", durationSeconds: 3900 },
    ],
  } as unknown as RecipeOut;
}

describe("useRecipeMethod", () => {
  beforeEach(() => sessionStorage.clear());

  test("groups steps into sections by step titles", () => {
    const { sections } = useRecipeMethod(makeRecipe());
    expect(sections.value).toEqual([
      { title: "Dough", steps: [0, 1] },
      { title: "Bake", steps: [2] },
    ]);
  });

  test("returns linked ingredients in recipe order and linked notes", () => {
    const recipe = makeRecipe();
    const { linkedIngredients, linkedNotes } = useRecipeMethod(recipe);
    expect(linkedIngredients(recipe.recipeInstructions[0]!).map(i => i.note)).toEqual(["Flour", "Eggs"]);
    expect(linkedNotes(recipe.recipeInstructions[1]!).map(n => n.title)).toEqual(["Tip"]);
    expect(linkedIngredients(recipe.recipeInstructions[2]!)).toEqual([]);
  });

  test("formats step durations", () => {
    const { formatDuration } = useRecipeMethod(makeRecipe());
    expect(formatDuration(null)).toBe("");
    expect(formatDuration(3900)).not.toBe("");
  });

  test("shares done steps between instances and toggles whole sections", async () => {
    const first = useRecipeMethod(makeRecipe());
    first.toggleDone(1);
    await nextTick();

    const second = useRecipeMethod(makeRecipe());
    expect(second.isDone(1)).toBe(true);
    expect(second.isDone(0)).toBe(false);

    second.toggleSection(second.sections.value[0]!);
    expect(second.isDone(0) && second.isDone(1)).toBe(true);
    second.toggleSection(second.sections.value[0]!);
    expect(second.isDone(0) || second.isDone(1)).toBe(false);

    second.setDone(2, true);
    second.resetDone();
    expect(second.isDone(2)).toBe(false);
  });
});
