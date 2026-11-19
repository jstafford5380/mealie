<script setup lang="ts">
import type { PlanEntryType } from "~/lib/api/types/meal-plan";
import { ChevronLeftIcon, ChevronRightIcon } from "@lucide/vue";
import {
  addDays,
  addMonths,
  endOfMonth,
  format,
  isAfter,
  isBefore,
  isSameDay,
  isSameMonth,
  isToday,
  startOfDay,
  startOfMonth,
} from "date-fns";

/**
 * Month calendar for choosing a meal-plan day. Days that already have meals show a dot:
 * filled for the chosen meal type, muted for other types. A week entry shows as a range.
 */
const selectedDate = defineModel<Date | [Date, Date]>();
const props = defineProps<{
  entryType?: PlanEntryType;
  /** "range" when the model is a [start, end] pair; clicking still picks one day. */
  multiple?: "range" | false;
}>();

const { household } = useHouseholdSelf();
const { locale } = useI18n();

const firstDayOfWeek = computed(() => household.value?.preferences?.firstDayOfWeek || 0);

const anchor = computed(() => (Array.isArray(selectedDate.value) ? selectedDate.value[0] : selectedDate.value) ?? new Date());
const month = ref(startOfMonth(anchor.value));
watch(anchor, (value) => {
  if (value && !isSameMonth(value, month.value)) {
    month.value = startOfMonth(value);
  }
});

const range = computed(() => ({ start: addMonths(month.value, -1), end: addMonths(month.value, 2) }));
const { mealplans } = useMealplans(range);

const monthLabel = computed(() => new Intl.DateTimeFormat(locale.value, { month: "long", year: "numeric" }).format(month.value));
const weekdays = computed(() => {
  const fmt = new Intl.DateTimeFormat(locale.value, { weekday: "short" });
  const long = new Intl.DateTimeFormat(locale.value, { weekday: "long" });
  // 2023-01-01 was a Sunday
  return Array.from({ length: 7 }, (_, i) => {
    const day = new Date(2023, 0, 1 + ((i + firstDayOfWeek.value) % 7));
    return { short: fmt.format(day), long: long.format(day) };
  });
});

const days = computed(() => {
  const first = startOfMonth(month.value);
  const offset = (first.getDay() - firstDayOfWeek.value + 7) % 7;
  const start = addDays(first, -offset);
  const weeks = Math.ceil((offset + endOfMonth(month.value).getDate()) / 7);
  return Array.from({ length: weeks * 7 }, (_, i) => addDays(start, i));
});

const selection = computed<[Date, Date] | null>(() => {
  const value = selectedDate.value;
  if (!value) {
    return null;
  }
  return Array.isArray(value) ? [startOfDay(value[0]), startOfDay(value[1])] : [startOfDay(value), startOfDay(value)];
});
function isSelected(day: Date) {
  const sel = selection.value;
  return !!sel && !isBefore(day, sel[0]) && !isAfter(day, sel[1]);
}
function isEdge(day: Date) {
  const sel = selection.value;
  return !!sel && (isSameDay(day, sel[0]) || isSameDay(day, sel[1]));
}

const planned = computed(() => {
  const byDay: Record<string, { match: boolean }> = {};
  for (const meal of mealplans.value ?? []) {
    // ranged entries (a whole week) aren't on one day
    if (meal.endDate || !meal.date) {
      continue;
    }
    const match = !props.entryType || meal.entryType === props.entryType;
    byDay[meal.date] = { match: (byDay[meal.date]?.match ?? false) || match };
  }
  return byDay;
});
const dayKey = (day: Date) => format(day, "yyyy-MM-dd");

function pick(day: Date) {
  selectedDate.value = day;
  if (!isSameMonth(day, month.value)) {
    month.value = startOfMonth(day);
  }
}

// Arrow keys move between days (and months); Enter/Space picks.
const grid = ref<HTMLElement>();
const focusDay = ref<Date>(anchor.value);
function onKey(event: KeyboardEvent) {
  const step: Record<string, number> = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7 };
  const delta = step[event.key];
  if (delta === undefined) {
    return;
  }
  event.preventDefault();
  const next = addDays(focusDay.value, delta);
  focusDay.value = next;
  if (!isSameMonth(next, month.value)) {
    month.value = startOfMonth(next);
  }
  nextTick(() => grid.value?.querySelector<HTMLElement>(`[data-day="${dayKey(next)}"]`)?.focus());
}
watch(anchor, (value) => {
  focusDay.value = value;
});
</script>

<template>
  <div class="mx-auto w-full max-w-sm font-sans">
    <div class="mb-2 flex items-center justify-between">
      <button
        type="button"
        class="inline-flex size-9 items-center justify-center rounded-full text-muted-foreground hover:bg-highlight hover:text-foreground"
        :aria-label="$t('general.previous')"
        @click="month = addMonths(month, -1)"
      >
        <ChevronLeftIcon class="size-5" />
      </button>
      <div
        class="text-[15px] font-semibold capitalize"
        aria-live="polite"
      >
        {{ monthLabel }}
      </div>
      <button
        type="button"
        class="inline-flex size-9 items-center justify-center rounded-full text-muted-foreground hover:bg-highlight hover:text-foreground"
        :aria-label="$t('general.next')"
        @click="month = addMonths(month, 1)"
      >
        <ChevronRightIcon class="size-5" />
      </button>
    </div>
    <div
      class="grid grid-cols-7 text-center text-xs font-semibold text-muted-foreground"
      aria-hidden="true"
    >
      <span
        v-for="day in weekdays"
        :key="day.long"
        class="py-1"
      >{{ day.short }}</span>
    </div>
    <div
      ref="grid"
      role="grid"
      :aria-label="monthLabel"
      class="grid grid-cols-7 gap-y-1"
      @keydown="onKey"
    >
      <button
        v-for="day in days"
        :key="dayKey(day)"
        type="button"
        role="gridcell"
        :data-day="dayKey(day)"
        :tabindex="isSameDay(day, focusDay) ? 0 : -1"
        :aria-selected="isSelected(day)"
        :aria-label="new Intl.DateTimeFormat($i18n.locale, { dateStyle: 'full' }).format(day)"
        class="relative mx-auto flex h-10 w-full flex-col items-center justify-center text-sm transition-colors focus-visible:z-10 focus-visible:outline-2 focus-visible:outline-ring"
        :class="[
          isSelected(day) && !isEdge(day) && 'bg-highlight text-highlight-foreground',
          isSelected(day) && multiple === 'range' && isSameDay(day, selection![0]) && 'rounded-s-full',
          isSelected(day) && multiple === 'range' && isSameDay(day, selection![1]) && 'rounded-e-full',
          isSelected(day) && multiple === 'range' && 'bg-highlight',
          !isSameMonth(day, month) && 'text-muted-foreground/60',
        ]"
        @click="pick(day); focusDay = day"
      >
        <span
          class="flex size-9 items-center justify-center rounded-full"
          :class="[
            isEdge(day) ? 'bg-primary font-semibold text-primary-foreground' : 'hover:bg-highlight',
            isToday(day) && !isEdge(day) && 'ring-1 ring-primary',
          ]"
        >{{ day.getDate() }}</span>
        <span
          v-if="planned[dayKey(day)]"
          class="absolute bottom-0.5 size-1.5 rounded-full"
          :class="planned[dayKey(day)]!.match ? (isEdge(day) ? 'bg-brand' : 'bg-primary') : 'bg-muted-foreground/50'"
          aria-hidden="true"
        />
      </button>
    </div>
  </div>
</template>
