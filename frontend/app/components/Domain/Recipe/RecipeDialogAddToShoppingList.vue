<template>
  <div v-if="dialog">
    <!-- Step 1: pick a list -->
    <BaseDialog
      v-if="shoppingListDialog && ready"
      v-model="dialog"
      :title="$t('recipe.add-to-list')"
      :icon="$globals.icons.cartCheck"
    >
      <div class="flex flex-col gap-2 px-6 pb-2 font-sans">
        <p
          v-if="!filteredShoppingLists.length && !newListForm.show"
          class="m-0 rounded-card border border-dashed px-4 py-6 text-center text-sm text-muted-foreground"
        >
          {{ $t('shopping-list.no-shopping-lists-found') }}
        </p>
        <button
          v-for="list in filteredShoppingLists"
          :key="list.id"
          type="button"
          class="flex items-center gap-3 rounded-card border bg-card px-4 py-3 text-left text-[15px] font-medium transition-colors hover:border-primary/40 hover:bg-highlight/60"
          @click="openShoppingListIngredientDialog(list)"
        >
          <MdiIcon
            :path="$globals.icons.cartCheck"
            class="size-5 text-primary"
          />
          <span class="min-w-0 flex-1 truncate">{{ list.name }}</span>
          <ChevronRightIcon class="size-4 text-muted-foreground" />
        </button>
        <form
          v-if="newListForm.show"
          class="mt-2 flex flex-col gap-2"
          @submit.prevent="createAndOpenList"
        >
          <TextField
            v-model="newListForm.name"
            :label="$t('shopping-list.new-list-name')"
            autofocus
          />
          <div class="flex justify-end gap-2">
            <Button
              variant="ghost"
              @click="resetNewListForm"
            >
              {{ $t("general.cancel") }}
            </Button>
            <Button
              type="submit"
              :disabled="!newListForm.name.trim() || newListForm.loading"
            >
              {{ $t("general.create") }}
            </Button>
          </div>
        </form>
      </div>
      <template #card-actions>
        <div class="flex w-full flex-wrap items-center gap-3">
          <Button
            variant="ghost"
            @click="dialog = false"
          >
            {{ $t("general.cancel") }}
          </Button>
          <label class="ms-auto flex cursor-pointer items-center gap-2 text-sm">
            <Checkbox
              :model-value="preferences.viewAllLists"
              @update:model-value="preferences.viewAllLists = !!$event; setShowAllToggled()"
            />
            {{ $t('general.show-all') }}
          </label>
          <Button
            v-if="!newListForm.show"
            variant="outline"
            @click="newListForm.show = true"
          >
            <PlusIcon class="size-4" />
            {{ $t("shopping-list.new-list") }}
          </Button>
        </div>
      </template>
    </BaseDialog>

    <!-- Step 2: choose the ingredients -->
    <BaseDialog
      v-if="shoppingListIngredientDialog"
      v-model="dialog"
      :title="selectedShoppingList?.name || $t('recipe.add-to-list')"
      :icon="$globals.icons.cartCheck"
      width="70%"
      :submit-text="$t('recipe.add-to-list')"
      can-submit
      @submit="addRecipesToList()"
    >
      <div class="flex max-h-[65vh] flex-col gap-5 overflow-y-auto px-6 pb-2 font-sans">
        <div class="flex flex-wrap justify-end gap-2">
          <Button
            variant="ghost"
            size="sm"
            @click="bulkCheckIngredients(false)"
          >
            <MdiIcon
              :path="$globals.icons.checkboxMultipleBlankOutline"
              class="size-4"
            />
            {{ $t('shopping-list.uncheck-all-items') }}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            @click="bulkCheckIngredients(true)"
          >
            <MdiIcon
              :path="$globals.icons.checkboxMultipleMarkedOutline"
              class="size-4"
            />
            {{ $t('shopping-list.check-all-items') }}
          </Button>
        </div>
        <section
          v-for="(recipeSection, recipeSectionIndex) in recipeIngredientSections"
          :key="recipeSection.recipeId + recipeSectionIndex"
          :class="recipeSectionIndex > 0 && 'border-t pt-4'"
        >
          <h3
            v-if="recipeIngredientSections.length > 1"
            class="m-0 mb-2 flex flex-wrap items-baseline gap-2 font-serif text-xl font-normal"
          >
            {{ recipeSection.recipeName }}
            <span
              v-if="recipeSection.parentRecipe?.name"
              class="font-sans text-xs font-semibold text-muted-foreground"
            >{{ $t("shopping-list.ingredient-of-recipe", { recipe: recipeSection.parentRecipe.name }) }}</span>
            <span
              v-if="recipeSection.recipeScale > 1"
              class="font-sans text-sm text-muted-foreground"
            >× {{ recipeSection.recipeScale }}</span>
          </h3>
          <div
            v-for="(ingredientSection, ingredientSectionIndex) in recipeSection.ingredientSections"
            :key="recipeSection.recipeId + recipeSectionIndex + ingredientSectionIndex"
          >
            <h4
              v-if="ingredientSection.sectionName"
              class="m-0 mb-1 mt-3 text-sm font-semibold text-muted-foreground"
            >
              {{ ingredientSection.sectionName }}
            </h4>
            <div class="grid grid-cols-1 gap-x-6 md:grid-cols-2">
              <label
                v-for="(ingredientData, i) in ingredientSection.ingredients"
                :key="recipeSection.recipeId + recipeSectionIndex + ingredientSectionIndex + i"
                class="flex cursor-pointer items-start gap-3 rounded-item px-1 py-1.5 hover:bg-highlight/50"
              >
                <Checkbox
                  v-model="ingredientData.checked"
                  class="mt-0.5 size-5 shrink-0"
                />
                <RecipeIngredientListItem
                  :key="`${ingredientData.ingredient?.quantity || 'no-qty'}-${i}`"
                  class="min-w-0 flex-1"
                  :class="!ingredientData.checked && 'opacity-50'"
                  :ingredient="ingredientData.ingredient"
                  :scale="recipeSection.recipeScale"
                />
              </label>
            </div>
          </div>
        </section>
      </div>
    </BaseDialog>
  </div>
</template>

<script setup lang="ts">
import { ChevronRightIcon, PlusIcon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import { Checkbox } from "~/components/ui/checkbox";
import TextField from "~/components/ui/field/TextField.vue";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { toRefs } from "@vueuse/core";
import { useUserApi } from "~/composables/api";
import { useNewShoppingListForm } from "~/composables/shopping-list-page/use-add-to-shopping-list-dialog";
import { alert } from "~/composables/use-toast";
import { useShoppingListPreferences } from "~/composables/use-users/preferences";
import type { RecipeIngredient, ShoppingListAddRecipeParamsBulk, ShoppingListSummary } from "~/lib/api/types/household";
import type { RecipeOut, RecipeDraft, RecipeSummary } from "~/lib/api/types/recipe";
import RecipeIngredientListItem from "./RecipeIngredientListItem.vue";

/** Ingredients are fetched on demand when the caller only has a summary. */
export type RecipeWithScale = RecipeSummary & {
  recipeIngredient?: RecipeOut["recipeIngredient"];
  scale: number;
};

export interface ShoppingListIngredient {
  checked: boolean;
  ingredient: RecipeIngredient;
}

export interface ShoppingListIngredientSection {
  sectionName: string;
  ingredients: ShoppingListIngredient[];
}

export interface ShoppingListRecipeIngredientSection {
  recipeId: string;
  recipeName: string;
  recipeScale: number;
  ingredientSections: ShoppingListIngredientSection[];
  parentRecipe?: Pick<RecipeDraft, "name">;
}

interface Props {
  recipes?: RecipeWithScale[];
  shoppingLists?: ShoppingListSummary[];
}
const props = withDefaults(defineProps<Props>(), {
  recipes: undefined,
  shoppingLists: () => [],
});

const emit = defineEmits<{
  "list-created": [list: ShoppingListSummary];
}>();

const dialog = defineModel<boolean>({ default: false });

const i18n = useI18n();
const auth = useMealieAuth();
const api = useUserApi();
const preferences = useShoppingListPreferences();
const router = useRouter();
const { form: newListForm, reset: resetNewListForm, create: createShoppingList } = useNewShoppingListForm();
const ready = ref(false);

// Capture values at initialization to avoid reactive updates
const currentHouseholdSlug = ref("");
const filteredShoppingLists = ref<ShoppingListSummary[]>([]);

const state = reactive({
  shoppingListDialog: false,
  shoppingListIngredientDialog: false,
  shoppingListShowAllToggled: false,
});

const { shoppingListDialog, shoppingListIngredientDialog, shoppingListShowAllToggled: _shoppingListShowAllToggled } = toRefs(state);

const recipeIngredientSections = ref<ShoppingListRecipeIngredientSection[]>([]);
const selectedShoppingList = ref<ShoppingListSummary | null>(null);

watch([dialog, () => preferences.value.viewAllLists], () => {
  if (dialog.value) {
    currentHouseholdSlug.value = auth.user.value?.householdSlug || "";
    filteredShoppingLists.value = props.shoppingLists.filter(
      list => preferences.value.viewAllLists || list.userId === auth.user.value?.id,
    );

    if (filteredShoppingLists.value.length === 1 && !state.shoppingListShowAllToggled) {
      selectedShoppingList.value = filteredShoppingLists.value[0];
      openShoppingListIngredientDialog(selectedShoppingList.value);
    }
    else {
      state.shoppingListDialog = true;
      ready.value = true;
    }
  }
  else if (!dialog.value) {
    initState();
  }
});

function buildIngredientSections(ingredients: ShoppingListIngredient[]): ShoppingListIngredientSection[] {
  let currentTitle = "";
  const onHandIngs: ShoppingListIngredient[] = [];
  const sections = ingredients.reduce((acc, ing) => {
    if (ing.ingredient.title) {
      currentTitle = ing.ingredient.title;
    }

    if (!acc.length || currentTitle !== acc[acc.length - 1].sectionName) {
      if (acc.length) {
        acc[acc.length - 1].ingredients.push(...onHandIngs);
        onHandIngs.length = 0;
      }
      acc.push({ sectionName: currentTitle, ingredients: [] });
    }

    const householdsWithFood = ing.ingredient?.food?.householdsWithIngredientFood || [];
    if (householdsWithFood.includes(currentHouseholdSlug.value)) {
      onHandIngs.push(ing);
      return acc;
    }

    acc[acc.length - 1].ingredients.push(ing);
    return acc;
  }, [] as ShoppingListIngredientSection[]);

  if (sections.length) {
    sections[sections.length - 1].ingredients.push(...onHandIngs);
  }
  return sections;
}

async function consolidateRecipesIntoSections(recipes: RecipeWithScale[]) {
  const recipeSectionMap = new Map<string, ShoppingListRecipeIngredientSection>();

  function addSubRecipeToMap(ing: RecipeIngredient, parentQuantity: number, parentScale: number, parentRecipe: Pick<RecipeDraft, "name">) {
    const subRecipe = ing.referencedRecipe!;
    const key = subRecipe.id || subRecipe.slug || "";
    const ownIngs: ShoppingListIngredient[] = [];
    const subRefIngs: RecipeIngredient[] = [];

    for (const subIng of subRecipe.recipeIngredient ?? []) {
      if (subIng.referencedRecipe) {
        subRefIngs.push(subIng);
      }
      else {
        const householdsWithFood = subIng.food?.householdsWithIngredientFood || [];
        ownIngs.push({
          checked: !householdsWithFood.includes(currentHouseholdSlug.value),
          ingredient: subIng,
        });
      }
    }

    recipeSectionMap.set(key, {
      recipeId: subRecipe.id || "",
      recipeName: subRecipe.name || "",
      recipeScale: parentQuantity * parentScale,
      ingredientSections: buildIngredientSections(ownIngs),
      parentRecipe,
    });

    subRefIngs.forEach(subIng => addSubRecipeToMap(subIng, (ing.quantity || 1) * (subIng.quantity || 1), parentScale, subRecipe));
  }

  for (const recipe of recipes) {
    if (!recipe.slug) {
      continue;
    }

    if (recipeSectionMap.has(recipe.slug)) {
      const existingSection = recipeSectionMap.get(recipe.slug);
      if (existingSection) {
        existingSection.recipeScale += recipe.scale;
      }
      continue;
    }

    let recipeData: RecipeOut | RecipeWithScale = recipe;
    if (!(recipe.id && recipe.name && recipe.recipeIngredient)) {
      const { data } = await api.recipes.getOne(recipe.slug);
      if (!data) {
        continue;
      }
      recipeData = data;
    }

    const recipeIngredient = recipeData.recipeIngredient ?? [];
    if (!recipeIngredient.length) {
      continue;
    }

    const ownIngs: ShoppingListIngredient[] = [];
    const subRefIngs: RecipeIngredient[] = [];
    recipeIngredient.forEach((ing) => {
      if (ing.referencedRecipe) {
        subRefIngs.push(ing);
      }
      else {
        const householdsWithFood = ing.food?.householdsWithIngredientFood || [];
        ownIngs.push({
          checked: !householdsWithFood.includes(currentHouseholdSlug.value),
          ingredient: ing,
        });
      }
    });

    recipeSectionMap.set(recipe.slug, {
      recipeId: recipeData.id,
      recipeName: recipeData.name,
      recipeScale: recipe.scale,
      ingredientSections: buildIngredientSections(ownIngs),
    });

    subRefIngs.forEach(ing => addSubRecipeToMap(ing, ing.quantity || 1, recipe.scale, recipeData));
  }

  recipeIngredientSections.value = Array.from(recipeSectionMap.values());
}

async function createAndOpenList() {
  const list = await createShoppingList();
  if (!list) {
    return;
  }

  filteredShoppingLists.value.push(list);
  // the parent owns `shoppingLists`, which this dialog re-filters from every time it's opened
  emit("list-created", list);

  await openShoppingListIngredientDialog(list);
}

function initState() {
  state.shoppingListDialog = false;
  state.shoppingListIngredientDialog = false;
  state.shoppingListShowAllToggled = false;
  recipeIngredientSections.value = [];
  selectedShoppingList.value = null;
  resetNewListForm();
}

initState();

async function openShoppingListIngredientDialog(list: ShoppingListSummary) {
  if (!props.recipes?.length) {
    return;
  }

  selectedShoppingList.value = list;
  await consolidateRecipesIntoSections(props.recipes);
  state.shoppingListDialog = false;
  state.shoppingListIngredientDialog = true;
}

function setShowAllToggled() {
  state.shoppingListShowAllToggled = true;
}

function bulkCheckIngredients(value = true) {
  recipeIngredientSections.value.forEach((recipeSection) => {
    recipeSection.ingredientSections.forEach((ingSection) => {
      ingSection.ingredients.forEach((ing) => {
        ing.checked = value;
      });
    });
  });
}

async function addRecipesToList() {
  if (!selectedShoppingList.value) {
    return;
  }

  const recipeData: ShoppingListAddRecipeParamsBulk[] = [];
  recipeIngredientSections.value.forEach((section) => {
    const ingredients: RecipeIngredient[] = [];
    section.ingredientSections.forEach((ingSection) => {
      ingSection.ingredients.forEach((ing) => {
        if (ing.checked) {
          ingredients.push(ing.ingredient);
        }
      });
    });

    if (!ingredients.length) {
      return;
    }

    recipeData.push(
      {
        recipeId: section.recipeId,
        recipeIncrementQuantity: section.recipeScale,
        recipeIngredients: ingredients,
      },
    );
  });
  const listId = selectedShoppingList.value.id;
  const { error } = await api.shopping.lists.addRecipes(listId, recipeData);
  // eslint-disable-next-line @typescript-eslint/no-unused-expressions
  error
    ? alert.error(i18n.t("recipe.failed-to-add-recipes-to-list"))
    : alert.success(i18n.t("recipe.successfully-added-to-list"), null, {
        action: {
          message: i18n.t("general.view"),
          onClick: () => router.push(`/shopping-lists/${listId ?? ""}`),
        },
      });

  state.shoppingListDialog = false;
  state.shoppingListIngredientDialog = false;
  dialog.value = false;
}
</script>
