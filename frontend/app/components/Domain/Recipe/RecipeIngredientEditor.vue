<template>
  <div class="font-sans">
    <input
      v-if="titleVisible"
      v-model="model.title"
      type="text"
      :placeholder="$t('recipe.section-title')"
      :aria-label="$t('recipe.section-title')"
      class="mb-1 mt-3 h-9 w-full max-w-md border-0 border-b border-input bg-transparent px-1 text-[15px] font-semibold outline-none placeholder:font-normal placeholder:text-muted-foreground/80 focus:border-ring"
      @click="$emit('clickIngredientField', 'title')"
    >
    <div class="flex items-start gap-1">
      <button
        v-if="enableDragHandle"
        type="button"
        class="handle inline-flex h-10 w-7 shrink-0 cursor-grab touch-none items-center justify-center rounded-item text-muted-foreground hover:bg-highlight hover:text-foreground active:cursor-grabbing"
        :aria-label="$t('general.drag-to-reorder')"
        :title="$t('general.drag-to-reorder')"
      >
        <GripVerticalIcon class="size-4" />
      </button>
      <div class="grid min-w-0 flex-1 grid-cols-[5rem_minmax(0,1fr)] gap-2 lg:grid-cols-[5rem_minmax(7rem,9rem)_minmax(0,1fr)_minmax(0,1.4fr)]">
        <input
          ref="quantityInput"
          type="number"
          inputmode="decimal"
          min="0"
          step="any"
          :value="model.quantity ?? ''"
          :placeholder="$t('recipe.quantity')"
          :aria-label="$t('recipe.quantity')"
          class="h-10 w-full min-w-0 rounded-control border border-input bg-card px-3 text-[15px] tabular-nums outline-none [appearance:textfield] placeholder:text-muted-foreground/80 focus:border-ring focus:ring-3 focus:ring-ring/25 [&::-webkit-inner-spin-button]:appearance-none"
          @keydown="quantityFilter"
          @input="onQuantityInput"
        >
        <SearchSelect
          v-model="model.unit"
          v-model:search="unitSearch"
          :items="filteredUnits"
          :placeholder="$t('recipe.choose-unit')"
          :warning="unitError ? (unitErrorTooltip || ' ') : undefined"
          creatable
          @create="createAssignUnit"
        />
        <SearchSelect
          v-if="!state.isRecipe"
          v-model="model.food"
          v-model:search="foodSearch"
          class="col-span-2 lg:col-span-1"
          :items="filteredFoods"
          :placeholder="$t('recipe.choose-food')"
          :warning="foodError ? (foodErrorTooltip || ' ') : undefined"
          creatable
          @create="createAssignFood"
        />
        <SearchSelect
          v-else
          v-model="model.referencedRecipe"
          v-model:search="search.query.value"
          class="col-span-2 lg:col-span-1"
          :items="search.data.value || []"
          :placeholder="$t('recipe.choose-recipe')"
          :empty-text="$t('search.type-to-search')"
          @focus="search.trigger()"
        />
        <input
          v-model="model.note"
          type="text"
          :placeholder="$t('recipe.notes')"
          :aria-label="$t('recipe.notes')"
          class="col-span-2 h-10 w-full min-w-0 rounded-control border border-input bg-card px-3 text-[15px] outline-none placeholder:text-muted-foreground/80 focus:border-ring focus:ring-3 focus:ring-ring/25 lg:col-span-1"
          @click="$emit('clickIngredientField', 'note')"
        >
      </div>
      <template v-if="enableContextMenu">
        <DropdownMenu :modal="false">
          <DropdownMenuTrigger as-child>
            <Button
              variant="ghost"
              size="icon"
              class="shrink-0"
              :aria-label="$t('general.menu')"
            >
              <EllipsisVerticalIcon class="size-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            align="end"
            class="min-w-52"
          >
            <DropdownMenuItem
              v-for="option in contextMenuOptions"
              :key="option.event"
              @select="onMenu(option.event)"
            >
              {{ option.text }}
            </DropdownMenuItem>
            <DropdownMenuItem
              variant="destructive"
              class="sm:display-none"
              :disabled="deleteDisabled"
              @select="$emit('delete')"
            >
              {{ $t("general.delete") }}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
        <Button
          variant="ghost"
          size="icon"
          class="shrink-0 text-muted-foreground hover:text-destructive max-sm:display-none"
          :disabled="deleteDisabled"
          :aria-label="$t('general.delete')"
          :title="$t('general.delete')"
          @click="$emit('delete')"
        >
          <Trash2Icon class="size-4" />
        </Button>
      </template>
    </div>
    <div :class="enableDragHandle && 'ps-8'">
      <!-- shown whenever the ingredient carries substitutions, so the toggle can't hide saved data -->
      <div
        v-if="substitutionsVisible"
        class="mt-2 rounded-control bg-muted/60 p-3"
      >
        <div class="mb-2 flex items-center gap-1.5 text-xs font-semibold text-muted-foreground">
          <MdiIcon
            :path="$globals.icons.swapHorizontal"
            class="size-4"
          />
          {{ $t("recipe.substitutions") }}
        </div>
        <RecipeIngredientSubstitutionEditor
          :substitutions="model.substitutions || []"
          :foods="allFoods"
          @add="addSubstitution"
          @delete="deleteSubstitution"
        />
      </div>
      <slot name="before-divider" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { EllipsisVerticalIcon, GripVerticalIcon, Trash2Icon } from "@lucide/vue";
import { computed, nextTick, onMounted, reactive, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { Button } from "~/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "~/components/ui/dropdown-menu";
import { MdiIcon } from "~/components/ui/mdi-icon";
import SearchSelect from "~/components/ui/field/SearchSelect.vue";
import { usePublicExploreApi, useUserApi } from "~/composables/api";
import { useRecipeSearch } from "~/composables/recipes/use-recipe-search";
import { useFoodData, useFoodStore, useUnitData, useUnitStore } from "~/composables/store";
import { useSearch } from "~/composables/use-search";
import RecipeIngredientSubstitutionEditor from "~/components/Domain/Recipe/RecipeIngredientSubstitutionEditor.vue";
import type { RecipeIngredient } from "~/lib/api/types/recipe";

// defineModel replaces modelValue prop
const model = defineModel<RecipeIngredient>({ required: true });

const props = defineProps({
  menuAttachTarget: {
    type: String,
    default: "body",
  },
  isRecipe: {
    type: Boolean,
    default: false,
  },
  unitError: {
    type: Boolean,
    default: false,
  },
  unitErrorTooltip: {
    type: String,
    default: "",
  },
  foodError: {
    type: Boolean,
    default: false,
  },
  foodErrorTooltip: {
    type: String,
    default: "",
  },
  enableContextMenu: {
    type: Boolean,
    default: false,
  },
  enableDragHandle: {
    type: Boolean,
    default: false,
  },
  deleteDisabled: {
    type: Boolean,
    default: false,
  },
  autofocus: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits([
  "clickIngredientField",
  "insert-above",
  "insert-below",
  "delete",
]);

const i18n = useI18n();

const state = reactive({
  showTitle: false,
  showSubstitutions: false,
  isRecipe: props.isRecipe,
});

// an ingredient that arrives with a title or substitutions shows them without being toggled on,
// so what the menu entries act on is this, not the flag on its own -- otherwise the first press
// is a no-op and the second one is the destructive half of a toggle nobody saw move
const titleVisible = computed(() => !!model.value.title || state.showTitle);
const substitutionsVisible = computed(() => !!model.value.substitutions?.length || state.showSubstitutions);

const contextMenuOptions = computed(() => {
  // these entries clear what they hide, so they name the action instead of saying "toggle"
  const options = [
    {
      text: titleVisible.value
        ? i18n.t("recipe.clear-section")
        : i18n.t("recipe.add-section"),
      event: "toggle-section",
    },
    {
      text: state.isRecipe ? i18n.t("recipe.use-food-instead") : i18n.t("recipe.use-recipe-instead"),
      event: "toggle-subrecipe",
    },
    {
      text: substitutionsVisible.value
        ? i18n.t("recipe.clear-substitutions")
        : i18n.t("recipe.add-substitutions"),
      event: "toggle-substitutions",
    },
    {
      text: i18n.t("recipe.insert-above"),
      event: "insert-above",
    },
    {
      text: i18n.t("recipe.insert-below"),
      event: "insert-below",
    },
  ];

  return options;
});

function onMenu(event: string) {
  switch (event) {
    case "toggle-section":
      toggleTitle();
      break;
    case "toggle-subrecipe":
      toggleIsRecipe();
      break;
    case "toggle-substitutions":
      toggleSubstitutions();
      break;
    case "insert-above":
      emit("insert-above");
      break;
    case "insert-below":
      emit("insert-below");
      break;
  }
}

// Foods
const foodStore = useFoodStore();
const foodData = useFoodData();
const { search: foodSearch, filtered: filteredFoods } = useSearch(foodStore.store);

// the substitution pickers offer every food; unlike the main field they can't create one,
// since a substitute the user has to invent is what the note is for
const allFoods = computed(() => foodStore.store.value);

async function createAssignFood(name?: string) {
  foodData.data.name = name || foodSearch.value;
  model.value.food = await foodStore.actions.createOne(foodData.data) || undefined;
  foodData.reset();
  foodSearch.value = "";
}

// Recipes
const route = useRoute();
const auth = useMealieAuth();
const groupSlug = computed(() => route.params.groupSlug as string || auth.user.value?.groupSlug || "");

const { isOwnGroup } = useLoggedInState();
const api = isOwnGroup.value ? useUserApi() : usePublicExploreApi(groupSlug.value).explore;
const search = useRecipeSearch(api);
const loading = ref(false);
const selectedIndex = ref(-1);
// Reset or Grab Recipes on Change
watch(loading, (val) => {
  if (!val) {
    search.query.value = "";
    selectedIndex.value = -1;
    search.data.value = [];
  }
});

// Units
const unitStore = useUnitStore();
const unitsData = useUnitData();
const { search: unitSearch, filtered: filteredUnits } = useSearch(unitStore.store);

async function createAssignUnit(name?: string) {
  unitsData.data.name = name || unitSearch.value;
  model.value.unit = await unitStore.actions.createOne(unitsData.data) || undefined;
  unitsData.reset();
  unitSearch.value = "";
}

function toggleTitle() {
  if (titleVisible.value) {
    model.value.title = "";
    state.showTitle = false;
  }
  else {
    state.showTitle = true;
  }
}

function addSubstitution() {
  model.value.substitutions = [...(model.value.substitutions || []), { substituteFoodId: null, note: "" }];
  state.showSubstitutions = true;
}

function deleteSubstitution(index: number) {
  model.value.substitutions?.splice(index, 1);
  // removing the last row leaves the section open; the user is still working in it
  state.showSubstitutions = true;
}

function toggleSubstitutions() {
  if (substitutionsVisible.value) {
    model.value.substitutions = [];
    state.showSubstitutions = false;
  }
  else {
    addSubstitution();
  }
}

function toggleIsRecipe() {
  if (state.isRecipe) {
    model.value.referencedRecipe = undefined;
  }
  else {
    model.value.unit = undefined;
    model.value.food = undefined;
  }
  state.isRecipe = !state.isRecipe;
}

// a new row focuses its quantity with the text selected, so typing replaces it
const quantityInput = ref<HTMLInputElement>();
onMounted(() => {
  if (props.autofocus) {
    nextTick(() => {
      quantityInput.value?.focus();
      quantityInput.value?.select();
    });
  }
});

function onQuantityInput(event: Event) {
  const raw = (event.target as HTMLInputElement).value;
  model.value.quantity = raw === "" ? null : Math.max(0, Number(raw));
}

function quantityFilter(e: KeyboardEvent) {
  if (e.key === "-" || e.key === "+" || e.key === "e") {
    e.preventDefault();
  }
}
</script>
