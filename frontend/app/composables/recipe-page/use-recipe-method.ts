import type { MaybeRefOrGetter } from "vue";
import type { RecipeIngredient, RecipeNote, RecipeOut, RecipeStep } from "~/lib/api/types/recipe";
import { useSessionStorage } from "@vueuse/core";

export interface MethodSection {
  title: string;
  /** Indexes into recipe.recipeInstructions. */
  steps: number[];
}

/**
 * What the reader and Cook mode need to show a recipe's method: sections, the
 * ingredients and notes linked to each step, step durations, and which steps are done.
 * Done steps are kept for the browser tab, so leaving Cook mode or reloading keeps progress.
 */
export function useRecipeMethod(recipe: MaybeRefOrGetter<RecipeOut>) {
  const i18n = useI18n();
  const steps = computed<RecipeStep[]>(() => toValue(recipe).recipeInstructions ?? []);

  const sections = computed<MethodSection[]>(() => {
    const list: MethodSection[] = [];
    steps.value.forEach((step, index) => {
      if (step.title || list.length === 0) {
        list.push({ title: step.title || "", steps: [] });
      }
      list[list.length - 1]!.steps.push(index);
    });
    return list;
  });

  const ingredientsByRef = computed(() => {
    const map: Record<string, RecipeIngredient> = {};
    for (const ing of toValue(recipe).recipeIngredient ?? []) {
      if (ing.referenceId) {
        map[ing.referenceId] = ing;
      }
    }
    return map;
  });

  const notesByRef = computed(() => {
    const map: Record<string, RecipeNote> = {};
    for (const note of toValue(recipe).notes ?? []) {
      if (note.referenceId) {
        map[note.referenceId] = note;
      }
    }
    return map;
  });

  function linkedIngredients(step: RecipeStep, from?: RecipeIngredient[]): RecipeIngredient[] {
    const ids = new Set((step.ingredientReferences ?? []).map(r => r.referenceId).filter(Boolean));
    if (!ids.size) {
      return [];
    }
    // `from` lets callers pass unit-converted ingredients while keeping recipe order
    return (from ?? toValue(recipe).recipeIngredient ?? []).filter(ing => ids.has(ing.referenceId || ""));
  }

  function linkedNotes(step: RecipeStep): RecipeNote[] {
    return (step.noteReferences ?? [])
      .map(r => (r.referenceId ? notesByRef.value[r.referenceId] : undefined))
      .filter((n): n is RecipeNote => !!n);
  }

  function formatDuration(seconds?: number | null): string {
    if (!seconds) {
      return "";
    }
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const rest = seconds % 60;
    return [
      hours ? i18n.t("recipe.step-duration-value-hours", { hours }) : "",
      minutes ? i18n.t("recipe.step-duration-value-minutes", { minutes }) : "",
      rest ? i18n.t("recipe.step-duration-value-seconds", { seconds: rest }) : "",
    ].filter(Boolean).join(" ");
  }

  const storageKey = computed(() => {
    const r = toValue(recipe);
    return `recipe-steps:${r.id || r.slug}:done`;
  });
  const doneById = useSessionStorage<Record<string, boolean>>(storageKey, {});

  function stepKey(index: number) {
    return steps.value[index]?.id || `idx:${index}`;
  }
  function isDone(index: number) {
    return !!doneById.value[stepKey(index)];
  }
  function setDone(index: number, value: boolean) {
    const key = stepKey(index);
    const next = Object.fromEntries(Object.entries(doneById.value).filter(([k]) => k !== key));
    if (value) {
      next[key] = true;
    }
    doneById.value = next;
  }
  function toggleDone(index: number) {
    setDone(index, !isDone(index));
  }
  function isSectionDone(section: MethodSection) {
    return section.steps.length > 0 && section.steps.every(isDone);
  }
  function toggleSection(section: MethodSection) {
    const value = !isSectionDone(section);
    const keys = new Set(section.steps.map(stepKey));
    const next = Object.fromEntries(Object.entries(doneById.value).filter(([k]) => !keys.has(k)));
    if (value) {
      keys.forEach((k) => {
        next[k] = true;
      });
    }
    doneById.value = next;
  }
  function resetDone() {
    doneById.value = {};
  }

  return {
    steps,
    sections,
    ingredientsByRef,
    linkedIngredients,
    linkedNotes,
    formatDuration,
    isDone,
    setDone,
    toggleDone,
    isSectionDone,
    toggleSection,
    resetDone,
  };
}
