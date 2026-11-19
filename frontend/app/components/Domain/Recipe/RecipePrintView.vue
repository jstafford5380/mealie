<template>
  <div :class="dense ? 'wrapper' : 'wrapper p-3'">
    <section class="mb-4 grid items-center gap-6 font-sans" :class="showImage ? 'grid-cols-[1fr_2fr]' : 'grid-cols-1'">
      <img
        v-if="showImage"
        :key="imageKey"
        :src="recipeImageUrl"
        alt=""
        class="max-w-full rounded-control"
        :class="preferences.imagePosition == ImagePosition.left ? 'order-first' : 'order-last'"
      >
      <div>
        <h1 class="m-0 mb-3 font-serif text-[26px] leading-tight">
          {{ recipe.name }}
        </h1>
        <p
          v-if="recipeYield"
          class="m-0 mb-3 flex items-center gap-2 text-sm"
        >
          <MdiIcon
            :path="$globals.icons.potSteam"
            class="size-4"
          />
          <SafeInlineHtml :html="recipeYield" />
        </p>
        <RecipeTimeCard
          :prep-time="recipe.prepTime"
          :total-time="recipe.totalTime"
          :perform-time="recipe.performTime"
          :prep-time-seconds="recipe.prepTimeSeconds"
          :total-time-seconds="recipe.totalTimeSeconds"
          :perform-time-seconds="recipe.performTimeSeconds"
          small
        />
        <SafeMarkdown
          v-if="preferences.showDescription"
          :source="recipe.description"
          class="mt-3 text-sm"
        />
      </div>
    </section>

    <!-- Ingredients -->
    <section>
      <h2 class="print-heading">
        {{ $t("recipe.ingredients") }}
      </h2>
      <div
        v-for="(ingredientSection, sectionIndex) in ingredientSections"
        :key="`ingredient-section-${sectionIndex}`"
        class="print-section"
      >
        <h4
          v-if="ingredientSection.ingredients[0].title"
          class="ingredient-title mt-2"
        >
          {{ ingredientSection.ingredients[0].title }}
        </h4>
        <div
          class="ingredient-grid"
          :style="{ gridTemplateRows: `repeat(${Math.ceil(ingredientSection.ingredients.length / 2)}, min-content)` }"
        >
          <div
            v-for="(ingredient, ingredientIndex) in ingredientSection.ingredients"
            :key="`ingredient-${ingredientIndex}`"
            class="ingredient-cell"
          >
            <p class="ingredient-body">
              <SafeInlineHtml :html="parseText(ingredient)" />
            </p>
            <!-- paper has nothing to tap, so what the menu holds on screen is spelled out here -->
            <SafeMarkdown
              v-if="preferences.showSubstitutions && substitutionSummary(ingredient)"
              class="substitution-body"
              :source="$t('recipe.substitutions-with-value', { substitutions: substitutionSummary(ingredient) })"
            />
          </div>
        </div>
      </div>
    </section>

    <!-- Instructions -->
    <section>
      <div
        v-for="(instructionSection, sectionIndex) in instructionSections"
        :key="`instruction-section-${sectionIndex}`"
        :class="{ 'print-section': instructionSection.sectionName }"
      >
        <h2
          v-if="!sectionIndex"
          class="print-heading"
        >
          {{ $t("recipe.instructions") }}
        </h2>
        <div
          v-for="(step, stepIndex) in instructionSection.instructions"
          :key="`instruction-${stepIndex}`"
        >
          <div class="print-section">
            <h4
              v-if="step.title"
              :key="`instruction-title-${stepIndex}`"
              class="instruction-title mb-2"
            >
              {{ step.title }}
            </h4>
            <h5>
              {{ step.summary ? step.summary : $t("recipe.step-index", {
                step: stepIndex
                  + instructionSection.stepOffset
                  + 1,
              }) }}
            </h5>
            <SafeMarkdown
              :source="step.text"
              class="recipe-step-body"
            />
            <!-- Step Ingredients -->
            <div
              v-if="preferences.showLinkedIngredients && step.ingredientReferences && step.ingredientReferences.length > 0"
              class="print-section"
            >
              <h6
                class="ingredient-title mt-2 mb-0"
              >
                {{ $t("recipe.ingredients") }}
              </h6>
              <div
                class="step-ingredient-grid"
                :style="{ gridTemplateRows: `repeat(${Math.ceil(step.ingredientReferences.length / 2)}, min-content)` }"
              >
                <template
                  v-for="(ingredient, ingredientIndex) in stepLinkedIngredients.get(`${sectionIndex}-${stepIndex}`) ?? []"
                  :key="`ingredient-${ingredientIndex}`"
                >
                  <p class="ingredient-body">
                    <SafeInlineHtml :html="parseText(ingredient)" />
                  </p>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Notes -->
    <div v-if="preferences.showNotes">
      <hr
        v-if="hasNotes"
        class="my-4 border-t border-black/30"
      >

      <section>
        <div
          v-for="(note, index) in recipe.notes"
          :key="index + 'note'"
        >
          <div class="print-section">
            <h4>{{ note.title }}</h4>
            <SafeMarkdown
              :source="note.text"
              class="note-body"
            />
          </div>
        </div>
      </section>
    </div>

    <!-- Nutrition -->
    <div v-if="preferences.showNutrition">
      <h2 class="print-heading">
        {{ $t("recipe.nutrition") }}
        <span class="nutrition-per-serving">({{ $t("recipe.per-serving") }})</span>
      </h2>

      <section>
        <div class="print-section">
          <table class="nutrition-table">
            <tbody>
              <tr
                v-for="(value, key) in recipe.nutrition"
                :key="key"
              >
                <template v-if="value">
                  <td>{{ labels[key].label }}</td>
                  <td>{{ value ? (labels[key].suffix ? `${value} ${labels[key].suffix}` : value) : '-' }}</td>
                </template>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { MdiIcon } from "~/components/ui/mdi-icon";
import RecipeTimeCard from "~/components/Domain/Recipe/RecipeTimeCard.vue";
import { useStaticRoutes } from "~/composables/api";
import type { RecipeOut, RecipeIngredient, RecipeStep } from "~/lib/api/types/recipe";
import { ImagePosition, useUserPrintPreferences } from "~/composables/use-users/preferences";
import { ingredientSubstitutionSummary, useFoodPlurality, useIngredientTextParser, useNutritionLabels } from "~/composables/recipes";
import { usePageState } from "~/composables/recipe-page/shared-state";
import { useScaledAmount } from "~/composables/recipes/use-scaled-amount";

type IngredientSection = {
  sectionName: string;
  ingredients: RecipeIngredient[];
};

type InstructionSection = {
  sectionName: string;
  stepOffset: number;
  instructions: RecipeStep[];
};

interface Props {
  recipe: RecipeOut;
  scale?: number;
  dense?: boolean;
}
const props = withDefaults(defineProps<Props>(), {
  scale: 1,
  dense: false,
});

const i18n = useI18n();
const preferences = useUserPrintPreferences();
const { recipeImage } = useStaticRoutes();
const { imageKey } = usePageState(props.recipe.slug);
const { labels } = useNutritionLabels();

const servingsDisplay = computed(() => {
  const { scaledAmountDisplay } = useScaledAmount(props.recipe.recipeYieldQuantity, props.scale);
  return scaledAmountDisplay || props.recipe.recipeYield
    ? i18n.t("recipe.yields-amount-with-text", {
      amount: scaledAmountDisplay,
      text: props.recipe.recipeYield,
    }) as string
    : "";
});

const yieldDisplay = computed(() => {
  const { scaledAmountDisplay } = useScaledAmount(props.recipe.recipeServings, props.scale);
  return scaledAmountDisplay ? i18n.t("recipe.serves-amount", { amount: scaledAmountDisplay }) as string : "";
});

const recipeYield = computed(() => {
  if (servingsDisplay.value && yieldDisplay.value) {
    return `${yieldDisplay.value}; ${servingsDisplay.value}`;
  }
  else {
    return yieldDisplay.value || servingsDisplay.value;
  }
});

const recipeImageUrl = computed(() => {
  return recipeImage(props.recipe.id, props.recipe.image, imageKey.value);
});

// Group ingredients by section so we can style them independently
const ingredientSections = computed<IngredientSection[]>(() => {
  if (!props.recipe.recipeIngredient) {
    return [];
  }
  const addIngredientsToSections = (ingredients: RecipeIngredient[], sections: IngredientSection[], title: string | null) => {
  // If title is set, ensure the section exists before adding ingredients
    let section: IngredientSection | undefined;
    if (title) {
      section = sections.find(sec => sec.sectionName === title);
      if (!section) {
        section = { sectionName: title, ingredients: [] };
        sections.push(section);
      }
    }

    ingredients.forEach((ingredient) => {
      if (preferences.value.expandChildRecipes && ingredient.referencedRecipe?.recipeIngredient?.length) {
        // Recursively add to the section for this referenced recipe
        addIngredientsToSections(
          ingredient.referencedRecipe.recipeIngredient,
          sections,
          "",
        );
      }
      else {
        const sectionName = title || ingredient.title || "";
        if (sectionName) {
          let sec = sections.find(sec => sec.sectionName === sectionName);
          if (!sec) {
            sec = { sectionName, ingredients: [] };
            sections.push(sec);
          }
          ingredient.title = sectionName;
          sec.ingredients.push(ingredient);
        }
        else {
          if (sections.length === 0) {
            sections.push({
              sectionName: "",
              ingredients: [ingredient],
            });
          }
          else {
            sections[sections.length - 1].ingredients.push(ingredient);
          }
        }
      }
    });
  };

  const sections: IngredientSection[] = [];
  addIngredientsToSections(props.recipe.recipeIngredient, sections, null);
  return sections;
});

// Group instructions by section so we can style them independently
const instructionSections = computed<InstructionSection[]>(() => {
  if (!props.recipe.recipeInstructions) {
    return [];
  }

  return props.recipe.recipeInstructions.reduce((sections, step) => {
    const offset = (() => {
      if (sections.length === 0) {
        return 0;
      }

      const lastOffset = sections[sections.length - 1].stepOffset;
      const lastNumSteps = sections[sections.length - 1].instructions.length;
      return lastOffset + lastNumSteps;
    })();

    // if title append new section to the end of the array
    if (step.title) {
      sections.push({
        sectionName: step.title,
        stepOffset: offset,
        instructions: [step],
      });

      return sections;
    }

    // append if first element
    if (sections.length === 0) {
      sections.push({
        sectionName: "",
        stepOffset: offset,
        instructions: [step],
      });

      return sections;
    }

    // otherwise add step to last section in the array
    sections[sections.length - 1].instructions.push(step);
    return sections;
  }, [] as InstructionSection[]);
});

const hasNotes = computed(() => {
  return props.recipe.notes && props.recipe.notes.length > 0;
});

// Precompute each step's linked ingredients so the template doesn't re-filter recipeIngredient on every render
const stepLinkedIngredients = computed(() => {
  const map = new Map<string, RecipeIngredient[]>();

  instructionSections.value.forEach((section, sectionIndex) => {
    section.instructions.forEach((step, stepIndex) => {
      if (!step.ingredientReferences?.length) {
        return;
      }

      const referenceIds = new Set(step.ingredientReferences.map(ref => ref.referenceId));
      map.set(
        `${sectionIndex}-${stepIndex}`,
        props.recipe.recipeIngredient.filter(ing => ing.referenceId && referenceIds.has(ing.referenceId)),
      );
    });
  });

  return map;
});

const { parseIngredientText } = useIngredientTextParser();

function parseText(ingredient: RecipeIngredient) {
  return parseIngredientText(ingredient, props.scale);
}

const { shouldPluralizeFood } = useFoodPlurality();

// the substitutes inflect with the line they stand in for, the same as on screen
function substitutionSummary(ingredient: RecipeIngredient) {
  return ingredientSubstitutionSummary(ingredient, shouldPluralizeFood(ingredient, props.scale));
}
const showImage = computed(() => !!props.recipe.image && !!preferences.value.imagePosition && preferences.value.imagePosition !== ImagePosition.hidden);
</script>

<style scoped>
/* Makes all text solid black */
.wrapper {
  background-color: white;
}

.wrapper,
.wrapper :deep(*) {
  opacity: 1 !important;
  color: black !important;
}

/* Prevents sections from being broken up between pages */
.print-section {
  page-break-inside: avoid;
}

p {
  padding-bottom: 0 !important;
  margin-bottom: 0 !important;
}

.wrapper h4,
.wrapper h5,
.wrapper h6 {
  margin: 0.5rem 0 0.25rem;
  font-weight: 700;
}

.wrapper h4 {
  font-size: 1rem;
}

.wrapper h5,
.wrapper h6 {
  font-size: 0.9rem;
}

.print-heading {
  margin: 1.25rem 0 0.5rem;
  font-size: 1.25rem;
  font-weight: 700;
}

.ingredient-grid {
  display: grid;
  grid-auto-flow: column;
  grid-template-columns: 1fr 1fr;
  grid-gap: 0.5rem;
}

.step-ingredient-grid {
  display: grid;
  grid-auto-flow: column;
  grid-template-columns: 1fr 1fr;
  grid-gap: 0.2rem;
}

.ingredient-title,
.instruction-title {
  grid-column: 1 / span 2;
  text-decoration: underline;
  text-underline-offset: 4px;
}

.ingredient-body,
.recipe-step-body,
.note-body {
  font-size: 14px;
}

.ingredient-cell {
  break-inside: avoid;
}

.substitution-body {
  font-size: 12px;
  line-height: 1.3;
  opacity: 0.7;
}

.substitution-body :deep(p) {
  margin: 0;
}

ul {
  padding-left: 1rem;
}

li {
  list-style-type: none;
  margin-bottom: 0.25rem;
}

.nutrition-per-serving {
  font-size: 0.9rem;
  font-weight: normal;
}

.nutrition-table {
  max-width: 80%;
  border-collapse: collapse;
}

.nutrition-table th,
.nutrition-table td {
  padding: 6px 10px;
  text-align: left;
  vertical-align: top;
  font-size: 14px;
}

.nutrition-table th {
  font-weight: bold;
  padding-bottom: 10px;
}

.nutrition-table td:first-child {
  width: 70%;
  font-weight: bold;
}

.nutrition-table td:last-child {
  width: 30%;
  text-align: right;
}

.nutrition-table td {
  padding: 2px;
  text-align: left;
  font-size: 14px;
}
</style>
