<script setup lang="ts">
import type { SortableEvent } from "sortablejs";
import type { MealBoardActions, MealsByDate } from "~/composables/use-group-mealplan";
import type { PlanEntryOut, PlanEntryType } from "~/lib/api/types/meal-plan";
import { EllipsisVerticalIcon, PlusIcon } from "@lucide/vue";
import { useMediaQuery } from "@vueuse/core";
import { endOfDay, format, isToday, isWithinInterval, startOfDay } from "date-fns";
import { VueDraggable } from "vue-draggable-plus";
import GroupMealPlanEntryDialog from "~/components/Domain/Household/GroupMealPlanEntryDialog.vue";
import RecipeDialogAddToShoppingList from "~/components/Domain/Recipe/RecipeDialogAddToShoppingList.vue";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "~/components/ui/dropdown-menu";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { useUserApi } from "~/composables/api";
import { useAddToShoppingListDialog } from "~/composables/shopping-list-page/use-add-to-shopping-list-dialog";
import { getScaledRecipes, usePlanTypeOptions } from "~/composables/use-group-mealplan";
import MealPlanEntryCard from "./MealPlanEntryCard.vue";

/**
 * The meal plan as a board: each week is a row of whole-week entries above a grid of
 * days (columns) by meal types (rows). Meals drag between cells, which moves them to that
 * day and meal type, or onto the week row. Phones get the same plan as a list of days.
 */
const props = defineProps<{
  mealplans: MealsByDate[];
  actions: MealBoardActions;
  configurator?: boolean;
}>();

const api = useUserApi();
const i18n = useI18n();
const planTypeOptions = usePlanTypeOptions();
const isWide = useMediaQuery("(min-width: 1024px)");

interface Block {
  key: string;
  week: MealsByDate | null;
  days: MealsByDate[];
}
const blocks = computed<Block[]>(() => {
  const list: Block[] = [];
  for (const plan of props.mealplans) {
    if (plan.endDate) {
      list.push({ key: `week-${format(plan.date, "yyyy-MM-dd")}`, week: plan, days: [] });
      continue;
    }
    if (!list.length) {
      list.push({ key: `days-${format(plan.date, "yyyy-MM-dd")}`, week: null, days: [] });
    }
    list[list.length - 1]!.days.push(plan);
  }
  return list;
});

// Breakfast, lunch and dinner always have a row; other types appear once a meal uses them.
const CORE: PlanEntryType[] = ["breakfast", "lunch", "dinner"];
function rowsFor(block: Block) {
  const used = new Set(block.days.flatMap(d => d.meals.map(m => m.entryType)));
  return planTypeOptions.filter(o => CORE.includes(o.value) || used.has(o.value));
}
function typeLabel(type: PlanEntryType) {
  return planTypeOptions.find(o => o.value === type)?.text ?? type;
}

// ---- local, draggable copies of each cell
const dateKey = (d: Date) => format(d, "yyyy-MM-dd");
const cellKey = (day: MealsByDate, type: PlanEntryType) => `${dateKey(day.date)}|${type}`;
const weekKey = (week: MealsByDate) => `week|${dateKey(week.date)}`;
const cells = reactive<Record<string, PlanEntryOut[]>>({});
watch(() => props.mealplans, (plans) => {
  const next: Record<string, PlanEntryOut[]> = {};
  for (const plan of plans) {
    if (plan.endDate) {
      next[weekKey(plan)] = [...plan.meals];
      continue;
    }
    for (const option of planTypeOptions) {
      next[cellKey(plan, option.value)] = plan.meals.filter(m => m.entryType === option.value);
    }
  }
  for (const key of Object.keys(cells)) {
    if (!(key in next)) {
      cells[key] = [];
    }
  }
  Object.assign(cells, next);
}, { immediate: true, deep: true });

function onDrop(event: SortableEvent) {
  const id = (event.item as HTMLElement).querySelector("[data-id]")?.getAttribute("data-id") ?? (event.item as HTMLElement).getAttribute("data-id");
  const target = (event.to as HTMLElement).dataset;
  if (!id || event.from === event.to) {
    return;
  }
  const meal = props.mealplans.flatMap(p => p.meals).find(m => String(m.id) === id);
  if (!meal) {
    return;
  }
  props.actions.updateOne({
    ...meal,
    date: target.date!,
    endDate: target.endDate || null,
    entryType: (target.type as PlanEntryType) || meal.entryType,
  });
}

// ---- dialogs and actions
const dialog = reactive({
  open: false,
  entry: null as PlanEntryOut | null,
  date: null as Date | null,
  endDate: null as Date | null,
  entryType: null as PlanEntryType | null,
});
function addMeal(date: Date, entryType: PlanEntryType | null, endDate: Date | null = null) {
  Object.assign(dialog, { entry: null, date, endDate, entryType, open: true });
}
function editMeal(meal: PlanEntryOut) {
  if (!meal.entryType) {
    return;
  }
  Object.assign(dialog, { entry: meal, date: null, endDate: null, entryType: null, open: true });
}

async function randomMeal(date: Date, type: PlanEntryType, endDate: Date | null = null) {
  const { data } = await api.mealplans.setRandom({
    date: dateKey(date),
    endDate: endDate ? dateKey(endDate) : null,
    entryType: type,
  });
  if (data) {
    props.actions.refreshAll?.();
  }
}
/** Replaces a meal with a random one of the same type; the new one is created first so a failure loses nothing. */
async function randomizeMeal(meal: PlanEntryOut) {
  if (!meal.entryType) {
    return;
  }
  const { data: created } = await api.mealplans.setRandom({ date: meal.date, endDate: meal.endDate, entryType: meal.entryType });
  if (created) {
    await api.mealplans.deleteOne(meal.id);
    props.actions.refreshAll?.();
  }
}
/** Moves a week entry onto today, so it counts like any other meal made today. */
function cookToday(meal: PlanEntryOut) {
  props.actions.updateOne({ ...meal, date: dateKey(new Date()), endDate: null });
}

const { shoppingLists, open: listDialog, addAllToList, addShoppingList } = useAddToShoppingListDialog();
const listRecipes = ref<ReturnType<typeof getScaledRecipes>>([]);
function addToList(meals: PlanEntryOut[]) {
  listRecipes.value = getScaledRecipes(meals);
  addAllToList();
}

const randomTypes = computed(() => planTypeOptions.map(o => ({ type: o.value, label: o.text })));
function isCurrentWeek(week: MealsByDate) {
  return !props.configurator && !!week.endDate && isWithinInterval(new Date(), { start: startOfDay(week.date), end: endOfDay(week.endDate) });
}
const dayName = (d: Date) => new Intl.DateTimeFormat(i18n.locale.value, { weekday: "short" }).format(d);
const today = (date: Date) => !props.configurator && isToday(date);
const longDay = (d: Date) => props.configurator ? new Intl.DateTimeFormat(i18n.locale.value, { weekday: "long" }).format(d) : new Intl.DateTimeFormat(i18n.locale.value, { weekday: "long", month: "short", day: "numeric" }).format(d);
// Pointer-driven dragging (not native drag-and-drop) behaves the same with mouse, touch and pen.
const sortableOptions = { group: "meals", animation: 180, delay: 250, delayOnTouchOnly: true, forceFallback: true, fallbackTolerance: 4, ghostClass: "opacity-40", filter: "button, [role=menuitem]", preventOnFilter: false };
</script>

<template>
  <div class="flex flex-col gap-8 font-sans">
    <GroupMealPlanEntryDialog
      v-model="dialog.open"
      :entry="dialog.entry"
      :configurator-week-start="configurator ? blocks[0]?.week?.date : undefined"
      :date="dialog.date"
      :end-date="dialog.endDate"
      :default-entry-type="dialog.entryType"
      @create="(payload, recipe) => actions.createOne(payload, recipe)"
      @update="(payload, recipe) => actions.updateOne(payload, recipe)"
    />
    <RecipeDialogAddToShoppingList
      v-if="!configurator && shoppingLists"
      v-model="listDialog"
      :recipes="listRecipes"
      :shopping-lists="shoppingLists"
      @list-created="addShoppingList"
    />

    <section
      v-for="block in blocks"
      :key="block.key"
      class="flex flex-col gap-3"
    >
      <!-- whole-week entries -->
      <div
        v-if="block.week"
        class="flex flex-wrap items-start gap-3 rounded-card border bg-card px-4 py-3"
        :class="isCurrentWeek(block.week) && 'border-primary/40'"
      >
        <div class="flex min-w-36 flex-col pt-1.5">
          <span class="text-sm font-semibold">{{ configurator ? $t('meal-plan.saved-whole-week') : isCurrentWeek(block.week) ? $t('meal-plan.this-week') : $t('meal-plan.week-of', { date: $d(block.week.date, 'short') }) }}</span>
          <span v-if="!configurator" class="text-xs text-muted-foreground">{{ $d(block.week.date, 'short') }} – {{ $d(block.week.endDate!, 'short') }}</span>
        </div>
        <VueDraggable
          v-model="cells[weekKey(block.week)]!"
          v-bind="sortableOptions"
          :data-date="dateKey(block.week.date)"
          :data-end-date="dateKey(block.week.endDate!)"
          class="flex min-h-10 min-w-0 flex-1 flex-wrap gap-2"
          @end="onDrop"
        >
          <MealPlanEntryCard
            v-for="meal in cells[weekKey(block.week)]"
            :key="meal.id"
            :meal="meal"
            :actions="actions"
            :configurator="configurator"
            layout="row"
            show-type
            class="w-full cursor-grab sm:w-72"
            @edit="editMeal"
            @randomize="randomizeMeal"
            @cook-today="cookToday"
          />
        </VueDraggable>
        <div class="flex items-center gap-1">
          <button
            type="button"
            class="inline-flex h-9 items-center gap-1.5 rounded-control px-2.5 text-sm font-semibold text-primary hover:bg-highlight"
            @click="addMeal(block.week.date, 'dinner', block.week.endDate!)"
          >
            <PlusIcon class="size-4" />
            {{ $t('meal-plan.add-for-the-week') }}
          </button>
          <DropdownMenu v-if="!configurator" :modal="false">
            <DropdownMenuTrigger as-child>
              <button
                type="button"
                class="inline-flex size-9 items-center justify-center rounded-control text-muted-foreground hover:bg-highlight hover:text-foreground"
                :aria-label="$t('general.actions')"
              >
                <EllipsisVerticalIcon class="size-4" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              align="end"
              class="min-w-56"
            >
              <DropdownMenuItem
                :disabled="!block.week.meals.some(m => m.recipe)"
                @select="addToList(block.week!.meals)"
              >
                <MdiIcon
                  :path="$globals.icons.cartCheck"
                  class="size-4"
                />
                {{ $t('meal-plan.add-week-to-list') }}
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuLabel class="text-xs text-muted-foreground">
                {{ $t('meal-plan.random-meal') }}
              </DropdownMenuLabel>
              <DropdownMenuItem
                v-for="option in randomTypes"
                :key="option.type"
                @select="randomMeal(block.week!.date, option.type, block.week!.endDate!)"
              >
                <MdiIcon
                  :path="$globals.icons.diceMultiple"
                  class="size-4"
                />
                {{ option.label }}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      <!-- desktop: days by meal types -->
      <div
        v-if="isWide && block.days.length"
        class="overflow-x-auto rounded-card border bg-card"
      >
        <div
          class="grid"
          :style="{ gridTemplateColumns: `6rem repeat(${block.days.length}, minmax(8.5rem, 1fr))` }"
        >
          <span class="border-b" />
          <div
            v-for="day in block.days"
            :key="dateKey(day.date)"
            class="group/day flex items-start justify-between gap-1 border-b border-s px-3 py-2.5"
            :class="today(day.date) && 'bg-highlight text-highlight-foreground'"
          >
            <div class="flex flex-col">
              <span class="text-[13px] text-muted-foreground">{{ today(day.date) ? $t('meal-plan.today') : dayName(day.date) }}</span>
              <span v-if="!configurator" class="text-xl font-bold leading-tight">{{ day.date.getDate() }}</span>
            </div>
            <DropdownMenu v-if="!configurator" :modal="false">
              <DropdownMenuTrigger as-child>
                <button
                  type="button"
                  class="inline-flex size-8 items-center justify-center rounded-control text-muted-foreground opacity-0 transition-opacity hover:bg-highlight hover:text-foreground focus-visible:opacity-100 group-hover/day:opacity-100 data-[state=open]:opacity-100"
                  :aria-label="`${$t('general.actions')}: ${longDay(day.date)}`"
                >
                  <EllipsisVerticalIcon class="size-4" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                align="end"
                class="min-w-56"
              >
                <DropdownMenuItem
                  :disabled="!day.meals.some(m => m.recipe)"
                  @select="addToList(day.meals)"
                >
                  <MdiIcon
                    :path="$globals.icons.cartCheck"
                    class="size-4"
                  />
                  {{ $t('meal-plan.add-day-to-list') }}
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuLabel class="text-xs text-muted-foreground">
                  {{ $t('meal-plan.random-meal') }}
                </DropdownMenuLabel>
                <DropdownMenuItem
                  v-for="option in randomTypes"
                  :key="option.type"
                  @select="randomMeal(day.date, option.type)"
                >
                  <MdiIcon
                    :path="$globals.icons.diceMultiple"
                    class="size-4"
                  />
                  {{ option.label }}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          <template
            v-for="row in rowsFor(block)"
            :key="row.value"
          >
            <div class="border-b px-3 py-3 text-sm font-semibold text-muted-foreground">
              {{ row.text }}
            </div>
            <div
              v-for="day in block.days"
              :key="cellKey(day, row.value)"
              class="group/cell flex min-w-0 flex-col gap-1.5 border-b border-s p-1.5"
              :class="today(day.date) && 'bg-highlight/30'"
            >
              <VueDraggable
                v-model="cells[cellKey(day, row.value)]!"
                v-bind="sortableOptions"
                :data-date="dateKey(day.date)"
                :data-type="row.value"
                class="flex min-h-2 flex-col gap-1.5"
                @end="onDrop"
              >
                <MealPlanEntryCard
                  v-for="meal in cells[cellKey(day, row.value)]"
                  :key="meal.id"
                  :meal="meal"
                  :actions="actions"
                  :configurator="configurator"
                  class="cursor-grab"
                  @edit="editMeal"
                  @randomize="randomizeMeal"
                  @cook-today="cookToday"
                />
              </VueDraggable>
              <button
                type="button"
                class="flex w-full items-center justify-center rounded-control border border-dashed text-muted-foreground transition-colors hover:border-primary/50 hover:bg-highlight/50 hover:text-primary"
                :class="cells[cellKey(day, row.value)]?.length ? 'h-7 border-transparent opacity-0 focus-visible:opacity-100 group-hover/cell:opacity-100 [@media(hover:none)]:opacity-100' : 'h-11'"
                :aria-label="$t('meal-plan.add-meal-type-on-day', { type: row.text, day: longDay(day.date) })"
                @click="addMeal(day.date, row.value)"
              >
                <PlusIcon class="size-4" />
              </button>
            </div>
          </template>
        </div>
      </div>

      <!-- phones and tablets: a list of days -->
      <div
        v-else-if="block.days.length"
        class="flex flex-col gap-3"
      >
        <article
          v-for="day in block.days"
          :key="dateKey(day.date)"
          class="rounded-card border bg-card"
          :class="today(day.date) && 'border-primary/40'"
        >
          <header class="flex items-center gap-2 border-b px-4 py-2.5">
            <h3
              class="m-0 flex-1 text-[15px] font-semibold"
              :class="today(day.date) && 'text-primary'"
            >
              {{ today(day.date) ? `${$t('meal-plan.today')} · ` : '' }}{{ longDay(day.date) }}
            </h3>
            <button
              type="button"
              class="inline-flex h-9 items-center gap-1 rounded-control px-2 text-sm font-semibold text-primary hover:bg-highlight"
              @click="addMeal(day.date, 'dinner')"
            >
              <PlusIcon class="size-4" />
              {{ $t('general.add') }}
            </button>
            <DropdownMenu v-if="!configurator" :modal="false">
              <DropdownMenuTrigger as-child>
                <button
                  type="button"
                  class="inline-flex size-9 items-center justify-center rounded-control text-muted-foreground hover:bg-highlight"
                  :aria-label="`${$t('general.actions')}: ${longDay(day.date)}`"
                >
                  <EllipsisVerticalIcon class="size-4" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                align="end"
                class="min-w-56"
              >
                <DropdownMenuItem
                  :disabled="!day.meals.some(m => m.recipe)"
                  @select="addToList(day.meals)"
                >
                  <MdiIcon
                    :path="$globals.icons.cartCheck"
                    class="size-4"
                  />
                  {{ $t('meal-plan.add-day-to-list') }}
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuLabel class="text-xs text-muted-foreground">
                  {{ $t('meal-plan.random-meal') }}
                </DropdownMenuLabel>
                <DropdownMenuItem
                  v-for="option in randomTypes"
                  :key="option.type"
                  @select="randomMeal(day.date, option.type)"
                >
                  <MdiIcon
                    :path="$globals.icons.diceMultiple"
                    class="size-4"
                  />
                  {{ option.label }}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </header>
          <div class="flex flex-col gap-3 p-3">
            <p
              v-if="!day.meals.length"
              class="m-0 px-1 text-sm text-muted-foreground"
            >
              {{ $t('meal-plan.nothing-planned') }}
            </p>
            <template
              v-for="option in planTypeOptions"
              :key="option.value"
            >
              <div v-if="cells[cellKey(day, option.value)]?.length">
                <div class="mb-1.5 px-1 text-xs font-semibold text-muted-foreground">
                  {{ typeLabel(option.value) }}
                </div>
                <VueDraggable
                  v-model="cells[cellKey(day, option.value)]!"
                  v-bind="sortableOptions"
                  :data-date="dateKey(day.date)"
                  :data-type="option.value"
                  class="flex flex-col gap-2"
                  @end="onDrop"
                >
                  <MealPlanEntryCard
                    v-for="meal in cells[cellKey(day, option.value)]"
                    :key="meal.id"
                    :meal="meal"
                    :actions="actions"
                    :configurator="configurator"
                    layout="row"
                    @edit="editMeal"
                    @randomize="randomizeMeal"
                    @cook-today="cookToday"
                  />
                </VueDraggable>
              </div>
            </template>
          </div>
        </article>
      </div>
    </section>

    <p
      v-if="isWide"
      class="m-0 text-sm text-muted-foreground"
    >
      {{ $t('meal-plan.board-hint') }}
    </p>
  </div>
</template>
