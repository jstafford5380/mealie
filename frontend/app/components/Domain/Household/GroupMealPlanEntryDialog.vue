<template>
  <BaseDialog
    v-model="dialog"
    :title="entry ? $t('meal-plan.update-this-meal-plan') : $t('meal-plan.create-a-new-meal-plan')"
    :submit-text="entry ? $t('general.update') : $t('general.create')"
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

        <MealPlanDatePicker
          v-model="pickerModel"
          :multiple="pickerMultiple"
          :entry-type="entryType"
        />

        <label
          v-if="showWeekOption"
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
      </div>

      <!-- both modes fill the same pane, so the dialog doesn't resize when switching between them -->
      <div class="flex min-h-[22rem] flex-col md:max-h-[60vh]">
        <RecipeSelector
          v-if="isRecipe"
          ref="selector"
          v-model="recipe"
          height="100%"
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
import RecipeScaleEditButton from "~/components/Domain/Recipe/RecipeScaleEditButton.vue";
import { Button } from "~/components/ui/button";
import SelectField from "~/components/ui/field/SelectField.vue";
import TextareaField from "~/components/ui/field/TextareaField.vue";
import TextField from "~/components/ui/field/TextField.vue";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { Switch } from "~/components/ui/switch";
import RecipeSelector from "~/components/Domain/Recipe/RecipeSelector.vue";
import { useMealPlanEntryDates, usePlanTypeOptions } from "~/composables/use-group-mealplan";
import { buildRuleQueryFilter, useMealplanRules } from "~/composables/use-mealplan-rules";
import { useUserMealPlanPreferences } from "~/composables/use-users/preferences";
import { validators } from "~/composables/use-validators";
import type { PlanEntryCreate, PlanEntryType, PlanEntryOut, PlanEntryUpdate } from "~/lib/api/types/meal-plan";
import type { RecipeSummary } from "~/lib/api/types/recipe";

interface Props {
  entry?: PlanEntryOut | null;
  date?: Date | null;
  /** Set when creating an entry for a week rather than a specific day */
  endDate?: Date | null;
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
  create: [payload: PlanEntryCreate];
  update: [payload: PlanEntryUpdate];
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
const title = ref("");
const text = ref("");
const ignoreRules = ref(false);

const isRecipe = computed(() => entryMode.value === "recipe");

const i18n = useI18n();
const { $globals } = useNuxtApp();
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

const recipeServings = computed(() => recipe.value?.recipeServings || recipe.value?.recipeYieldQuantity || 1);

// a scale is only meaningful for the recipe it was chosen for
watch(() => recipe.value?.id, () => {
  recipeScale.value = 1;
}, { flush: "sync" });

const submitDisabled = computed(() => isRecipe.value ? !recipe.value : !title.value.trim());

function parseEntryDate(date: string) {
  const [year, month, day] = date.split("-").map(Number);
  return new Date(year, month - 1, day);
}

function initialize() {
  entryMode.value = props.entry && !props.entry.recipeId ? "note" : "recipe";
  selectedDate.value = props.entry ? parseEntryDate(props.entry.date) : props.date ?? new Date();
  isWeekEntry.value = props.entry ? !!props.entry.endDate : !!props.endDate;
  entryType.value = props.entry?.entryType ?? props.defaultEntryType ?? "dinner";
  recipe.value = props.entry?.recipe ?? null;
  recipeScale.value = props.entry?.recipeScale ?? 1;
  title.value = props.entry?.title ?? "";
  text.value = props.entry?.text ?? "";
  ignoreRules.value = false;
  selector.value?.reset();
}

function submit() {
  const payload = {
    ...entryDatesPayload.value,
    entryType: entryType.value,
    title: isRecipe.value ? "" : title.value,
    text: isRecipe.value ? "" : text.value,
    recipeId: isRecipe.value ? recipe.value?.id : null,
    recipeScale: isRecipe.value ? recipeScale.value : 1,
  };

  if (props.entry) {
    emit("update", {
      ...payload,
      id: props.entry.id,
      groupId: props.entry.groupId,
      userId: props.entry.userId,
    });
  }
  else {
    emit("create", payload);
  }
}

watch(dialog, (isOpen) => {
  if (isOpen) {
    initialize();
  }
});
</script>
