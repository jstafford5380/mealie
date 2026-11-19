<template>
  <div
    class="flex flex-col font-sans"
    :style="{ height }"
  >
    <label class="flex h-11 items-center gap-2 rounded-control border border-input bg-card px-3 focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/25">
      <SearchIcon class="size-4 shrink-0 text-muted-foreground" />
      <input
        ref="searchInput"
        v-model="search"
        type="search"
        :placeholder="$t('search.search-placeholder')"
        :aria-label="$t('search.search')"
        class="h-full min-w-0 flex-1 bg-transparent text-[15px] outline-none placeholder:text-muted-foreground/80"
      >
    </label>

    <div class="mt-3 flex flex-wrap items-center gap-2">
      <SearchFilter
        v-if="categories.length"
        v-model="selectedCategories"
        :items="categories"
      >
        {{ $t("category.categories") }}
      </SearchFilter>
      <SearchFilter
        v-if="tags.length"
        v-model="selectedTags"
        :items="tags"
      >
        {{ $t("tag.tags") }}
      </SearchFilter>
      <slot name="filters" />
    </div>

    <div
      v-if="modelValue"
      class="mt-3 flex items-center gap-2"
    >
      <span class="text-xs font-semibold text-muted-foreground">{{ $t("general.selected") }}</span>
      <span class="inline-flex h-8 max-w-full items-center gap-1.5 rounded-full bg-primary ps-3 pe-1 text-sm font-semibold text-primary-foreground">
        <span class="truncate">{{ modelValue.name }}</span>
        <button
          type="button"
          class="inline-flex size-6 items-center justify-center rounded-full hover:bg-black/15"
          :aria-label="`${$t('general.remove')}: ${modelValue.name}`"
          @click="select(null)"
        >
          <XIcon class="size-3.5" />
        </button>
      </span>
    </div>

    <div
      ref="resultsContainer"
      class="mt-3 min-h-40 flex-1 overflow-y-auto"
    >
      <div
        v-if="recipes.length"
        class="flex flex-col gap-0.5"
      >
        <RecipeCardLineItem
          v-for="recipe in recipes"
          :key="recipe.id"
          :recipe="recipe"
          :active="recipe.id === modelValue?.id"
          disable-link
          @click="select(recipe)"
        />
      </div>
      <div
        v-else-if="!loading"
        class="py-2"
      >
        <slot name="no-results">
          <p class="m-0 rounded-card border border-dashed px-4 py-6 text-center text-sm text-muted-foreground">
            {{ $t('search.no-results') }}
          </p>
        </slot>
      </div>
      <div ref="sentinel" />
      <div
        v-if="loading"
        class="flex justify-center py-3"
      >
        <span class="size-6 animate-spin rounded-full border-2 border-muted border-t-primary" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useIntersectionObserver, watchDebounced } from "@vueuse/core";
import { SearchIcon, XIcon } from "@lucide/vue";
import RecipeCardLineItem from "./RecipeCardLineItem.vue";
import SearchFilter from "~/components/Domain/SearchFilter.vue";
import { useLazyRecipes } from "~/composables/recipes";
import { useCategoryStore, useTagStore } from "~/composables/store";
import type { CategoryOut, RecipeSummary, TagOut } from "~/lib/api/types/recipe";
import type { RecipeSearchQuery } from "~/lib/api/user/recipes/recipe";

interface Props {
  queryFilter?: string | null;
  height?: string;
}
const props = withDefaults(defineProps<Props>(), {
  queryFilter: null,
  height: "100%",
});

const modelValue = defineModel<RecipeSummary | null>({ default: null });

const PER_PAGE = 20;

const { fetchMore } = useLazyRecipes();
const { store: categories } = useCategoryStore();
const { store: tags } = useTagStore();

const search = ref("");
const selectedCategories = ref<CategoryOut[]>([]);
const selectedTags = ref<TagOut[]>([]);

const recipes = ref<RecipeSummary[]>([]);
const page = ref(1);
const hasMore = ref(true);
const loading = ref(false);

// discards the results of any request that was superseded while it was in flight
let latestRequest = 0;

const query = computed<RecipeSearchQuery>(() => {
  return {
    search: search.value || "",
    categories: selectedCategories.value.map(category => category.id),
    tags: selectedTags.value.map(tag => tag.id),
  };
});

function select(recipe: RecipeSummary | null) {
  modelValue.value = recipe;
}

function reset() {
  search.value = "";
  selectedCategories.value = [];
  selectedTags.value = [];
}

defineExpose({ reset });

// the search box takes focus when the selector appears (in a dialog, after the dialog's own focus)
const searchInput = ref<HTMLInputElement | null>(null);
onMounted(() => requestAnimationFrame(() => searchInput.value?.focus()));

async function fetchPage(pageNumber: number, perPage: number) {
  return await fetchMore(pageNumber, perPage, "name", "asc", null, query.value, props.queryFilter);
}

async function reload() {
  const requestId = ++latestRequest;
  loading.value = true;

  // we double-up the first call so the results overflow their container,
  // otherwise there's nothing to scroll and no more recipes are ever loaded
  const newRecipes = await fetchPage(1, PER_PAGE * 2);
  if (requestId !== latestRequest) {
    return;
  }

  recipes.value = newRecipes;
  hasMore.value = newRecipes.length >= PER_PAGE * 2;
  page.value = 2;
  loading.value = false;
}

async function loadMore() {
  if (!hasMore.value || loading.value) {
    return;
  }

  const requestId = ++latestRequest;
  loading.value = true;
  page.value += 1;

  const newRecipes = await fetchPage(page.value, PER_PAGE);
  if (requestId !== latestRequest) {
    return;
  }

  recipes.value = [...recipes.value, ...newRecipes];
  hasMore.value = newRecipes.length >= PER_PAGE;
  loading.value = false;
}

const resultsContainer = ref<HTMLElement | null>(null);
const sentinel = ref<HTMLElement | null>(null);
useIntersectionObserver(
  sentinel,
  ([entry]) => {
    if (entry?.isIntersecting) {
      loadMore();
    }
  },
  { root: resultsContainer },
);

watchDebounced(
  [query, () => props.queryFilter],
  async () => {
    await reload();
  },
  { debounce: 300 },
);

onMounted(async () => {
  await reload();
});
</script>
