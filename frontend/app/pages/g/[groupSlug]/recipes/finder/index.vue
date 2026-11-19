<template>
  <div class="mx-auto w-full max-w-[1200px] px-4 pb-16 pt-3 font-sans sm:px-6 lg:pt-8">
    <BaseDialog
      v-model="state.queryFilterMenu"
      :title="$t('recipe-finder.other-filters')"
      :icon="$globals.icons.filter"
      width="100%"
      max-width="1100px"
      :submit-disabled="!state.queryFilterEditorValue"
      can-confirm
      @confirm="saveQueryFilter"
    >
      <div class="px-6 pb-2">
        <QueryFilterBuilder
          :key="state.queryFilterMenuKey"
          :initial-query-filter="state.queryFilterJSON"
          :field-defs="queryFilterBuilderFields"
          @input="(value) => state.queryFilterEditorValue = value"
          @input-j-s-o-n="(value) => state.queryFilterEditorValueJSON = value"
        />
      </div>
      <template #custom-card-action>
        <Button
          variant="ghost"
          class="text-destructive hover:text-destructive"
          @click="clearQueryFilter"
        >
          {{ $t("search.clear-selection") }}
        </Button>
      </template>
    </BaseDialog>

    <header class="mb-6">
      <h1 class="m-0 text-[26px] font-bold tracking-tight sm:text-[32px]">
        {{ $t('recipe-finder.recipe-finder') }}
      </h1>
      <p class="m-0 mt-1 max-w-[65ch] text-[15px] text-muted-foreground">
        {{ $t('recipe-finder.recipe-finder-description') }}
      </p>
    </header>

    <div
      v-if="state.ready"
      class="grid gap-6 lg:grid-cols-[300px_minmax(0,1fr)] lg:items-start"
    >
      <!-- what you have -->
      <aside class="flex flex-col gap-5 lg:sticky lg:top-20">
        <div class="flex flex-wrap gap-2">
          <SearchFilter
            v-if="foods"
            v-model="selectedFoods"
            :items="foods"
          >
            <MdiIcon
              :path="$globals.icons.foods"
              class="size-4"
            />
            {{ $t("general.foods") }}
          </SearchFilter>
          <SearchFilter
            v-if="tools"
            v-model="selectedTools"
            :items="tools"
          >
            <MdiIcon
              :path="$globals.icons.potSteam"
              class="size-4"
            />
            {{ $t("tool.tools") }}
          </SearchFilter>
          <button
            type="button"
            class="inline-flex h-9 items-center gap-2 rounded-full border px-3 text-sm font-medium transition-colors"
            :class="otherFilterCount ? 'border-primary bg-highlight text-highlight-foreground' : 'border-input bg-card hover:bg-highlight/60'"
            @click="state.queryFilterMenu = true"
          >
            <MdiIcon
              :path="$globals.icons.filter"
              class="size-4"
            />
            {{ $t("recipe-finder.other-filters") }}
            <span
              v-if="otherFilterCount"
              class="inline-flex min-w-5 items-center justify-center rounded-full bg-primary px-1.5 text-xs font-bold text-primary-foreground"
            >{{ otherFilterCount }}</span>
          </button>
          <Popover v-model:open="state.settingsMenu">
            <PopoverTrigger as-child>
              <button
                type="button"
                class="inline-flex h-9 items-center gap-2 rounded-full border border-input bg-card px-3 text-sm font-medium hover:bg-highlight/60"
              >
                <SlidersHorizontalIcon class="size-4" />
                {{ $t("general.settings") }}
              </button>
            </PopoverTrigger>
            <PopoverContent
              align="start"
              class="w-[min(320px,calc(100vw-2rem))]"
            >
              <div class="flex flex-col gap-1">
                <NumberInputField
                  v-model="maxMissingFoods"
                  :precision="null"
                  :min="0"
                  :label="$t('recipe-finder.max-missing-ingredients')"
                />
                <NumberInputField
                  v-model="maxMissingTools"
                  :precision="null"
                  :min="0"
                  :label="$t('recipe-finder.max-missing-tools')"
                />
                <CheckboxField
                  v-if="isOwnGroup"
                  v-model="state.settings.includeFoodsOnHand"
                  :label="$t('recipe-finder.include-ingredients-on-hand')"
                />
                <CheckboxField
                  v-if="isOwnGroup"
                  v-model="state.settings.includeToolsOnHand"
                  :label="$t('recipe-finder.include-tools-on-hand')"
                />
                <CheckboxField
                  v-model="state.settings.includeSubstitutions"
                  :label="$t('recipe-finder.include-substitutions')"
                />
              </div>
            </PopoverContent>
          </Popover>
        </div>

        <section>
          <h2 class="m-0 mb-2 text-sm font-semibold">
            {{ $t("recipe-finder.selected-ingredients") }}
          </h2>
          <p
            v-if="!selectedFoods.length"
            class="m-0 text-sm text-muted-foreground"
          >
            {{ $t("recipe-finder.no-ingredients-selected") }}
          </p>
          <div
            v-else
            class="flex max-h-[50vh] flex-wrap gap-1.5 overflow-y-auto"
          >
            <span
              v-for="food in selectedFoods"
              :key="food.id"
              class="inline-flex h-8 max-w-full items-center gap-1 rounded-full bg-highlight ps-3 pe-1 text-sm font-semibold text-highlight-foreground"
            >
              <span class="truncate">{{ food.pluralName || food.name }}</span>
              <button
                type="button"
                class="inline-flex size-6 items-center justify-center rounded-full hover:bg-background/40"
                :aria-label="$t('general.remove-item', { name: food.pluralName || food.name })"
                @click="removeFood(food)"
              >
                <XIcon class="size-3.5" />
              </button>
            </span>
          </div>
        </section>
        <section v-if="selectedTools.length">
          <h2 class="m-0 mb-2 text-sm font-semibold">
            {{ $t("recipe-finder.selected-tools") }}
          </h2>
          <div class="flex flex-wrap gap-1.5">
            <span
              v-for="tool in selectedTools"
              :key="tool.id"
              class="inline-flex h-8 max-w-full items-center gap-1 rounded-full bg-highlight ps-3 pe-1 text-sm font-semibold text-highlight-foreground"
            >
              <span class="truncate">{{ tool.name }}</span>
              <button
                type="button"
                class="inline-flex size-6 items-center justify-center rounded-full hover:bg-background/40"
                :aria-label="$t('general.remove-item', { name: tool.name })"
                @click="removeTool(tool)"
              >
                <XIcon class="size-3.5" />
              </button>
            </span>
          </div>
        </section>
      </aside>

      <!-- what you can make -->
      <div class="flex min-w-0 flex-col gap-6">
        <template v-if="recipeSuggestions.readyToMake.length || recipeSuggestions.missingItems.length">
          <section
            v-if="recipeSuggestions.readyToMake.length"
            class="flex flex-col gap-2"
          >
            <h2 class="m-0 text-lg font-bold">
              {{ $t("recipe-finder.ready-to-make") }}
              <span class="ms-1 text-sm font-normal text-muted-foreground tabular-nums">{{ recipeSuggestions.readyToMake.length }}</span>
            </h2>
            <RecipeSuggestion
              v-for="(item, idx) in recipeSuggestions.readyToMake"
              :key="`${idx}-ready`"
              :recipe="item.recipe"
              :missing-foods="item.missingFoods"
              :missing-tools="item.missingTools"
              :substituted-foods="item.substitutedFoods"
              :disable-checkbox="state.loading"
              @add-food="addFood"
              @remove-food="removeFood"
              @add-tool="addTool"
              @remove-tool="removeTool"
            />
          </section>
          <section
            v-if="recipeSuggestions.missingItems.length"
            class="flex flex-col gap-2"
          >
            <h2 class="m-0 text-lg font-bold">
              {{ $t("recipe-finder.almost-ready-to-make") }}
              <span class="ms-1 text-sm font-normal text-muted-foreground tabular-nums">{{ recipeSuggestions.missingItems.length }}</span>
            </h2>
            <RecipeSuggestion
              v-for="(item, idx) in recipeSuggestions.missingItems"
              :key="`${idx}-missing`"
              :recipe="item.recipe"
              :missing-foods="item.missingFoods"
              :missing-tools="item.missingTools"
              :substituted-foods="item.substitutedFoods"
              :disable-checkbox="state.loading"
              @add-food="addFood"
              @remove-food="removeFood"
              @add-tool="addTool"
              @remove-tool="removeTool"
            />
          </section>
        </template>
        <div
          v-else-if="!state.recipesReady"
          class="flex justify-center py-10"
        >
          <AppLoader :waiting-text="$t('general.loading-recipes')" />
        </div>
        <div
          v-else
          class="rounded-card border border-dashed px-4 py-10 text-center"
        >
          <p class="m-0 font-semibold">
            {{ $t("recipe-finder.no-recipes-found") }}
          </p>
          <p class="m-0 mt-1 text-sm text-muted-foreground">
            {{ $t("recipe-finder.no-recipes-found-description") }}
          </p>
        </div>
      </div>
    </div>
    <div
      v-else
      class="flex justify-center py-10"
    >
      <AppLoader :waiting-text="$t('general.loading-recipes')" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { SlidersHorizontalIcon, XIcon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import CheckboxField from "~/components/ui/field/CheckboxField.vue";
import NumberInputField from "~/components/ui/field/NumberInputField.vue";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { Popover, PopoverContent, PopoverTrigger } from "~/components/ui/popover";
import { watchDebounced } from "@vueuse/core";
import { useUserApi } from "~/composables/api";
import { usePublicExploreApi } from "~/composables/api/api-client";
import { useLoggedInState } from "~/composables/use-logged-in-state";
import { useFoodStore, usePublicFoodStore, useToolStore, usePublicToolStore } from "~/composables/store";
import type { IngredientFoodOut, RecipeSuggestionQuery, RecipeSuggestionResponseItem, ToolOut } from "~/lib/api/types/recipe";
import QueryFilterBuilder from "~/components/Domain/QueryFilterBuilder.vue";
import { useRecipeFilterFields } from "~/composables/use-recipe-filter-fields";
import RecipeSuggestion from "~/components/Domain/Recipe/RecipeSuggestion.vue";
import SearchFilter from "~/components/Domain/SearchFilter.vue";
import type { QueryFilterJSON } from "~/lib/api/types/non-generated";
import { useRecipeFinderPreferences } from "~/composables/use-users/preferences";
import { normalizeMissingItemLimit } from "~/lib/recipe/recipe-finder";

interface RecipeSuggestions {
  readyToMake: RecipeSuggestionResponseItem[];
  missingItems: RecipeSuggestionResponseItem[];
}

const i18n = useI18n();
const auth = useMealieAuth();
const route = useRoute();

useSeoMeta({
  title: i18n.t("recipe-finder.recipe-finder"),
});

const groupSlug = computed(() => route.params.groupSlug as string || auth.user.value?.groupSlug || "");
const { isOwnGroup } = useLoggedInState();
const api = isOwnGroup.value ? useUserApi() : usePublicExploreApi(groupSlug.value).explore;

const preferences = useRecipeFinderPreferences();
const state = reactive({
  ready: false,
  loading: false,
  recipesReady: false,
  settingsMenu: false,
  queryFilterMenu: false,
  queryFilterMenuKey: 0,
  queryFilterEditorValue: "",
  queryFilterEditorValueJSON: {},
  queryFilterJSON: preferences.value.queryFilterJSON,
  settings: {
    maxMissingFoods: normalizeMissingItemLimit(preferences.value.maxMissingFoods),
    maxMissingTools: normalizeMissingItemLimit(preferences.value.maxMissingTools),
    includeFoodsOnHand: preferences.value.includeFoodsOnHand,
    includeToolsOnHand: preferences.value.includeToolsOnHand,
    includeSubstitutions: preferences.value.includeSubstitutions,
    queryFilter: preferences.value.queryFilter,
    limit: 20,
  },
});

const maxMissingFoods = computed({
  get: () => state.settings.maxMissingFoods,
  set: (value) => {
    state.settings.maxMissingFoods = normalizeMissingItemLimit(value);
  },
});

const maxMissingTools = computed({
  get: () => state.settings.maxMissingTools,
  set: (value) => {
    state.settings.maxMissingTools = normalizeMissingItemLimit(value);
  },
});

onMounted(() => {
  if (!isOwnGroup.value) {
    state.settings.includeFoodsOnHand = false;
    state.settings.includeToolsOnHand = false;
  }
});

watch(
  () => state,
  (newState) => {
    preferences.value.queryFilter = newState.settings.queryFilter;
    preferences.value.queryFilterJSON = newState.queryFilterJSON;
    preferences.value.maxMissingFoods = newState.settings.maxMissingFoods;
    preferences.value.maxMissingTools = newState.settings.maxMissingTools;
    preferences.value.includeFoodsOnHand = newState.settings.includeFoodsOnHand;
    preferences.value.includeToolsOnHand = newState.settings.includeToolsOnHand;
    preferences.value.includeSubstitutions = newState.settings.includeSubstitutions;
  },
  {
    deep: true,
  },
);

const otherFilterCount = computed(() => (state.queryFilterJSON.parts || []).length);

const foodStore = isOwnGroup.value ? useFoodStore() : usePublicFoodStore(groupSlug.value);
const foods = computed(() => foodStore.store.value);
const selectedFoods = ref<IngredientFoodOut[]>([]);
function addFood(food: IngredientFoodOut) {
  selectedFoods.value = [...selectedFoods.value, food];
  handleFoodUpdates();
}
function removeFood(food: IngredientFoodOut) {
  selectedFoods.value = selectedFoods.value.filter(f => f.id !== food.id);
  handleFoodUpdates();
}
function handleFoodUpdates() {
  selectedFoods.value.sort((a, b) => (a.pluralName || a.name).localeCompare(b.pluralName || b.name));
  preferences.value.foodIds = selectedFoods.value.map(food => food.id);
}
watch(
  () => selectedFoods.value,
  () => {
    handleFoodUpdates();
  },
);

const toolStore = isOwnGroup.value ? useToolStore() : usePublicToolStore(groupSlug.value);
const tools = computed(() => toolStore.store.value);
const selectedTools = ref<ToolOut[]>([]);
function addTool(tool: ToolOut) {
  selectedTools.value = [...selectedTools.value, tool];
  handleToolUpdates();
}
function removeTool(tool: ToolOut) {
  selectedTools.value = selectedTools.value.filter(t => t.id !== tool.id);
  handleToolUpdates();
}
function handleToolUpdates() {
  selectedTools.value.sort((a, b) => a.name.localeCompare(b.name));
  preferences.value.toolIds = selectedTools.value.map(tool => tool.id);
}
watch(
  () => selectedTools.value,
  () => {
    handleToolUpdates();
  },
);

async function hydrateFoods() {
  if (!preferences.value.foodIds.length) {
    return;
  }
  if (!foodStore.store.value.length) {
    await foodStore.actions.refresh();
  }

  const foods = preferences.value.foodIds
    .map(foodId => foodStore.store.value.find(food => food.id === foodId))
    .filter(food => !!food);

  selectedFoods.value = foods;
}

async function hydrateTools() {
  if (!preferences.value.toolIds.length) {
    return;
  }
  if (!toolStore.store.value.length) {
    await toolStore.actions.refresh();
  }

  const tools = preferences.value.toolIds
    .map(toolId => toolStore.store.value.find(tool => tool.id === toolId))
    .filter(tool => !!tool);

  selectedTools.value = tools;
}

onMounted(async () => {
  await Promise.all([hydrateFoods(), hydrateTools()]);
  state.ready = true;
  if (!selectedFoods.value.length) {
    state.recipesReady = true;
  };
});

const recipeResponseItems = ref<RecipeSuggestionResponseItem[]>([]);
const recipeSuggestions = computed<RecipeSuggestions>(() => {
  const readyToMake: RecipeSuggestionResponseItem[] = [];
  const missingItems: RecipeSuggestionResponseItem[] = [];
  recipeResponseItems.value.forEach((responseItem) => {
    if (responseItem.missingFoods.length === 0 && responseItem.missingTools.length === 0) {
      readyToMake.push(responseItem);
    }
    else {
      missingItems.push(responseItem);
    };
  });

  return {
    readyToMake,
    missingItems,
  };
});

watchDebounced(
  [selectedFoods, selectedTools, state.settings], async () => {
    // don't search for suggestions if no filter are selected
    if (!selectedFoods.value.length && !selectedTools.value.length && !state.settings.queryFilter) {
      recipeResponseItems.value = [];
      state.recipesReady = true;
      return;
    }

    state.loading = true;
    const { data } = await api.recipes.getSuggestions(
      {
        limit: state.settings.limit,
        queryFilter: state.settings.queryFilter,
        maxMissingFoods: state.settings.maxMissingFoods,
        maxMissingTools: state.settings.maxMissingTools,
        includeFoodsOnHand: state.settings.includeFoodsOnHand,
        includeToolsOnHand: state.settings.includeToolsOnHand,
        includeSubstitutions: state.settings.includeSubstitutions,
      } as RecipeSuggestionQuery,
      selectedFoods.value.map(food => food.id),
      selectedTools.value.map(tool => tool.id),
    );
    state.loading = false;
    if (!data) {
      return;
    }
    recipeResponseItems.value = data.items;
    state.recipesReady = true;
  },
  {
    debounce: 500,
  },
);

// Tools are left out on purpose: the finder has its own tool picker with "max missing tools",
// and a second tool filter in the query builder would contradict it.
const queryFilterBuilderFields = useRecipeFilterFields({ exclude: ["tools.id"] });

function clearQueryFilter() {
  state.queryFilterEditorValue = "";
  state.queryFilterEditorValueJSON = { parts: [] } as QueryFilterJSON;
  state.settings.queryFilter = "";
  state.queryFilterJSON = { parts: [] } as QueryFilterJSON;
  state.queryFilterMenu = false;
  state.queryFilterMenuKey += 1;
}

function saveQueryFilter() {
  state.settings.queryFilter = state.queryFilterEditorValue || "";
  state.queryFilterJSON = state.queryFilterEditorValueJSON || { parts: [] } as QueryFilterJSON;
  state.queryFilterMenu = false;
}
</script>
