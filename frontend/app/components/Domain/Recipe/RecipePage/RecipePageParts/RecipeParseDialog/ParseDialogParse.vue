<template>
  <ParseDialogChangeParser
    v-model="parser"
    :available-parsers="availableParsers"
    :show-nlp-language-hint="showNlpLanguageHint"
    @update:model-value="(newParser) => parser = newParser"
    @parse="parseIngredients"
  />
  <div
    v-if="currentIng"
    class="mt-4 flex flex-col gap-3 font-sans"
  >
    <p class="m-0 rounded-panel bg-muted px-6 py-4 text-center font-serif text-xl">
      {{ currentIng.input }}
    </p>
    <div
      class="flex items-center gap-2 text-sm font-medium"
      :class="(currentIng.confidence?.average || 0) < confidenceThreshold ? 'text-destructive' : 'text-primary'"
    >
      <MdiIcon
        :path="(currentIng.confidence?.average || 0) < confidenceThreshold ? $globals.icons.alert : $globals.icons.check"
        class="size-4"
      />
      {{ $t("recipe.parser.confidence-score") }}: {{ currentIng.confidence ? asPercentage(currentIng.confidence?.average!) : "" }}
    </div>
    <RecipeIngredientEditor
      v-model="currentIng.ingredient"
      :unit-error="!!currentMissingUnit"
      :unit-error-tooltip="$t('recipe.parser.this-unit-could-not-be-parsed-automatically')"
      :food-error="!!currentMissingFood"
      :food-error-tooltip="$t('recipe.parser.this-food-could-not-be-parsed-automatically')"
    />
    <div class="mt-2 flex flex-wrap items-center gap-2">
      <label class="me-auto flex cursor-pointer items-center gap-2 text-sm font-medium text-destructive">
        <Checkbox v-model="currentIngShouldDelete" />
        {{ $t("recipe.parser.delete-item") }}
      </label>
      <Button
        v-if="currentMissingUnit && !currentIng.ingredient.unit?.id"
        variant="outline"
        size="sm"
        :disabled="state.loading.unit"
        @click="createMissingUnit"
      >
        <MdiIcon
          :path="$globals.icons.units"
          class="size-4"
        />
        {{ $t("recipe.parser.missing-unit", { unit: currentMissingUnit }) }}
      </Button>
      <Button
        v-if="currentMissingUnit && currentIng.ingredient.unit?.id && currentMissingUnit.toLowerCase() != currentIng.ingredient.unit?.name.toLowerCase()"
        variant="outline"
        size="sm"
        :disabled="state.loading.unit"
        @click="addMissingUnitAsAlias"
      >
        <MdiIcon
          :path="$globals.icons.units"
          class="size-4"
        />
        {{ $t("recipe.parser.add-text-as-alias-for-item", { text: currentMissingUnit, item: currentIng.ingredient.unit.name }) }}
      </Button>
      <Button
        v-if="currentMissingFood && !currentIng.ingredient.food?.id"
        variant="outline"
        size="sm"
        :disabled="state.loading.food"
        @click="createMissingFood"
      >
        <MdiIcon
          :path="$globals.icons.foods"
          class="size-4"
        />
        {{ $t("recipe.parser.missing-food", { food: currentMissingFood }) }}
      </Button>
      <Button
        v-if="currentMissingFood && currentIng.ingredient.food?.id && currentMissingFood.toLowerCase() != currentIng.ingredient.food?.name.toLowerCase()"
        variant="outline"
        size="sm"
        :disabled="state.loading.food"
        @click="addMissingFoodAsAlias"
      >
        <MdiIcon
          :path="$globals.icons.foods"
          class="size-4"
        />
        {{ $t("recipe.parser.add-text-as-alias-for-item", { text: currentMissingFood, item: currentIng.ingredient.food.name }) }}
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Button } from "~/components/ui/button";
import { Checkbox } from "~/components/ui/checkbox";
import { MdiIcon } from "~/components/ui/mdi-icon";
import type { useParseIngredientsDialog } from "~/composables/recipes/use-parse-ingredients-dialog";

const props = defineProps<{
  dialogState: ReturnType<typeof useParseIngredientsDialog>;
}>();

const {
  state,
  currentIng,
  showNlpLanguageHint,
  availableParsers,
  currentIngShouldDelete,
  parser,
  confidenceThreshold,
  currentMissingFood,
  currentMissingUnit,
  parseIngredients,
  createMissingFood,
  createMissingUnit,
  addMissingFoodAsAlias,
  addMissingUnitAsAlias,
} = props.dialogState;

function asPercentage(num: number | undefined): string {
  if (!num) {
    return "0%";
  }

  return Math.round(num * 100).toFixed(2) + "%";
}
</script>
