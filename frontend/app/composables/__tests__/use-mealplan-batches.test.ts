import { expect, test } from "vitest";
import { getScaledRecipes } from "../use-group-mealplan";
import { copyMealToSlot, getBatchBalance, planRemainingLeftovers, projectMealBatches } from "../use-mealplan-batches";
import { makePlanEntry, makeRecipeSummary } from "~/tests/factories";

test("projects each batch independently and keeps shopping quantities separate from portions eaten", () => {
  const recipe = makeRecipeSummary({ recipeServings: 4 });
  const first = makePlanEntry({
    id: 1,
    date: "2026-11-16",
    entryType: "dinner",
    recipe,
    recipeId: recipe.id,
    recipeBatchId: "first",
    recipeScale: 0.25,
  });
  const earlierLunch = makePlanEntry({
    ...first,
    id: 2,
    entryType: "lunch",
    recipeBatchId: null,
    leftoverBatchId: "first",
  });
  const leftovers = makePlanEntry({ ...earlierLunch, id: 3, date: "2026-11-17" });
  const second = makePlanEntry({ ...first, id: 4, date: "2026-11-20", recipeBatchId: "second" });
  const meals = [first, earlierLunch, leftovers, second];

  const { batches, unlinked } = projectMealBatches(meals);
  expect(unlinked).toEqual([earlierLunch]);
  expect(batches.map(batch => getBatchBalance(batch, batch.source.date))).toEqual([3, 3]);
  expect(getBatchBalance(batches[0]!, "2026-11-17")).toBe(2);
  expect(getBatchBalance(batches[0]!, "2026-11-17", leftovers.id)).toBe(3);
  expect(getScaledRecipes(meals).map(recipe => recipe.scale)).toEqual([1, 1]);

  const overbooked = projectMealBatches([first, { ...leftovers, recipeScale: 1 }]);
  expect(getBatchBalance(overbooked.batches[0]!, "2026-11-17")).toBe(-1);
});

test("dropping a batch plans its full unallocated remainder", () => {
  const recipe = makeRecipeSummary({ recipeServings: 4 });
  const source = makePlanEntry({ date: "2026-11-16", entryType: "dinner", recipe, recipeId: recipe.id, recipeScale: 0.25 });
  const batch = { id: "monday", source, uses: [] };
  expect(planRemainingLeftovers(batch, "2026-11-17", "lunch")).toEqual({
    date: "2026-11-17",
    entryType: "lunch",
    recipeId: recipe.id,
    recipeScale: 0.75,
    leftoverBatchId: "monday",
  });
  expect(planRemainingLeftovers(batch, "2026-11-16", "lunch")).toBeNull();

  const reserved = { ...batch, uses: [makePlanEntry({ id: 2, date: "2026-11-18", recipe, recipeScale: 0.5 })] };
  expect(planRemainingLeftovers(reserved, "2026-11-17", "lunch")?.recipeScale).toBe(0.25);
  expect(planRemainingLeftovers({ ...reserved, uses: [{ ...reserved.uses[0]!, recipeScale: 0.75 }] }, "2026-11-17", "lunch")).toBeNull();
});

test("copies a fresh batch independently and caps a leftover copy at the unallocated portion", () => {
  const recipe = makeRecipeSummary({ recipeServings: 4 });
  const source = makePlanEntry({
    id: 1,
    date: "2026-11-16",
    recipe,
    recipeId: recipe.id,
    recipeBatchId: "monday",
    recipeScale: 0.25,
  });
  const original = makePlanEntry({
    id: 2,
    date: "2026-11-17",
    recipe,
    recipeId: recipe.id,
    leftoverBatchId: "monday",
    recipeScale: 0.5,
  });
  const destination = { date: "2026-11-18", entryType: "dinner" } as const;
  const batch = { id: "monday", source, uses: [original] };

  const freshCopy = copyMealToSlot(source, destination, [batch]);
  expect(freshCopy).toMatchObject({ ...destination, recipeId: recipe.id, recipeScale: 0.25 });
  expect(freshCopy?.recipeBatchId).toMatch(/^[\da-f-]{36}$/);
  expect(freshCopy?.recipeBatchId).not.toBe(source.recipeBatchId);
  expect(copyMealToSlot(original, destination, [batch])).toMatchObject({
    ...destination,
    recipeId: recipe.id,
    recipeScale: 0.25,
    leftoverBatchId: "monday",
  });
  expect(copyMealToSlot(original, destination, [{ ...batch, uses: [{ ...original, recipeScale: 0.75 }] }])).toBeNull();
});
