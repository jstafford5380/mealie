<script setup lang="ts">
import { format, parseISO } from "date-fns";
import type { PlanEntryOut } from "~/lib/api/types/meal-plan";
import RecipeThumb from "~/components/Domain/Recipe/RecipeThumb.vue";
import { getAvailableLeftovers, getBatchBalance, leftoverDragType, type MealBatch } from "~/composables/use-mealplan-batches";

const props = defineProps<{
  days: Date[];
  batches: MealBatch[];
  unlinked: PlanEntryOut[];
  configurator?: boolean;
  selectedBatchId?: string | null;
}>();
const emit = defineEmits<{
  selectBatch: [id: string];
  dragBatch: [id: string | null];
}>();
const i18n = useI18n();
const headingId = useId();
const dates = computed(() => props.days.map(date => ({ date, key: format(date, "yyyy-MM-dd") })));
const rows = computed(() => props.batches.flatMap((batch) => {
  const available = getAvailableLeftovers(batch);
  if (available <= 0) return [];

  const cells = dates.value.map(({ key }) => ({
    key,
    balance: key < batch.source.date ? null : getBatchBalance(batch, key),
  }));
  return cells.some(cell => cell.balance !== null && cell.balance !== 0)
    ? [{ batch, cells }]
    : [];
}));
const hasUnlinked = computed(() => props.unlinked.some(entry => dates.value.some(day => day.key === entry.date)));
const hasShortage = computed(() => props.batches.some(batch =>
  dates.value.some(({ key }) => key >= batch.source.date && getBatchBalance(batch, key) < 0),
));
const shortDay = (date: Date) => new Intl.DateTimeFormat(i18n.locale.value, {
  weekday: "short",
  ...(props.configurator ? {} : { month: "short", day: "numeric" }),
}).format(date);

function startDrag(event: DragEvent, id: string) {
  if (!event.dataTransfer) return;
  event.dataTransfer.setData(leftoverDragType, id);
  event.dataTransfer.effectAllowed = "copy";
  emit("dragBatch", id);
}
</script>

<template>
  <section :aria-labelledby="headingId" class="flex flex-col gap-2">
    <h2 :id="headingId" class="m-0 text-lg font-semibold">
      {{ $t("meal-plan.projected-leftovers") }}
    </h2>
    <p v-if="rows.length" class="m-0 text-sm text-muted-foreground">
      {{ $t("meal-plan.drag-leftovers-hint") }}
    </p>
    <p v-if="hasUnlinked" role="status" class="m-0 text-sm text-destructive">
      {{ $t("meal-plan.unlinked-leftovers") }}
    </p>
    <p v-if="hasShortage" role="status" class="m-0 text-sm text-destructive">
      {{ $t("meal-plan.leftovers-overbooked") }}
    </p>
    <p v-if="!rows.length" class="m-0 text-sm text-muted-foreground">
      {{ $t("meal-plan.no-projected-leftovers") }}
    </p>
    <div v-else class="overflow-x-auto rounded-card border bg-card">
      <table class="w-full border-collapse text-start text-sm">
        <caption class="sr-only">
          {{ $t("meal-plan.leftover-servings-by-day") }}
        </caption>
        <thead>
          <tr class="border-b">
            <th scope="col" class="min-w-52 px-3 py-2 text-start">
              {{ $t("meal-plan.leftover-batch") }}
            </th>
            <th v-for="day in dates" :key="day.key" scope="col" class="min-w-20 whitespace-nowrap border-s px-3 py-2 text-start">
              {{ shortDay(day.date) }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="{ batch, cells } in rows" :key="batch.id" class="border-b last:border-b-0">
            <th scope="row" class="px-3 py-2 text-start">
              <button
                type="button"
                draggable="true"
                :aria-pressed="selectedBatchId === batch.id"
                class="flex w-full cursor-grab items-center gap-2 rounded-control border bg-background p-1.5 text-start hover:bg-highlight aria-pressed:border-primary aria-pressed:bg-highlight active:cursor-grabbing"
                @dragstart="startDrag($event, batch.id)"
                @dragend="emit('dragBatch', null)"
                @click="emit('selectBatch', batch.id)"
              >
                <RecipeThumb
                  :recipe-id="batch.source.recipe?.id"
                  :image="batch.source.recipe?.image"
                  class="pointer-events-none h-10 w-12 rounded-item"
                />
                <span class="min-w-0">
                  <span class="block text-xs font-semibold leading-tight">{{ batch.source.recipe?.name }}</span>
                  <span class="mt-0.5 block text-xs font-normal text-muted-foreground">
                    {{ shortDay(parseISO(batch.source.date)) }} · {{ $t(`meal-plan.${batch.source.entryType}`) }}
                  </span>
                </span>
              </button>
            </th>
            <td
              v-for="{ key, balance } in cells"
              :key="key"
              class="whitespace-nowrap border-s px-3 py-2 tabular-nums"
              :class="balance === null && 'text-muted-foreground'"
            >
              {{ balance === null ? '—' : $n(balance, { maximumFractionDigits: 2 }) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
