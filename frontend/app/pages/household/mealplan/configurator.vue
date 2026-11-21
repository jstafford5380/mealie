<template>
  <div class="mx-auto w-full max-w-[1440px] px-4 pb-16 pt-4 font-sans sm:px-6 lg:px-8 lg:pt-8">
    <Button as-child variant="ghost" class="mb-3">
      <NuxtLink to="/household/mealplan/planner/view">
        {{ $t("meal-plan.meal-planner") }}
      </NuxtLink>
    </Button>
    <h1 class="mb-6 text-[28px] font-bold tracking-tight sm:text-[32px]">
      {{ $t("meal-plan.configurator") }}
    </h1>

    <div class="mb-6 flex flex-wrap items-end gap-3">
      <SelectField
        v-if="savedPlans.length"
        :model-value="draft?.id ?? null"
        :items="savedPlans.map(({ id, name }) => ({ value: id, title: name }))"
        :label="$t('meal-plan.saved-plan-select')"
        :disabled="busy"
        class="w-full sm:w-64"
        @update:model-value="openPlan"
      />
      <Button :disabled="busy" variant="outline" @click="newPlan">
        {{ $t("meal-plan.new-saved-plan") }}
      </Button>
    </div>

    <p v-if="error" role="alert" class="mb-4 text-sm text-destructive">
      {{ error }}
    </p>
    <p v-if="status" role="status" class="mb-4 text-sm text-muted-foreground">
      {{ status }}
    </p>

    <template v-if="draft">
      <form class="mb-6 flex flex-wrap items-end gap-3" @submit.prevent="save">
        <TextField
          v-model="draft.name"
          :label="$t('meal-plan.saved-plan-name')"
          :disabled="busy"
          maxlength="120"
          class="w-full sm:w-64"
        />
        <Button type="submit" :disabled="busy || !dirty || !draft.name.trim()">
          {{ $t("general.save") }}
        </Button>
      </form>
      <MealPlanBoard
        :key="draft.id ?? 'new'"
        :mealplans="board"
        :actions="actions"
        :inert="busy"
        configurator
      />
    </template>
    <p v-else-if="!busy && !savedPlans.length && !error" class="text-sm text-muted-foreground">
      {{ $t("meal-plan.saved-plan-empty") }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { addDays, format, parseISO } from "date-fns";
import MealPlanBoard from "~/components/Domain/Mealplan/MealPlanBoard.vue";
import { Button } from "~/components/ui/button";
import SelectField from "~/components/ui/field/SelectField.vue";
import TextField from "~/components/ui/field/TextField.vue";
import { useUserApi } from "~/composables/api";
import type { MealBoardActions, MealsByDate } from "~/composables/use-group-mealplan";
import { useHouseholdSelf } from "~/composables/use-households";
import type { PlanEntryOut, SavedMealPlanCreate, SavedMealPlanOut, SavedMealPlanSummary } from "~/lib/api/types/meal-plan";

definePageMeta({ middleware: ["auth"] });

const i18n = useI18n();
useSeoMeta({ title: i18n.t("meal-plan.configurator") });

const { mealplans: api } = useUserApi();
const { household, actions: householdActions } = useHouseholdSelf();
const firstDay = computed(() => household.value?.preferences?.firstDayOfWeek ?? 0);

// The board uses Date values for cell keys and weekday labels. Only weekday numbers go to storage.
const sunday = new Date(2024, 0, 7);
const weekStart = computed(() => addDays(sunday, firstDay.value));
const dateKey = (date: Date) => format(date, "yyyy-MM-dd");

const savedPlans = ref<SavedMealPlanSummary[]>([]);
const draft = ref<{ id: string | null; name: string } | null>(null);
const meals = ref<PlanEntryOut[]>([]);
const busy = ref(false);
const error = ref("");
const status = ref("");
let nextEntryId = 1;
const lastSaved = ref("");

const payload = computed<SavedMealPlanCreate | null>(() => draft.value && ({
  name: draft.value.name,
  entries: meals.value.map(meal => ({
    weekday: meal.endDate ? null : parseISO(meal.date).getDay(),
    entryType: meal.entryType,
    title: meal.title,
    text: meal.text,
    recipeId: meal.recipeId,
    recipeScale: meal.recipeScale,
  })),
}));
const dirty = computed(() => !!payload.value && JSON.stringify(payload.value) !== lastSaved.value);

const board = computed<MealsByDate[]>(() => [
  {
    date: weekStart.value,
    endDate: addDays(weekStart.value, 6),
    meals: meals.value.filter(meal => meal.endDate),
  },
  ...Array.from({ length: 7 }, (_, offset) => {
    const date = addDays(weekStart.value, offset);
    return { date, meals: meals.value.filter(meal => !meal.endDate && meal.date === dateKey(date)) };
  }),
]);

const actions: MealBoardActions = {
  createOne(entry, recipe) {
    meals.value.push({
      ...entry,
      id: nextEntryId++,
      groupId: "",
      userId: "",
      householdId: "",
      title: entry.title ?? "",
      text: entry.text ?? "",
      recipeScale: entry.recipeScale ?? 1,
      entryType: entry.entryType ?? "breakfast",
      endDate: entry.endDate ?? null,
      recipeId: entry.recipeId ?? null,
      recipe: recipe ?? null,
      updatedAt: null,
    });
  },
  updateOne(entry, recipe) {
    meals.value = meals.value.map(meal => meal.id === entry.id
      ? { ...meal, ...entry, recipe: recipe === undefined ? meal.recipe : recipe }
      : meal);
  },
  deleteOne(id) {
    meals.value = meals.value.filter(meal => meal.id !== id);
  },
};

function canLeaveDraft() {
  return !busy.value && (!dirty.value || window.confirm(i18n.t("meal-plan.saved-plan-discard")));
}

onBeforeRouteLeave(canLeaveDraft);

function loadDraft(plan?: SavedMealPlanOut) {
  draft.value = { id: plan?.id ?? null, name: plan?.name ?? "" };
  meals.value = (plan?.entries ?? []).map(entry => ({
    ...entry,
    id: nextEntryId++,
    date: dateKey(entry.weekday === null
      ? weekStart.value
      : addDays(weekStart.value, (entry.weekday - firstDay.value + 7) % 7)),
    endDate: entry.weekday === null ? dateKey(addDays(weekStart.value, 6)) : null,
    groupId: "",
    userId: "",
    householdId: "",
    updatedAt: null,
  }));
  lastSaved.value = JSON.stringify(payload.value);
}

function newPlan() {
  if (canLeaveDraft()) {
    error.value = "";
    status.value = "";
    loadDraft();
  }
}

async function openPlan(id: unknown) {
  if (typeof id !== "string" || id === draft.value?.id || !canLeaveDraft()) return;

  busy.value = true;
  error.value = "";
  status.value = "";
  try {
    const { data } = await api.getSavedPlan(id);
    if (data) loadDraft(data);
    else error.value = i18n.t("meal-plan.saved-plan-load-error");
  }
  finally {
    busy.value = false;
  }
}

async function save() {
  if (!draft.value || !payload.value || busy.value || !dirty.value) return;

  busy.value = true;
  error.value = "";
  status.value = "";
  try {
    const { data } = draft.value.id
      ? await api.updateSavedPlan(draft.value.id, payload.value)
      : await api.createSavedPlan(payload.value);
    if (!data) {
      error.value = i18n.t("meal-plan.saved-plan-save-error");
      return;
    }
    savedPlans.value = [
      ...savedPlans.value.filter(plan => plan.id !== data.id),
      { id: data.id, name: data.name },
    ].sort((a, b) => a.name.localeCompare(b.name));
    loadDraft(data);
    status.value = i18n.t("meal-plan.saved-plan-saved");
  }
  finally {
    busy.value = false;
  }
}

onMounted(async () => {
  busy.value = true;
  try {
    const [{ data }] = await Promise.all([api.getSavedPlans(), householdActions.refresh()]);
    if (data) savedPlans.value = data;
    else error.value = i18n.t("meal-plan.saved-plan-load-error");
  }
  finally {
    busy.value = false;
  }
});
</script>
