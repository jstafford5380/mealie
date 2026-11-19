<template>
  <form
    class="flex flex-col gap-3"
    role="search"
    @submit.prevent="search"
  >
    <label class="flex h-12 items-center gap-3 rounded-control border border-input bg-card px-4 shadow-xs focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/25">
      <SearchIcon class="size-5 shrink-0 text-muted-foreground" />
      <input
        ref="input"
        v-model="state.search"
        type="search"
        enterkeyhint="search"
        autocomplete="off"
        :aria-label="$t('search.search')"
        :placeholder="$t('search.search-placeholder')"
        class="min-w-0 flex-1 border-0 bg-transparent text-base text-foreground outline-none placeholder:text-muted-foreground [&::-webkit-search-cancel-button]:hidden"
        @keyup.enter="hideKeyboard"
      >
      <button
        v-if="state.search"
        type="button"
        class="inline-flex size-8 items-center justify-center rounded-item text-muted-foreground hover:bg-highlight hover:text-highlight-foreground"
        :aria-label="$t('general.clear')"
        @click="state.search = ''"
      >
        <XIcon class="size-4" />
      </button>
    </label>

    <div class="flex flex-wrap items-center gap-2">
      <RecipeExplorerPageSearchFilters />
      <span class="flex-1" />
      <!-- Sort -->
      <DropdownMenu :modal="false">
        <DropdownMenuTrigger as-child>
          <Button
            variant="outline"
            size="sm"
            class="h-9 rounded-full"
          >
            <MdiIcon
              :path="state.orderDirection === 'asc' ? $globals.icons.sortAscending : $globals.icons.sortDescending"
              class="size-[18px]"
            />
            <span class="max-sm:sr-only">{{ sortText }}</span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent
          align="end"
          class="min-w-56"
        >
          <DropdownMenuItem @select="toggleOrderDirection">
            <MdiIcon :path="state.orderDirection === 'asc' ? $globals.icons.sortDescending : $globals.icons.sortAscending" />
            {{ state.orderDirection === "asc" ? $t("general.sort-descending") : $t("general.sort-ascending") }}
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            v-for="v in sortable"
            :key="v.value"
            :class="activeOrderBy === v.value && 'bg-highlight/60 font-semibold text-highlight-foreground'"
            :aria-current="activeOrderBy === v.value ? 'true' : undefined"
            @select="(e: Event) => {
              if (v.value === 'random') { e.preventDefault(); setRandomOrderByWrapper(); }
              else { setOrderBy(v.value); }
            }"
          >
            <MdiIcon :path="v.icon" />
            <span class="flex-1">{{ v.name }}</span>
            <MdiIcon
              v-if="v.value === 'random' && showRandomLoading"
              :path="$globals.icons.refreshCircle"
              class="size-4"
            />
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <!-- Search settings -->
      <Popover>
        <PopoverTrigger as-child>
          <Button
            variant="outline"
            size="icon-sm"
            class="size-9 rounded-full"
            :aria-label="$t('general.settings')"
          >
            <MdiIcon
              :path="$globals.icons.cog"
              class="size-[18px]"
            />
          </Button>
        </PopoverTrigger>
        <PopoverContent
          align="end"
          class="flex w-64 flex-col gap-3"
        >
          <label class="flex items-center justify-between gap-3 text-[15px] font-medium">
            {{ $t("search.auto-search") }}
            <Switch v-model="state.auto" />
          </label>
          <Button
            variant="outline"
            class="w-full"
            @click="reset"
          >
            {{ $t("general.reset") }}
          </Button>
        </PopoverContent>
      </Popover>
    </div>

    <Button
      v-if="!state.auto"
      type="submit"
      size="lg"
      class="w-full sm:mx-auto sm:max-w-sm"
    >
      <SearchIcon class="size-5" />
      {{ $t("search.search") }}
    </Button>
  </form>
</template>

<script setup lang="ts">
import { SearchIcon, XIcon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "~/components/ui/dropdown-menu";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { Popover, PopoverContent, PopoverTrigger } from "~/components/ui/popover";
import { Switch } from "~/components/ui/switch";
import RecipeExplorerPageSearchFilters from "./RecipeExplorerPageSearchFilters.vue";
import { useRecipeExplorerSearch, clearRecipeExplorerSearchState } from "~/composables/use-recipe-explorer-search";

const emit = defineEmits<{
  ready: [];
}>();

const auth = useMealieAuth();
const { isOwnGroup } = useLoggedInState();
const route = useRoute();
const { $globals } = useNuxtApp();
const i18n = useI18n();
const showRandomLoading = ref(false);

const groupSlug = computed(() => route.params.groupSlug as string || auth.user.value?.groupSlug || "");

const {
  state,
  passedQueryWithSeed,
  search,
  reset,
  toggleOrderDirection,
  setOrderBy,
  setRandomOrderBy,
  filterItems,
  initialize,
} = useRecipeExplorerSearch(groupSlug);

defineExpose({
  passedQueryWithSeed,
  filterItems,
});

onMounted(async () => {
  await initialize();
  emit("ready");
});

onUnmounted(() => {
  // Clear the cache when component unmounts to ensure fresh state on remount
  clearRecipeExplorerSearchState(groupSlug.value);
});

const activeOrderBy = computed(() => (!isOwnGroup.value && state.value.orderBy === "last_made" ? "created_at" : state.value.orderBy));

const sortText = computed(() => {
  const orderBy = activeOrderBy.value;
  const sort = sortable.value.find(s => s.value === orderBy);
  if (!sort) return "";
  return `${sort.name}`;
});

const sortable = computed(() => [
  {
    icon: $globals.icons.orderAlphabeticalAscending,
    name: i18n.t("general.sort-alphabetically"),
    value: "name",
  },
  {
    icon: $globals.icons.newBox,
    name: i18n.t("general.created"),
    value: "created_at",
  },
  {
    icon: $globals.icons.chefHat,
    name: i18n.t("general.last-made"),
    value: "last_made",
  },
  {
    icon: $globals.icons.star,
    name: i18n.t("general.rating"),
    value: "rating",
  },
  {
    icon: $globals.icons.clockOutline,
    name: i18n.t("recipe.total-time"),
    value: "total_time_seconds",
  },
  {
    icon: $globals.icons.update,
    name: i18n.t("general.updated"),
    value: "updated_at",
  },
  {
    icon: $globals.icons.diceMultiple,
    name: i18n.t("general.random"),
    value: "random",
  },
].filter(item => isOwnGroup.value || item.value !== "last_made"));

// Methods
const input: Ref<any> = ref(null);

function hideKeyboard() {
  (input.value as HTMLInputElement | null)?.blur();
}

// function to show refresh icon
async function setRandomOrderByWrapper() {
  if (!showRandomLoading.value) {
    showRandomLoading.value = true;
  }
  await setRandomOrderBy();
}
</script>
