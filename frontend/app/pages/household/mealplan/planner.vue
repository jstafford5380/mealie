<template>
  <div class="mx-auto w-full max-w-[1440px] px-4 pb-16 pt-4 font-sans sm:px-6 lg:px-8 lg:pt-8">
    <RecipeDialogAddToShoppingList
      v-if="shoppingLists"
      v-model="shoppingListDialog"
      :recipes="weekRecipesWithScales"
      :shopping-lists="shoppingLists"
      @list-created="addShoppingList"
    />
    <GroupMealPlanCalendarDialog v-model="calendarDialog" />

    <div class="mb-6 flex flex-wrap items-center gap-x-4 gap-y-3">
      <h1 class="m-0 text-[28px] font-bold tracking-tight sm:text-[32px]">
        {{ $t("meal-plan.meal-planner") }}
      </h1>
      <div class="flex w-full min-w-0 items-center gap-1 sm:w-auto">
        <Button
          variant="outline"
          size="icon"
          class="shrink-0"
          :aria-label="$t('meal-plan.previous-range')"
          :title="$t('meal-plan.previous-range')"
          @click="changeWeek(-1)"
        >
          <ChevronLeftIcon class="size-4" />
        </Button>
        <Popover v-model:open="state.picker">
          <PopoverTrigger as-child>
            <Button
              variant="outline"
              class="min-w-0 flex-1 sm:flex-none"
              :aria-label="`${$t('meal-plan.choose-range')}: ${$d(visibleRange.start, 'short')} – ${$d(visibleRange.end, 'short')}`"
            >
              <MdiIcon
                :path="$globals.icons.calendar"
                class="size-4"
              />
              <span class="truncate">{{ rangeLabel }}</span>
            </Button>
          </PopoverTrigger>
          <PopoverContent
            align="start"
            class="flex w-[min(22rem,calc(100vw-2rem))] flex-col gap-4"
          >
            <MealPlanDatePicker
              v-model="pickerRange"
              multiple="range"
            />
            <div class="grid grid-cols-2 gap-3 border-t pt-3">
              <template v-if="isDaysMode">
                <NumberInputField
                  v-model="numberOfDaysPast"
                  :min="0"
                  :label="$t('meal-plan.numberOfDaysPast-label')"
                  :hint="$t('meal-plan.numberOfDaysPast-hint')"
                />
                <NumberInputField
                  v-model="numberOfDays"
                  :min="1"
                  :label="$t('meal-plan.numberOfDays-label')"
                  :hint="$t('meal-plan.numberOfDays-hint')"
                />
              </template>
              <template v-else>
                <NumberInputField
                  v-model="numberOfWeeksPast"
                  :min="0"
                  :label="$t('meal-plan.numberOfWeeksPast-label')"
                  :hint="$t('meal-plan.numberOfWeeksPast-hint')"
                />
                <NumberInputField
                  v-model="numberOfWeeks"
                  :min="1"
                  :label="$t('meal-plan.numberOfWeeks-label')"
                  :hint="$t('meal-plan.numberOfWeeks-hint')"
                />
              </template>
            </div>
          </PopoverContent>
        </Popover>
        <Button
          variant="outline"
          size="icon"
          class="shrink-0"
          :aria-label="$t('meal-plan.next-range')"
          :title="$t('meal-plan.next-range')"
          @click="changeWeek(1)"
        >
          <ChevronRightIcon class="size-4" />
        </Button>
        <Button
          variant="ghost"
          class="shrink-0 text-primary"
          @click="goToToday"
        >
          {{ $t("meal-plan.today") }}
        </Button>
      </div>

      <div class="ms-auto flex flex-wrap items-center gap-2">
        <div
          role="radiogroup"
          :aria-label="$t('meal-plan.range-mode')"
          class="inline-flex rounded-control bg-muted p-1 text-sm"
        >
          <button
            v-for="mode in modeOptions"
            :key="mode.value"
            type="button"
            role="radio"
            :aria-checked="mealPlanPreferences.mode === mode.value"
            :title="mode.value === 'weeks' && hiddenWeekMealCount > 0 ? $t('meal-plan.week-meals-hidden', hiddenWeekMealCount) : undefined"
            class="inline-flex h-8 items-center gap-1.5 rounded-item px-3 font-semibold transition-colors"
            :class="mealPlanPreferences.mode === mode.value ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'"
            @click="mealPlanPreferences.mode = mode.value"
          >
            {{ mode.label }}
            <span
              v-if="mode.value === 'weeks' && hiddenWeekMealCount > 0"
              class="inline-flex min-w-5 items-center justify-center rounded-full bg-primary px-1.5 text-[11px] font-bold text-primary-foreground"
            >{{ hiddenWeekMealCount }}<span class="sr-only">: {{ $t('meal-plan.week-meals-hidden', hiddenWeekMealCount) }}</span></span>
          </button>
        </div>
        <Button
          :disabled="!hasRecipes"
          @click="addAllToList"
        >
          <MdiIcon
            :path="$globals.icons.cartCheck"
            class="size-4"
          />
          <span class="max-sm:sr-only">{{ $t("meal-plan.add-all-to-list") }}</span>
        </Button>
        <DropdownMenu :modal="false">
          <DropdownMenuTrigger as-child>
            <Button
              variant="ghost"
              size="icon"
              :aria-label="$t('general.more')"
            >
              <EllipsisVerticalIcon class="size-5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            align="end"
            class="min-w-52"
          >
            <DropdownMenuItem @select="calendarDialog = true">
              <MdiIcon
                :path="$globals.icons.calendar"
                class="size-4"
              />
              {{ $t("meal-plan.calendar-feed") }}
            </DropdownMenuItem>
            <DropdownMenuItem @select="router.push('/household/mealplan/settings')">
              <MdiIcon
                :path="$globals.icons.cog"
                class="size-4"
              />
              {{ $t("general.settings") }}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>

    <NuxtPage
      :mealplans="plans"
      :actions="actions"
    />
  </div>
</template>

<script setup lang="ts">
import { addDays, addWeeks, differenceInCalendarDays, format, isSameDay, isValid, parseISO } from "date-fns";
import { ChevronLeftIcon, ChevronRightIcon, EllipsisVerticalIcon } from "@lucide/vue";
import GroupMealPlanCalendarDialog from "~/components/Domain/Household/GroupMealPlanCalendarDialog.vue";
import { Button } from "~/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "~/components/ui/dropdown-menu";
import NumberInputField from "~/components/ui/field/NumberInputField.vue";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { Popover, PopoverContent, PopoverTrigger } from "~/components/ui/popover";
import RecipeDialogAddToShoppingList from "~/components/Domain/Recipe/RecipeDialogAddToShoppingList.vue";
import { useAddToShoppingListDialog } from "~/composables/shopping-list-page/use-add-to-shopping-list-dialog";
import type { MealsByDate } from "~/composables/use-group-mealplan";
import { getScaledRecipes, getWeekRange, useMealplans } from "~/composables/use-group-mealplan";
import { useHouseholdSelf } from "~/composables/use-households";
import { useUserMealPlanPreferences } from "~/composables/use-users/preferences";

definePageMeta({
  middleware: ["auth"],
});

const TABS = {
  view: "household-mealplan-planner-view",
  edit: "household-mealplan-planner-edit",
};

const route = useRoute();
const router = useRouter();
const i18n = useI18n();
const { household, actions: householdActions } = useHouseholdSelf();
const { shoppingLists, open: shoppingListDialog, addAllToList, addShoppingList } = useAddToShoppingListDialog();
const calendarDialog = ref(false);

useSeoMeta({
  title: i18n.t("meal-plan.dinner-this-week"),
});

// useHouseholdSelf() caches data in a module-level singleton for the lifetime of the tab,
// so revisiting this page via client-side navigation can otherwise use a stale
// firstDayOfWeek value if household preferences were changed elsewhere (e.g. Admin
// Households panel) in the same session. Force a revalidation whenever this page is entered.
onMounted(() => {
  householdActions.refresh();
});

const mealPlanPreferences = useUserMealPlanPreferences();
const isDaysMode = computed(() => mealPlanPreferences.value.mode === "days");
const numberOfDaysPast = ref<number>(mealPlanPreferences.value.numberOfDaysPast || 0);
const numberOfDays = ref<number>(mealPlanPreferences.value.numberOfDays || 7);
watch(numberOfDaysPast, (val) => {
  mealPlanPreferences.value.numberOfDaysPast = Number(val);
});
watch(numberOfDays, (val) => {
  mealPlanPreferences.value.numberOfDays = Number(val);
});
const numberOfWeeksPast = ref<number>(mealPlanPreferences.value.numberOfWeeksPast || 0);
const numberOfWeeks = ref<number>(mealPlanPreferences.value.numberOfWeeks || 1);
watch(numberOfWeeksPast, (val) => {
  mealPlanPreferences.value.numberOfWeeksPast = Number(val);
});
watch(numberOfWeeks, (val) => {
  mealPlanPreferences.value.numberOfWeeks = Number(val);
});

// Force to /view if current route is /planner
if (route.path === "/household/mealplan/planner") {
  router.push({
    name: TABS.view,
    query: route.query,
  });
}

function safeParseISO(date: string, fallback: Date | undefined = undefined) {
  try {
    const parsed = parseISO(date);
    return isValid(parsed) ? parsed : fallback;
  }
  catch {
    return fallback;
  }
}

// In weeks mode these are a day in the first and last week of the default range; `visibleRange` rounds them out to whole weeks
function defaultStartDate() {
  return isDaysMode.value
    ? addDays(new Date(), -numberOfDaysPast.value)
    : addWeeks(new Date(), -numberOfWeeksPast.value);
}

function defaultEndDate() {
  return isDaysMode.value
    ? addDays(new Date(), numberOfDays.value - 1)
    : addWeeks(new Date(), numberOfWeeks.value - 1);
}

// Initialize dates from query parameters or defaults
const initialStartDate = safeParseISO(route.query.start as string, defaultStartDate());
const initialEndDate = safeParseISO(route.query.end as string, defaultEndDate());

const state = ref({
  range: [initialStartDate, initialEndDate] as [Date, Date],
  start: initialStartDate,
  picker: false,
  end: initialEndDate,
});

const firstDayOfWeek = computed(() => {
  return household.value?.preferences?.firstDayOfWeek || 0;
});

const modeOptions = computed(() => [
  { value: "weeks" as const, label: i18n.t("meal-plan.weeks") },
  { value: "days" as const, label: i18n.t("meal-plan.days") },
]);

/** The picker picks one day per click: the first click starts a range, the second finishes it. */
const pickerRange = computed<Date | [Date, Date]>({
  get: () => {
    const [first, last] = state.value.range;
    return state.value.range.length === 2 && first && last ? [first, last].sort((a, b) => a.getTime() - b.getTime()) as [Date, Date] : first!;
  },
  set: (value) => {
    const day = Array.isArray(value) ? value[0] : value;
    if (!day) {
      return;
    }
    if (state.value.range.length === 1) {
      state.value.range = [state.value.range[0]!, day].sort((a, b) => a.getTime() - b.getTime()) as [Date, Date];
    }
    else {
      state.value.range = [day] as unknown as [Date, Date];
    }
  },
});

const rangeLabel = computed(() => {
  const fmt = new Intl.DateTimeFormat(i18n.locale.value, { month: "short", day: "numeric" });
  return `${fmt.format(visibleRange.value.start)} – ${fmt.format(visibleRange.value.end)}`;
});

function goToToday() {
  state.value.range = [defaultStartDate(), defaultEndDate()];
}

function changeWeek(step: number) {
  const { start, end } = visibleRange.value;
  const stepSize = differenceInCalendarDays(end, start) + 1;
  state.value.range = [
    addDays(start, step * stepSize),
    addDays(end, step * stepSize),
  ];
}

watch(isDaysMode, () => {
  state.value.range = [defaultStartDate(), defaultEndDate()];
});

// In weeks mode the planner shows whole weeks, so the selected range is rounded out to the weeks it touches
const visibleRange = computed(() => {
  const sorted = [...state.value.range].sort((a, b) => a.getTime() - b.getTime());

  const start = sorted[0] ?? defaultStartDate();
  const end = sorted[sorted.length - 1] ?? defaultEndDate();

  if (isDaysMode.value) {
    return { start, end };
  }

  return {
    start: getWeekRange(start, firstDayOfWeek.value).start,
    end: getWeekRange(end, firstDayOfWeek.value).end,
  };
});

// Once a range is fully picked, show the whole weeks in the picker too. A half-picked range (one date)
// is left alone, so the picker can still take the second click.
watch(visibleRange, ({ start, end }) => {
  if (isDaysMode.value) return;

  const [first, last] = state.value.range;
  if (state.value.range.length === 2 && !(first && last && isSameDay(first, start) && isSameDay(last, end))) {
    state.value.range = [start, end];
  }
});

// Update query parameters when date range changes
watch(visibleRange, (newRange) => {
  // Keep current route name and params, just update the query
  router.replace({
    name: route.name || TABS.view,
    params: route.params,
    query: {
      ...route.query,
      start: format(newRange.start, "yyyy-MM-dd"),
      end: format(newRange.end, "yyyy-MM-dd"),
    },
  });
}, { immediate: true });

const { mealplans, actions } = useMealplans(visibleRange);

function filterMealByDate(date: Date) {
  if (!mealplans.value) return [];
  return mealplans.value.filter((meal) => {
    // week entries aren't planned for a specific day
    if (meal.endDate) return false;

    const mealDate = parseISO(meal.date);
    return isSameDay(mealDate, date);
  });
}

const days = computed(() => {
  const numDays
    = Math.floor((visibleRange.value.end.getTime() - visibleRange.value.start.getTime()) / (1000 * 60 * 60 * 24)) + 1;

  // Calculate absolute value
  if (numDays < 0) return [];

  return Array.from(Array(numDays).keys()).map(
    (i) => {
      const date = new Date(visibleRange.value.start.getTime());
      date.setDate(date.getDate() + i);
      return date;
    },
  );
});

const mealsByDate = computed(() => {
  return days.value.map((day) => {
    return { date: day, meals: filterMealByDate(day) };
  });
});

/**
 * The visible days grouped by week, each with that week's entries, so meals can be planned for any visible week.
 * Week entries are grouped by their own dates rather than the current weeks, so they still show up (as a week
 * without days) if the household's first day of the week has changed since they were planned.
 */
const mealsByWeek = computed(() => {
  const weeks = new Map<string, { week: MealsByDate; days: MealsByDate[] }>();
  const getWeek = (start: Date, end: Date) => {
    const key = format(start, "yyyy-MM-dd");
    if (!weeks.has(key)) {
      weeks.set(key, { week: { date: start, endDate: end, meals: [] }, days: [] });
    }
    return weeks.get(key)!;
  };

  for (const day of mealsByDate.value) {
    const { start, end } = getWeekRange(day.date, firstDayOfWeek.value);
    getWeek(start, end).days.push(day);
  }

  for (const meal of mealplans.value ?? []) {
    if (meal.endDate) {
      getWeek(parseISO(meal.date), parseISO(meal.endDate)).week.meals.push(meal);
    }
  }

  return [...weeks.values()].sort((a, b) => a.week.date.getTime() - b.week.date.getTime());
});

/** Each week followed by its days, the order the planner pages lay them out in. Days mode leaves out the weeks. */
const plans = computed(() => isDaysMode.value
  ? mealsByDate.value
  : mealsByWeek.value.flatMap(({ week, days }) => [week, ...days]));

const hiddenWeekMealCount = computed(() => isDaysMode.value
  ? (mealplans.value ?? []).filter(meal => meal.endDate).length
  : 0);

const allMeals = computed(() => plans.value.flatMap(({ meals }) => meals));

const hasRecipes = computed(() => {
  return allMeals.value.some(meal => meal.recipe);
});

const weekRecipesWithScales = computed(() => {
  return getScaledRecipes(allMeals.value);
});
</script>
