<template>
  <BaseDialog
    v-model="dialog"
    :title="entry ? $t('meal-plan.edit-meal') : $t('meal-plan.add-meal')"
    :submit-text="entry ? $t('general.save') : $t('general.add')"
    :icon="$globals.icons.foods"
    :submit-disabled="submitDisabled"
    width="1000"
    can-submit
    disable-submit-on-enter
    @submit="submit"
  >
    <div class="grid gap-6 px-6 pb-2 font-sans md:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
      <div class="flex flex-col gap-4">
        <div
          role="radiogroup"
          :aria-label="$t('meal-plan.entry-kind')"
          class="grid grid-cols-2 rounded-control bg-muted p-1"
        >
          <button
            v-for="mode in modes"
            :key="mode.value"
            type="button"
            role="radio"
            :aria-checked="entryMode === mode.value"
            class="inline-flex h-9 items-center justify-center gap-2 rounded-item text-sm font-semibold transition-colors"
            :class="entryMode === mode.value ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'"
            @click="entryMode = mode.value"
          >
            <MdiIcon
              :path="mode.icon"
              class="size-4"
            />
            {{ mode.label }}
          </button>
        </div>

        <SelectField
          v-if="configuratorWeekStart"
          v-model="configuratorSlot"
          :label="$t('meal-plan.saved-meal-day')"
          :items="configuratorSlots"
        />
        <MealPlanDatePicker
          v-else
          v-model="pickerModel"
          :multiple="pickerMultiple"
          :entry-type="entryType"
        />

        <label
          v-if="!configuratorWeekStart && showWeekOption"
          class="flex cursor-pointer items-center justify-between gap-3"
        >
          <span>
            <span class="block text-[15px] font-medium">{{ $t("meal-plan.plan-for-the-whole-week") }}</span>
            <span
              v-if="isWeekEntry"
              class="block text-sm text-muted-foreground"
            >{{ $d(weekRange.start, "short") }} – {{ $d(weekRange.end, "short") }}</span>
          </span>
          <Switch v-model="isWeekEntry" />
        </label>

        <SelectField
          v-model="entryType"
          :items="planTypeOptions"
          :label="$t('recipe.entry-type')"
          item-title="text"
          item-value="value"
        />

        <div
          v-if="isRecipe && recipe"
          class="flex items-center gap-3"
        >
          <span class="text-sm font-semibold">{{ $t("recipe.servings") }}</span>
          <RecipeScaleEditButton
            v-model="recipeScale"
            :recipe-servings="recipeServings"
            edit-scale
          />
        </div>
        <template v-if="isRecipe && recipe && !isWeekEntry && batches">
          <SelectField
            v-model="cookingMode"
            :items="cookingModes"
            :label="$t('meal-plan.cooking-mode')"
          />
          <SelectField
            v-if="cookingMode === 'leftovers'"
            v-model="leftoverBatchId"
            :items="batchOptions"
            :label="$t('meal-plan.leftover-batch')"
          />
          <p v-if="batchMessage" class="m-0 text-sm text-destructive">
            {{ batchMessage }}
          </p>
        </template>
      </div>

      <!-- both modes fill the same pane, so the dialog doesn't resize when switching between them -->
      <div class="flex min-h-[22rem] flex-col md:max-h-[60vh]">
        <RecipeSelector
          v-if="isRecipe"
          ref="selector"
          v-model="recipe"
          class="min-h-0 flex-auto"
          height="auto"
          :query-filter="ruleQueryFilter"
        >
          <template #filters>
            <label
              class="ms-auto flex items-center gap-2 text-sm font-medium"
              :class="!applicableRuleFilter && 'opacity-50'"
            >
              {{ $t('meal-plan.ignore-rules') }}
              <Switch
                v-model="ignoreRules"
                :disabled="!applicableRuleFilter"
              />
            </label>
          </template>
          <template #no-results>
            <div class="flex flex-col items-start gap-2 rounded-card bg-highlight/50 px-4 py-4 text-sm">
              <template v-if="ruleQueryFilter">
                {{ $t("meal-plan.no-recipes-match-your-rules") }}
                <Button
                  variant="outline"
                  size="sm"
                  @click="ignoreRules = true"
                >
                  {{ $t("meal-plan.ignore-rules") }}
                </Button>
              </template>
              <template v-else>
                {{ $t('search.no-results') }}
              </template>
            </div>
          </template>
        </RecipeSelector>

        <div
          v-else
          class="flex flex-col gap-3"
        >
          <TextField
            v-model="title"
            :label="$t('meal-plan.meal-title')"
            :rules="[validators.required]"
            autofocus
          />
          <TextareaField
            v-model="text"
            :label="$t('meal-plan.meal-note')"
            :rows="6"
          />
        </div>
      </div>
    </div>
  </BaseDialog>
</template>

<script setup lang="ts">
import { addDays, format, parseISO } from "date-fns";
import RecipeScaleEditButton from "~/components/Domain/Recipe/RecipeScaleEditButton.vue";
import { Button } from "~/components/ui/button";
import SelectField from "~/components/ui/field/SelectField.vue";
import TextareaField from "~/components/ui/field/TextareaField.vue";
import TextField from "~/components/ui/field/TextField.vue";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { Switch } from "~/components/ui/switch";
import RecipeSelector from "~/components/Domain/Recipe/RecipeSelector.vue";
import { useMealPlanEntryDates, usePlanTypeOptions } from "~/composables/use-group-mealplan";
import { batchPrecedesMeal, getAvailableLeftovers, getBaseServings, type MealBatch } from "~/composables/use-mealplan-batches";
import { buildRuleQueryFilter, useMealplanRules } from "~/composables/use-mealplan-rules";
import { useUserMealPlanPreferences } from "~/composables/use-users/preferences";
import { uuid4 } from "~/composables/use-utils";
import { validators } from "~/composables/use-validators";
import type { PlanEntryCreate, PlanEntryType, PlanEntryOut, PlanEntryUpdate } from "~/lib/api/types/meal-plan";
import type { RecipeSummary } from "~/lib/api/types/recipe";

interface Props {
  entry?: PlanEntryOut | null;
  configuratorWeekStart?: Date;
  date?: Date | null;
  /** Set when creating an entry for a week rather than a specific day */
  endDate?: Date | null;
  batches?: MealBatch[];
  /** Meal type to start a new entry with (the board passes the row it was opened from). */
  defaultEntryType?: PlanEntryType | null;
}
const props = withDefaults(defineProps<Props>(), {
  entry: null,
  date: null,
  endDate: null,
  defaultEntryType: null,
});

const emit = defineEmits<{
  create: [payload: PlanEntryCreate, recipe: RecipeSummary | null];
  update: [payload: PlanEntryUpdate, recipe: RecipeSummary | null];
}>();

const dialog = defineModel<boolean>({ required: true });

const { rules } = useMealplanRules();
const planTypeOptions = usePlanTypeOptions();

const selector = ref<InstanceType<typeof RecipeSelector> | null>(null);

const entryMode = ref<"recipe" | "note">("recipe");
const { selectedDate, isWeekEntry, weekRange, entryDates, entryDatesPayload, pickerModel, pickerMultiple }
  = useMealPlanEntryDates();
const entryType = ref<PlanEntryType>("dinner");
const recipe = ref<RecipeSummary | null>(null);
const recipeScale = ref(1);
const cookingMode = ref<"planned" | "full" | "leftovers">("planned");
const leftoverBatchId = ref<string | null>(null);
const title = ref("");
const text = ref("");
const ignoreRules = ref(false);

const isRecipe = computed(() => entryMode.value === "recipe");

const i18n = useI18n();
const { $globals } = useNuxtApp();
const configuratorSlots = computed(() => {
  const start = props.configuratorWeekStart;
  if (!start) return [];
  const weekdays = new Intl.DateTimeFormat(i18n.locale.value, { weekday: "long" });
  return [
    { value: "week", title: i18n.t("meal-plan.saved-whole-week") },
    ...Array.from({ length: 7 }, (_, offset) => {
      const date = addDays(start, offset);
      return { value: format(date, "yyyy-MM-dd"), title: weekdays.format(date) };
    }),
  ];
});
const configuratorSlot = computed({
  get: () => isWeekEntry.value ? "week" : format(selectedDate.value, "yyyy-MM-dd"),
  set(value) {
    isWeekEntry.value = value === "week";
    selectedDate.value = isWeekEntry.value ? props.configuratorWeekStart! : parseISO(value);
  },
});

const modes = computed(() => [
  { value: "recipe" as const, label: i18n.t("general.recipe"), icon: $globals.icons.silverwareForkKnife },
  { value: "note" as const, label: i18n.t("meal-plan.note"), icon: $globals.icons.textBox },
]);

const mealPlanPreferences = useUserMealPlanPreferences();
const showWeekOption = computed(() => mealPlanPreferences.value.mode === "weeks" || isWeekEntry.value);

const applicableRuleFilter = computed(() => buildRuleQueryFilter(
  rules.value,
  entryDates.value.date,
  entryType.value,
  entryDates.value.endDate,
));
const ruleQueryFilter = computed(() => ignoreRules.value ? null : applicableRuleFilter.value);

const recipeServings = computed(() => getBaseServings(recipe.value));
const cookingModes = computed(() => [
  { value: "planned", title: i18n.t("meal-plan.cook-planned-servings") },
  { value: "full", title: i18n.t("meal-plan.cook-full-batch") },
  { value: "leftovers", title: i18n.t("meal-plan.use-leftovers") },
]);
const matchingBatches = computed(() => {
  const date = format(selectedDate.value, "yyyy-MM-dd");
  return (props.batches ?? []).filter(batch =>
    batch.source.id !== props.entry?.id
    && batch.source.recipeId === recipe.value?.id
    && batchPrecedesMeal(batch.source, date, entryType.value)
    && (batch.id === leftoverBatchId.value || availableServings(batch) > 0),
  );
});
function availableServings(batch: MealBatch) {
  return getAvailableLeftovers(batch, props.entry?.id);
}
const batchOptions = computed(() => {
  const options = matchingBatches.value.map(batch => ({
    value: batch.id,
    title: i18n.t("meal-plan.leftover-batch-option", {
      date: props.configuratorWeekStart
        ? new Intl.DateTimeFormat(i18n.locale.value, { weekday: "long" }).format(parseISO(batch.source.date))
        : i18n.d(parseISO(batch.source.date), "short"),
      meal: i18n.t(`meal-plan.${batch.source.entryType}`),
      remaining: i18n.n(Math.max(0, availableServings(batch)), { maximumFractionDigits: 2 }),
    }),
  }));
  if (leftoverBatchId.value && !options.some(option => option.value === leftoverBatchId.value)) {
    options.push({ value: leftoverBatchId.value, title: i18n.t("meal-plan.leftover-batch-unavailable") });
  }
  return options;
});
const batchMessage = computed(() => {
  if (!props.batches || !isRecipe.value || !recipe.value || isWeekEntry.value) return "";
  if (cookingMode.value === "full" && recipeScale.value > 1) {
    return i18n.t("meal-plan.full-batch-too-small");
  }
  if (cookingMode.value === "leftovers") {
    const batch = matchingBatches.value.find(batch => batch.id === leftoverBatchId.value);
    if (!batch) return i18n.t(matchingBatches.value.length ? "meal-plan.select-leftover-batch" : "meal-plan.no-leftover-batch");
    if (recipeScale.value * recipeServings.value - availableServings(batch) > 1e-6) {
      return i18n.t("meal-plan.leftover-batch-too-small");
    }
  }
  return "";
});

// a scale is only meaningful for the recipe it was chosen for
watch(() => recipe.value?.id, () => {
  recipeScale.value = 1;
  cookingMode.value = "planned";
  leftoverBatchId.value = null;
}, { flush: "sync" });

const submitDisabled = computed(() => isRecipe.value ? !recipe.value || !!batchMessage.value : !title.value.trim());

function initialize() {
  entryMode.value = props.entry && !props.entry.recipeId ? "note" : "recipe";
  selectedDate.value = props.entry ? parseISO(props.entry.date) : props.date ?? new Date();
  isWeekEntry.value = props.entry ? !!props.entry.endDate : !!props.endDate;
  entryType.value = props.entry?.entryType ?? props.defaultEntryType ?? "dinner";
  recipe.value = props.entry?.recipe ?? null;
  recipeScale.value = props.entry?.recipeScale ?? 1;
  cookingMode.value = props.entry?.leftoverBatchId ? "leftovers" : props.entry?.recipeBatchId ? "full" : "planned";
  leftoverBatchId.value = props.entry?.leftoverBatchId ?? null;
  title.value = props.entry?.title ?? "";
  text.value = props.entry?.text ?? "";
  ignoreRules.value = false;
  selector.value?.reset();
}

function submit() {
  if (submitDisabled.value) return;
  const chooseBatch = props.batches && isRecipe.value && !isWeekEntry.value;
  const existingBatch = props.entry?.recipeId === recipe.value?.id ? props.entry?.recipeBatchId : null;
  const payload = {
    ...entryDatesPayload.value,
    ...(props.configuratorWeekStart && {
      date: format(isWeekEntry.value ? props.configuratorWeekStart : selectedDate.value, "yyyy-MM-dd"),
      endDate: isWeekEntry.value ? format(addDays(props.configuratorWeekStart, 6), "yyyy-MM-dd") : null,
    }),
    entryType: entryType.value,
    title: isRecipe.value ? "" : title.value,
    text: isRecipe.value ? "" : text.value,
    recipeId: isRecipe.value ? recipe.value?.id : null,
    recipeScale: isRecipe.value ? recipeScale.value : 1,
    ...(props.batches && {
      recipeBatchId: chooseBatch && cookingMode.value === "full"
        ? existingBatch ?? uuid4()
        : null,
      leftoverBatchId: chooseBatch && cookingMode.value === "leftovers" ? leftoverBatchId.value : null,
    }),
  };

  if (props.entry) {
    emit("update", {
      ...payload,
      id: props.entry.id,
      groupId: props.entry.groupId,
      userId: props.entry.userId,
    }, isRecipe.value ? recipe.value : null);
  }
  else {
    emit("create", payload, isRecipe.value ? recipe.value : null);
  }
}

watch(dialog, (isOpen) => {
  if (isOpen) {
    initialize();
  }
});
</script>
