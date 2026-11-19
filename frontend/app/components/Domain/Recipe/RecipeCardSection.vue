<template>
  <section class="flex flex-col gap-4 font-sans">
    <div
      v-if="!disableToolbar"
      class="flex flex-wrap items-center gap-2"
    >
      <h2
        v-if="title"
        class="m-0 me-auto flex min-w-0 items-center gap-2 text-xl font-bold tracking-tight text-foreground"
      >
        <MdiIcon
          v-if="icon"
          :path="displayTitleIcon"
          class="size-5 text-muted-foreground"
        />
        <span class="truncate">{{ title }}</span>
      </h2>
      <span
        v-else
        class="me-auto"
      />
      <Button
        variant="outline"
        :disabled="recipes.length === 0"
        @click="navigateRandom"
      >
        <MdiIcon
          :path="$globals.icons.diceMultiple"
          class="size-[18px]"
        />
        <span class="max-sm:sr-only">{{ $t("general.random") }}</span>
      </Button>
      <DropdownMenu
        v-if="!disableSort"
        :modal="false"
      >
        <DropdownMenuTrigger as-child>
          <Button
            variant="outline"
            :disabled="sortLoading"
          >
            <MdiIcon
              :path="sortIcon"
              class="size-[18px]"
            />
            <span class="max-sm:sr-only">{{ $t("general.sort") }}</span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent
          align="end"
          class="min-w-52"
        >
          <DropdownMenuItem
            v-for="option in sortOptions"
            :key="option.event"
            :class="option.active && 'font-semibold'"
            @select="sortRecipes(option.event)"
          >
            <MdiIcon :path="option.icon" />
            <span class="flex-1">{{ option.label }}</span>
            <span
              v-if="option.active"
              class="text-xs text-muted-foreground"
            >{{ preferences.orderDirection === "asc" ? "↑" : "↓" }}</span>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
      <div
        role="group"
        :aria-label="$t('general.toggle-view')"
        class="flex rounded-control border border-input bg-card p-0.5"
      >
        <button
          type="button"
          :aria-pressed="!useMobileCards"
          :aria-label="$t('general.grid-view')"
          class="inline-flex size-9 items-center justify-center rounded-item text-muted-foreground aria-pressed:bg-highlight aria-pressed:text-highlight-foreground"
          @click="setListView(false)"
        >
          <LayoutGridIcon class="size-[18px]" />
        </button>
        <button
          type="button"
          :aria-pressed="useMobileCards"
          :aria-label="$t('general.list-view')"
          class="inline-flex size-9 items-center justify-center rounded-item text-muted-foreground aria-pressed:bg-highlight aria-pressed:text-highlight-foreground"
          @click="setListView(true)"
        >
          <ListIcon class="size-[18px]" />
        </button>
      </div>
    </div>

    <template v-if="recipes && ready">
      <div
        v-if="!useMobileCards"
        class="grid grid-cols-2 gap-x-3 gap-y-6 sm:gap-x-5 md:grid-cols-3 2xl:grid-cols-4"
      >
        <RecipeTile
          v-for="recipe in recipes"
          :key="recipe.id"
          :name="recipe.name || ''"
          :description="recipe.description"
          :slug="recipe.slug || ''"
          :rating="recipe.rating"
          :image="recipe.image"
          :tags="recipe.tags"
          :total-time="recipe.totalTime"
          :recipe-id="recipe.id || ''"
          @item-selected="(item, urlPrefix) => emit('itemSelected', item, urlPrefix)"
        />
      </div>
      <div
        v-else
        class="grid grid-cols-1 gap-3"
        :class="!singleColumn && 'lg:grid-cols-2 2xl:grid-cols-3'"
      >
        <RecipeRow
          v-for="recipe in recipes"
          :key="recipe.id"
          :name="recipe.name || ''"
          :description="recipe.description"
          :slug="recipe.slug || ''"
          :rating="recipe.rating"
          :image="recipe.image"
          :tags="recipe.tags"
          :total-time="recipe.totalTime"
          :recipe-id="recipe.id || ''"
          @item-selected="(item, urlPrefix) => emit('itemSelected', item, urlPrefix)"
        />
      </div>
      <div
        ref="sentinel"
        class="h-px"
        aria-hidden="true"
      />
    </template>

    <div
      v-if="loading && (!ready || recipes.length === 0)"
      class="grid grid-cols-2 gap-x-3 gap-y-6 sm:gap-x-5 md:grid-cols-3 2xl:grid-cols-4"
      role="status"
      :aria-label="$t('general.loading-recipes')"
    >
      <div
        v-for="n in 8"
        :key="n"
        class="flex flex-col gap-2.5"
      >
        <Skeleton class="aspect-[4/3] w-full rounded-card" />
        <Skeleton class="h-4 w-4/5" />
        <Skeleton class="h-3 w-1/2" />
      </div>
    </div>
    <div
      v-else-if="loading"
      class="flex justify-center py-6"
      role="status"
    >
      <Spinner
        class="size-6 text-primary"
        :label="$t('general.loading-recipes')"
      />
    </div>
    <AppScrollToTop />
  </section>
</template>

<script setup lang="ts">
import { LayoutGridIcon, ListIcon } from "@lucide/vue";
import { useIntersectionObserver, useThrottleFn } from "@vueuse/core";
import { Button } from "~/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "~/components/ui/dropdown-menu";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { Skeleton } from "~/components/ui/skeleton";
import { Spinner } from "~/components/ui/spinner";
import RecipeRow from "./RecipeRow.vue";
import RecipeTile from "./RecipeTile.vue";
import type { UrlPrefixParam } from "./RecipeChips.vue";
import { useLoggedInState } from "~/composables/use-logged-in-state";
import { useLazyRecipes } from "~/composables/recipes";
import type { RecipeSummary, TagOut } from "~/lib/api/types/recipe";
import { useUserSortPreferences } from "~/composables/use-users/preferences";
import type { RecipeSearchQuery } from "~/lib/api/user/recipes/recipe";

const REPLACE_RECIPES_EVENT = "replaceRecipes";
const APPEND_RECIPES_EVENT = "appendRecipes";

interface Props {
  disableToolbar?: boolean;
  disableSort?: boolean;
  icon?: string | null;
  title?: string | null;
  singleColumn?: boolean;
  recipes?: RecipeSummary[];
  query?: RecipeSearchQuery | null;
}
const props = withDefaults(defineProps<Props>(), {
  disableToolbar: false,
  disableSort: false,
  icon: null,
  title: null,
  singleColumn: false,
  recipes: () => [],
  query: null,
});

const emit = defineEmits<{
  replaceRecipes: [recipes: RecipeSummary[]];
  appendRecipes: [recipes: RecipeSummary[]];
  itemSelected: [item: TagOut, urlPrefix: UrlPrefixParam];
}>();

const preferences = useUserSortPreferences();

const EVENTS = {
  az: "az",
  rating: "rating",
  created: "created",
  updated: "updated",
  lastMade: "lastMade",
  totalTime: "totalTime",
  shuffle: "shuffle",
};

// recipes without a value can't be ranked by these, so they always go to the end regardless of direction
const NULLS_LAST_ORDER_BY = ["total_time_seconds"];

const auth = useMealieAuth();
const { $globals } = useNuxtApp();
const { isOwnGroup } = useLoggedInState();
// List view is a saved preference on any screen size; phones default to the two-column grid.
const useMobileCards = computed(() => !!preferences.value.useMobileCards);

const displayTitleIcon = computed(() => {
  return props.icon || $globals.icons.tags;
});

const requestedOrderBy = computed(() => props.query?.orderBy || preferences.value.orderBy);
const effectiveOrderBy = computed(() => {
  return !isOwnGroup.value && requestedOrderBy.value === "last_made" ? "created_at" : requestedOrderBy.value;
});

const sortIcon = computed(() => {
  if (!isOwnGroup.value && requestedOrderBy.value === "last_made") {
    return preferences.value.orderDirection === "asc"
      ? $globals.icons.sortCalendarAscending
      : $globals.icons.sortCalendarDescending;
  }

  return preferences.value.sortIcon;
});

const sortLoading = ref(false);
const randomSeed = ref(Date.now().toString());

const route = useRoute();
const groupSlug = computed(() => route.params.groupSlug as string || auth.user.value?.groupSlug || "");

const page = ref(1);
const perPage = 32;
const hasMore = ref(true);
const ready = ref(false);
const loading = ref(false);

const { fetchMore, getRandom } = useLazyRecipes(isOwnGroup.value ? null : groupSlug.value);
const { savePosition, getSavedPage, restorePosition } = useScrollPosition();
const router = useRouter();

const queryFilter = computed(() => {
  return props.query?.queryFilter || null;

  // TODO: allow user to filter out null values when ordering by a value that may be null (such as lastMade)

  // const orderBy = props.query?.orderBy || preferences.value.orderBy;
  // const orderByFilter = preferences.value.filterNull && orderBy ? `${orderBy} IS NOT NULL` : null;

  // if (props.query.queryFilter && orderByFilter) {
  //   return `(${props.query.queryFilter}) AND ${orderByFilter}`;
  // } else if (props.query.queryFilter) {
  //   return props.query.queryFilter;
  // } else {
  //   return orderByFilter;
  // }
});

async function fetchRecipes(pageCount = 1) {
  const orderDir = props.query?.orderDirection || preferences.value.orderDirection;
  const orderBy = effectiveOrderBy.value;
  const orderByNullPosition = props.query?.orderByNullPosition
    || (NULLS_LAST_ORDER_BY.includes(orderBy) || orderDir !== "asc" ? "last" : "first");
  const localQuery = { ...props.query };
  if (orderBy === "random") {
    localQuery._searchSeed = randomSeed.value;
  }
  return await fetchMore(
    page.value,
    perPage * pageCount,
    orderBy,
    orderDir,
    orderByNullPosition,
    localQuery,
    // we use a computed queryFilter to filter out recipes that have a null value for the property we're sorting by
    queryFilter.value,
  );
}

onMounted(async () => {
  loading.value = true;
  const savedPage = getSavedPage(route.path);

  if (savedPage && savedPage > 2) {
    page.value = 1;
    hasMore.value = true;
    const newRecipes = await fetchRecipes(savedPage);
    if (newRecipes.length < perPage * savedPage) {
      hasMore.value = false;
    }
    page.value = savedPage;
    emit(REPLACE_RECIPES_EVENT, newRecipes);
    ready.value = true;
    restorePosition(route.path);
  }
  else {
    await initRecipes();
    ready.value = true;
    if (savedPage) {
      restorePosition(route.path);
    }
  }
  loading.value = false;
});

let lastQuery: string | undefined = JSON.stringify(props.query);
watch(
  () => props.query,
  async (newValue: RecipeSearchQuery | undefined | null) => {
    const newValueString = JSON.stringify(newValue);
    if (lastQuery !== newValueString) {
      lastQuery = newValueString;
      ready.value = false;
      await initRecipes();
      ready.value = true;
    }
  },
);

async function initRecipes() {
  if (effectiveOrderBy.value === "random") {
    randomSeed.value = Date.now().toString();
  }
  page.value = 1;
  hasMore.value = true;

  // we double-up the first call to avoid a bug with large screens that render
  // the entire first page without scrolling, preventing additional loading
  const newRecipes = await fetchRecipes(page.value + 1);
  if (newRecipes.length < perPage) {
    hasMore.value = false;
  }

  // since we doubled the first call, we also need to advance the page
  page.value = page.value + 1;

  emit(REPLACE_RECIPES_EVENT, newRecipes);
}

const infiniteScroll = useThrottleFn(async () => {
  if (!hasMore.value || loading.value) {
    return;
  }

  loading.value = true;
  page.value = page.value + 1;

  const newRecipes = await fetchRecipes();
  if (newRecipes.length < perPage) {
    hasMore.value = false;
  }
  if (newRecipes.length) {
    emit(APPEND_RECIPES_EVENT, newRecipes);
  }

  savePosition(route.path, page.value);

  loading.value = false;
}, 500);

async function sortRecipes(sortType: string) {
  if (sortLoading.value || loading.value) {
    return;
  }

  if (!isOwnGroup.value && sortType === EVENTS.lastMade) {
    return;
  }

  function setter(
    orderBy: string,
    ascIcon: string,
    descIcon: string,
    defaultOrderDirection = "asc",
    filterNull = false,
  ) {
    if (preferences.value.orderBy !== orderBy) {
      preferences.value.orderBy = orderBy;
      preferences.value.orderDirection = defaultOrderDirection;
      preferences.value.filterNull = filterNull;
    }
    else {
      preferences.value.orderDirection = preferences.value.orderDirection === "asc" ? "desc" : "asc";
    }
    preferences.value.sortIcon = preferences.value.orderDirection === "asc" ? ascIcon : descIcon;
  }

  switch (sortType) {
    case EVENTS.az:
      setter(
        "name",
        $globals.icons.sortAlphabeticalAscending,
        $globals.icons.sortAlphabeticalDescending,
        "asc",
        false,
      );
      break;
    case EVENTS.rating:
      setter("rating", $globals.icons.sortAscending, $globals.icons.sortDescending, "desc", true);
      break;
    case EVENTS.created:
      setter(
        "created_at",
        $globals.icons.sortCalendarAscending,
        $globals.icons.sortCalendarDescending,
        "desc",
        false,
      );
      break;
    case EVENTS.updated:
      setter("updated_at", $globals.icons.sortClockAscending, $globals.icons.sortClockDescending, "desc", false);
      break;
    case EVENTS.lastMade:
      setter(
        "last_made",
        $globals.icons.sortCalendarAscending,
        $globals.icons.sortCalendarDescending,
        "desc",
        true,
      );
      break;
    case EVENTS.totalTime:
      setter(
        "total_time_seconds",
        $globals.icons.sortAscending,
        $globals.icons.sortDescending,
        "asc",
        true,
      );
      break;
    case EVENTS.shuffle:
      setter(
        "random",
        $globals.icons.diceMultiple,
        $globals.icons.diceMultiple, // icon in asc and desc is the same for random
      );
      // We update the seed value to have a different order
      randomSeed.value = Date.now().toString();
      break;
    default:
      console.log("Unknown Event", sortType);
      return;
  }

  // reset pagination
  page.value = 1;
  hasMore.value = true;

  sortLoading.value = true;
  loading.value = true;

  // fetch new recipes
  const newRecipes = await fetchRecipes();
  emit(REPLACE_RECIPES_EVENT, newRecipes);

  sortLoading.value = false;
  loading.value = false;
}

async function navigateRandom() {
  const recipe = await getRandom(props.query, queryFilter.value);
  if (!recipe?.slug) {
    return;
  }

  router.push(`/g/${groupSlug.value}/r/${recipe.slug}`);
}

function setListView(list: boolean) {
  preferences.value.useMobileCards = list;
}

const i18n = useI18n();
const sortOptions = computed(() => [
  { event: EVENTS.az, orderBy: "name", label: i18n.t("general.sort-alphabetically"), icon: $globals.icons.orderAlphabeticalAscending },
  { event: EVENTS.rating, orderBy: "rating", label: i18n.t("general.rating"), icon: $globals.icons.star },
  { event: EVENTS.created, orderBy: "created_at", label: i18n.t("general.created"), icon: $globals.icons.newBox },
  { event: EVENTS.updated, orderBy: "updated_at", label: i18n.t("general.updated"), icon: $globals.icons.update },
  { event: EVENTS.lastMade, orderBy: "last_made", label: i18n.t("general.last-made"), icon: $globals.icons.chefHat },
  { event: EVENTS.totalTime, orderBy: "total_time_seconds", label: i18n.t("recipe.total-time"), icon: $globals.icons.clockOutline },
  { event: EVENTS.shuffle, orderBy: "random", label: i18n.t("general.random"), icon: $globals.icons.diceMultiple },
]
  .filter(option => isOwnGroup.value || option.event !== EVENTS.lastMade)
  .map(option => ({ ...option, active: effectiveOrderBy.value === option.orderBy })));

// Infinite scroll: load the next page when the end of the list comes into view.
const sentinel = ref<HTMLElement | null>(null);
useIntersectionObserver(sentinel, ([entry]) => {
  if (entry?.isIntersecting) {
    infiniteScroll();
  }
}, { rootMargin: "600px 0px" });
</script>
