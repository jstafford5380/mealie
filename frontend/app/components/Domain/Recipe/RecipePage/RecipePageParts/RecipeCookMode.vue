<script setup lang="ts">
import type { RecipeOut } from "~/lib/api/types/recipe";
import { ArrowLeftIcon, ArrowRightIcon, CheckIcon, ClockIcon, XIcon } from "@lucide/vue";
import { onKeyStroke, useScrollLock } from "@vueuse/core";
import RecipeIngredients from "~/components/Domain/Recipe/RecipeIngredients.vue";
import { Button } from "~/components/ui/button";
import { useRecipeMethod } from "~/composables/recipe-page/use-recipe-method";
import RecipePageIngredientToolsView from "./RecipePageIngredientToolsView.vue";
import RecipePageScale from "./RecipePageScale.vue";

/**
 * Cook mode: one step at a time, large enough to read from across the counter,
 * with that step's ingredients beside it. Progress is shared with the reader's method.
 */
const props = defineProps<{
  /** The recipe as saved, for the servings and units controls. */
  recipe: RecipeOut;
  /** The recipe as displayed (unit conversion applied). */
  displayedRecipe: RecipeOut;
  ingredientStorageKey?: string;
}>();
const scale = defineModel<number>("scale", { default: 1 });
const emit = defineEmits<{ close: [] }>();

const { steps, linkedIngredients, linkedNotes, formatDuration, isDone, setDone, resetDone } = useRecipeMethod(() => props.recipe);

const total = computed(() => steps.value.length);
const firstOpen = steps.value.findIndex((_, i) => !isDone(i));
const current = ref(firstOpen === -1 ? 0 : firstOpen);
const step = computed(() => steps.value[current.value]);

// The step's section heading carries over from the nearest titled step above it.
const sectionTitle = computed(() => {
  for (let i = current.value; i >= 0; i--) {
    if (steps.value[i]?.title) {
      return steps.value[i]!.title;
    }
  }
  return "";
});

const stepIngredients = computed(() => (step.value ? linkedIngredients(step.value, props.displayedRecipe.recipeIngredient) : []));
const stepNotes = computed(() => (step.value ? linkedNotes(step.value) : []));
// Steps without linked ingredients show the full list; otherwise the cook's last choice holds.
const preferAll = ref(false);
const panel = computed<"step" | "all">({
  get: () => (stepIngredients.value.length && !preferAll.value ? "step" : "all"),
  set: (value) => {
    preferAll.value = value === "all";
  },
});

const unlinkedIngredients = computed(() => props.displayedRecipe.recipeIngredient.filter(ing =>
  !steps.value.some(s => s.ingredientReferences?.some(r => r.referenceId === ing.referenceId)),
));
const hasAnyLinks = computed(() => unlinkedIngredients.value.length < props.displayedRecipe.recipeIngredient.length);

const isLast = computed(() => current.value >= total.value - 1);

const stage = ref<HTMLElement>();
function goTo(index: number) {
  current.value = Math.min(Math.max(index, 0), Math.max(total.value - 1, 0));
  stage.value?.scrollTo({ top: 0 });
}
function next() {
  if (isLast.value) {
    // the dish is done; the next cook starts from step one
    resetDone();
    emit("close");
    return;
  }
  setDone(current.value, true);
  goTo(current.value + 1);
}
function previous() {
  goTo(current.value - 1);
}

function fromControl(event: KeyboardEvent) {
  const el = event.target as HTMLElement | null;
  return !!el?.closest("input, textarea, select, [contenteditable], [role='menu'], [role='listbox'], [role='dialog']");
}
onKeyStroke("ArrowRight", (e) => {
  if (!fromControl(e)) {
    e.preventDefault();
    next();
  }
});
onKeyStroke("ArrowLeft", (e) => {
  if (!fromControl(e)) {
    e.preventDefault();
    previous();
  }
});

// Cook mode covers the page; the page underneath shouldn't scroll with it.
const scrollLock = useScrollLock(import.meta.client ? document.documentElement : null);
onMounted(() => {
  scrollLock.value = true;
});
onBeforeUnmount(() => {
  scrollLock.value = false;
});
</script>

<template>
  <div
    class="fixed inset-0 z-[2040] flex flex-col bg-background font-sans text-foreground"
    role="region"
    :aria-label="$t('recipe.cook-mode')"
  >
    <!-- top bar -->
    <div class="flex items-center gap-3 border-b bg-card px-3 py-2 sm:px-5">
      <Button
        variant="ghost"
        size="icon"
        :aria-label="$t('recipe.exit-cook-mode')"
        :title="$t('recipe.exit-cook-mode')"
        @click="emit('close')"
      >
        <XIcon class="size-5" />
      </Button>
      <div class="min-w-0 flex-1">
        <div class="truncate font-serif text-lg leading-tight">
          {{ recipe.name }}
        </div>
        <div
          v-if="total"
          class="text-xs text-muted-foreground"
        >
          {{ $t('recipe.step-of', { step: current + 1, total }) }}
        </div>
      </div>
      <WakelockSwitch class="!p-0 max-sm:display-none" />
    </div>

    <!-- progress: one segment per step, tap to jump -->
    <div
      v-if="total > 1"
      class="flex gap-1 bg-card px-3 pb-2 sm:px-5"
    >
      <button
        v-for="(_, i) in steps"
        :key="i"
        type="button"
        class="h-1.5 flex-1 rounded-full transition-colors"
        :class="i === current ? 'bg-brand' : isDone(i) ? 'bg-primary' : 'bg-muted'"
        :aria-label="$t('recipe.step-index', { step: i + 1 })"
        :aria-current="i === current ? 'step' : undefined"
        @click="goTo(i)"
      />
    </div>

    <div class="grid min-h-0 flex-1 grid-cols-1 lg:grid-cols-[minmax(300px,380px)_minmax(0,1fr)]">
      <!-- ingredients -->
      <aside class="order-2 min-h-0 overflow-y-auto border-t bg-card px-4 py-4 lg:order-1 lg:border-e lg:border-t-0 lg:px-5">
        <RecipePageScale
          v-model="scale"
          :recipe="recipe"
          class="mb-4"
        />
        <div
          v-if="hasAnyLinks && stepIngredients.length"
          class="mb-3 inline-flex rounded-control bg-muted p-1 text-sm"
          role="tablist"
        >
          <button
            v-for="option in (['step', 'all'] as const)"
            :key="option"
            type="button"
            role="tab"
            :aria-selected="panel === option"
            class="rounded-item px-3 py-1.5 font-semibold transition-colors"
            :class="panel === option ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground'"
            @click="panel = option"
          >
            {{ option === 'step' ? $t('recipe.for-this-step') : $t('recipe.all-ingredients') }}
          </button>
        </div>
        <template v-if="panel === 'step' && stepIngredients.length">
          <RecipeIngredients
            :value="stepIngredients"
            :scale="scale"
            is-cook-mode
            :storage-key="ingredientStorageKey"
          />
          <div
            v-if="unlinkedIngredients.length"
            class="mt-6"
          >
            <h3 class="m-0 mb-1 text-sm font-semibold text-muted-foreground">
              {{ $t('recipe.not-linked-ingredients') }}
            </h3>
            <RecipeIngredients
              :value="unlinkedIngredients"
              :scale="scale"
              is-cook-mode
              :storage-key="ingredientStorageKey"
            />
          </div>
        </template>
        <RecipePageIngredientToolsView
          v-else
          :recipe="displayedRecipe"
          :scale="scale"
          is-cook-mode
          :ingredient-storage-key="ingredientStorageKey"
        />
      </aside>

      <!-- the step -->
      <main
        ref="stage"
        class="order-1 min-h-0 overflow-y-auto px-5 py-6 sm:px-10 sm:py-10 lg:order-2"
      >
        <div
          v-if="step"
          :key="current"
          class="mx-auto max-w-[68ch]"
        >
          <div
            v-if="sectionTitle"
            class="mb-2 text-sm font-semibold text-muted-foreground"
          >
            {{ sectionTitle }}
          </div>
          <div class="mb-4 flex flex-wrap items-center gap-3">
            <span class="font-serif text-[56px] leading-none text-primary">{{ current + 1 }}</span>
            <SafeMarkdown
              v-if="step.summary"
              class="text-xl font-semibold [&_p]:m-0"
              :source="step.summary"
            />
            <span
              v-if="step.durationSeconds"
              class="inline-flex items-center gap-1.5 rounded-full bg-subtle px-3 py-1 text-sm font-semibold text-subtle-foreground"
            >
              <ClockIcon class="size-4" />
              {{ formatDuration(step.durationSeconds) }}
            </span>
          </div>
          <SafeMarkdown
            class="recipe-step-text text-[21px] leading-[1.6] sm:text-[24px]"
            :source="step.text || ''"
          />
          <div
            v-if="stepNotes.length"
            class="mt-8 flex flex-col gap-3"
          >
            <div
              v-for="note in stepNotes"
              :key="note.referenceId ?? note.title"
              class="rounded-card border-s-4 border-brand bg-card p-4"
            >
              <div class="mb-1 font-semibold">
                {{ note.title || $t('recipe.note') }}
              </div>
              <SafeMarkdown
                class="text-[16px] leading-relaxed [&_p]:m-0"
                :source="note.text"
              />
            </div>
          </div>
        </div>
      </main>
    </div>

    <!-- step navigation -->
    <div class="flex items-center gap-3 border-t bg-card px-3 py-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] sm:px-5">
      <Button
        variant="outline"
        size="lg"
        :disabled="current === 0"
        @click="previous"
      >
        <ArrowLeftIcon class="size-5" />
        <span class="max-sm:sr-only">{{ $t('general.previous') }}</span>
      </Button>
      <Button
        size="lg"
        class="ms-auto min-w-40"
        @click="next"
      >
        <template v-if="isLast">
          <CheckIcon class="size-5" />
          {{ $t('recipe.finish-cooking') }}
        </template>
        <template v-else>
          {{ $t('general.next') }}
          <ArrowRightIcon class="size-5" />
        </template>
      </Button>
    </div>
  </div>
</template>
