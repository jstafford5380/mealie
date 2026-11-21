import type { PlanEntryCreate, PlanEntryOut, PlanEntryType, RecipeSummary } from "~/lib/api/types/meal-plan";
import { uuid4 } from "./use-utils";

export const leftoverDragType = "application/x-mealie-leftover-batch";

const mealOrder: PlanEntryType[] = ["breakfast", "lunch", "dinner", "side", "snack", "drink", "dessert"];

export function getBaseServings(recipe: RecipeSummary | null | undefined): number {
  return recipe?.recipeServings || recipe?.recipeYieldQuantity || 1;
}

function getServings(entry: PlanEntryOut): number {
  return getBaseServings(entry.recipe) * (entry.recipeScale ?? 1);
}

export function batchPrecedesMeal(source: PlanEntryOut, date: string, type: PlanEntryType): boolean {
  return source.date < date || (source.date === date && mealOrder.indexOf(source.entryType) <= mealOrder.indexOf(type));
}

export interface MealBatch {
  id: string;
  source: PlanEntryOut;
  uses: PlanEntryOut[];
}

export function projectMealBatches(entries: PlanEntryOut[]) {
  const batches = new Map<string, MealBatch>();
  const unlinked: PlanEntryOut[] = [];

  for (const source of entries) {
    if (source.recipeBatchId && source.recipe && !source.endDate) {
      batches.set(source.recipeBatchId, { id: source.recipeBatchId, source, uses: [] });
    }
  }
  for (const entry of entries) {
    if (!entry.leftoverBatchId) continue;
    const batch = batches.get(entry.leftoverBatchId);
    if (batch && entry.recipeId === batch.source.recipeId && !entry.endDate
      && batchPrecedesMeal(batch.source, entry.date, entry.entryType)) {
      batch.uses.push(entry);
    }
    else {
      unlinked.push(entry);
    }
  }
  return { batches: [...batches.values()].sort((a, b) => a.source.date.localeCompare(b.source.date)), unlinked };
}

export function getBatchBalance(batch: MealBatch, throughDate: string, excludeEntryId?: number | null): number {
  const initial = getBaseServings(batch.source.recipe) - getServings(batch.source);
  const used = batch.uses.reduce(
    (total, entry) => entry.date <= throughDate && entry.id !== excludeEntryId ? total + getServings(entry) : total,
    0,
  );
  return Math.round((initial - used) * 1e6) / 1e6;
}

export function getAvailableLeftovers(batch: MealBatch, excludeEntryId?: number | null): number {
  return getBatchBalance(batch, "9999-12-31", excludeEntryId);
}

export function planRemainingLeftovers(batch: MealBatch, date: string, entryType: PlanEntryType): PlanEntryCreate | null {
  const remaining = getAvailableLeftovers(batch);
  if (!batch.source.recipeId || remaining <= 0 || !batchPrecedesMeal(batch.source, date, entryType)) return null;

  return {
    date,
    entryType,
    recipeId: batch.source.recipeId,
    recipeScale: remaining / getBaseServings(batch.source.recipe),
    leftoverBatchId: batch.id,
  };
}

export function copyMealToSlot(
  meal: PlanEntryOut,
  slot: Pick<PlanEntryCreate, "date" | "endDate" | "entryType">,
  batches: MealBatch[],
): PlanEntryCreate | null {
  const entryType = slot.entryType ?? meal.entryType;
  if (meal.leftoverBatchId) {
    const batch = batches.find(batch => batch.id === meal.leftoverBatchId && batch.source.recipeId === meal.recipeId);
    const available = !slot.endDate && batch && planRemainingLeftovers(batch, slot.date, entryType);
    if (!available) return null;
    return { ...available, recipeScale: Math.min(available.recipeScale ?? 1, meal.recipeScale ?? 1) };
  }

  if (meal.recipeBatchId && slot.endDate) return null;
  return {
    ...slot,
    entryType,
    title: meal.title,
    text: meal.text,
    recipeId: meal.recipeId,
    recipeScale: meal.recipeScale,
    recipeBatchId: meal.recipeBatchId ? uuid4() : null,
  };
}
