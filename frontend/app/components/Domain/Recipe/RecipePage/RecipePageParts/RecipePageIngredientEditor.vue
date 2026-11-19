<template>
  <div class="font-sans">
    <div
      v-if="recipe.recipeIngredient.length > 0 && !hasFoodOrUnit"
      class="mb-5 flex flex-wrap items-center gap-3 rounded-card border border-primary/25 bg-highlight/50 p-4"
    >
      <MdiIcon
        :path="$globals.icons.information"
        class="size-5 shrink-0 text-primary"
      />
      <p class="m-0 min-w-0 flex-1 text-sm">
        {{ $t('recipe.ingredients-not-parsed-description', { parse: $t('recipe.parse') }) }}
      </p>
      <Button
        variant="outline"
        @click="toggleIsParsing(true)"
      >
        <MdiIcon
          :path="$globals.icons.foods"
          class="size-4"
        />
        {{ $t('recipe.parse') }}
      </Button>
    </div>
    <VueDraggable
      v-if="recipe.recipeIngredient.length > 0"
      v-model="recipe.recipeIngredient"
      handle=".handle"
      :delay="250"
      :delay-on-touch-only="true"
      class="flex flex-col gap-2"
      v-bind="{
        animation: 200,
        group: 'recipe-ingredients',
        disabled: false,
        ghostClass: 'ghost',
      }"
      @start="drag = true"
      @end="drag = false"
    >
      <RecipeIngredientEditor
        v-for="(ingredient, index) in recipe.recipeIngredient"
        :key="ingredient.referenceId"
        v-model="recipe.recipeIngredient[index]"
        :is-recipe="ingredientIsRecipe(ingredient)"
        :autofocus="ingredient.referenceId === autofocusIngredientId"
        enable-drag-handle
        enable-context-menu
        @delete="recipe.recipeIngredient.splice(index, 1)"
        @insert-above="insertNewIngredient(index)"
        @insert-below="insertNewIngredient(index + 1)"
      />
    </VueDraggable>
    <p
      v-else
      class="m-0 rounded-card border border-dashed px-4 py-6 text-center text-sm text-muted-foreground"
    >
      {{ $t('recipe.no-ingredients-yet') }}
    </p>
    <div class="mt-4 flex flex-wrap justify-end gap-2">
      <RecipeDialogBulkAdd
        ref="domBulkAddDialog"
        class="display-none"
        @bulk-data="addIngredient"
      />
      <Button
        variant="ghost"
        @click="showBulkAdd"
      >
        <MdiIcon
          :path="$globals.icons.create"
          class="size-4"
        />
        {{ $t('new-recipe.bulk-add') }}
      </Button>
      <Button
        variant="outline"
        @click="addRecipe"
      >
        <MdiIcon
          :path="$globals.icons.silverwareForkKnife"
          class="size-4"
        />
        {{ $t('new-recipe.add-recipe') }}
      </Button>
      <Button @click="addIngredient">
        <PlusIcon class="size-4" />
        {{ $t('new-recipe.add-food') }}
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { PlusIcon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { VueDraggable } from "vue-draggable-plus";
import type { RecipeOut, RecipeIngredient } from "~/lib/api/types/recipe";
import RecipeIngredientEditor from "~/components/Domain/Recipe/RecipeIngredientEditor.vue";
import RecipeDialogBulkAdd from "~/components/Domain/Recipe/RecipeDialogBulkAdd.vue";
import { usePageState } from "~/composables/recipe-page/shared-state";
import { uuid4 } from "~/composables/use-utils";

const recipe = defineModel<RecipeOut>({ required: true });
const ingredientsWithRecipe = new Map<string, boolean>();

const drag = ref(false);
// a row added one at a time takes focus so the user can type straight into it
const autofocusIngredientId = ref<string | null>(null);
const domBulkAddDialog = ref<InstanceType<typeof RecipeDialogBulkAdd> | null>(null);
const { toggleIsParsing } = usePageState(recipe.value.slug);

const hasFoodOrUnit = computed(() => {
  if (!recipe.value) {
    return false;
  }
  if (recipe.value.recipeIngredient) {
    for (const ingredient of recipe.value.recipeIngredient) {
      if (ingredient.food || ingredient.unit) {
        return true;
      }
    }
  }
  return false;
});

function showBulkAdd() {
  domBulkAddDialog.value?.open();
}

function ingredientIsRecipe(ingredient: RecipeIngredient): boolean {
  if (ingredient.referencedRecipe) {
    return true;
  }

  if (ingredient.referenceId) {
    return !!ingredientsWithRecipe.get(ingredient.referenceId);
  }

  return false;
}

function addIngredient(ingredients: Array<string> | null = null) {
  if (ingredients?.length) {
    const newIngredients = ingredients.map((x) => {
      return {
        referenceId: uuid4(),
        title: "",
        note: x,
        unit: undefined,
        food: undefined,
        quantity: 0,
      };
    });

    if (newIngredients) {
      recipe.value.recipeIngredient.push(...newIngredients);
    }
  }
  else {
    const referenceId = uuid4();
    autofocusIngredientId.value = referenceId;
    recipe.value.recipeIngredient.push({
      referenceId,
      title: "",
      note: "",
      unit: undefined,
      food: undefined,
      quantity: 0,
    });
  }
}

function addRecipe(recipes: Array<string> | null = null) {
  const refId = uuid4();
  ingredientsWithRecipe.set(refId, true);

  if (recipes?.length) {
    const newRecipes = recipes.map((x) => {
      return {
        referenceId: refId,
        title: "",
        note: x,
        unit: undefined,
        referencedRecipe: undefined,
        quantity: 1,
      };
    });

    if (newRecipes) {
      recipe.value.recipeIngredient.push(...newRecipes);
    }
  }
  else {
    autofocusIngredientId.value = refId;
    recipe.value.recipeIngredient.push({
      referenceId: refId,
      title: "",
      note: "",
      unit: undefined,
      referencedRecipe: undefined,
      quantity: 1,
    });
  }
}

function insertNewIngredient(dest: number) {
  const referenceId = uuid4();
  autofocusIngredientId.value = referenceId;
  recipe.value.recipeIngredient.splice(dest, 0, {
    referenceId,
    title: "",
    note: "",
    unit: undefined,
    food: undefined,
    quantity: 0,
  });
}
</script>
