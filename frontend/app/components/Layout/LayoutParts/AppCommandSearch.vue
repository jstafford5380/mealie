<script setup lang="ts">
import type { AppNavItem, AppNavSection } from "~/composables/use-app-navigation";
import type { RecipeSummary } from "~/lib/api/types/recipe";
import { SearchIcon, XIcon } from "@lucide/vue";
import { useEventListener } from "@vueuse/core";
import { DialogContent, DialogOverlay, DialogPortal, DialogRoot, DialogTitle } from "reka-ui";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { useUserApi } from "~/composables/api";
import { usePublicExploreApi } from "~/composables/api/api-client";
import { useStaticRoutes } from "~/composables/api/static-routes";
import { useNavGroupSlug } from "~/composables/use-app-navigation";
import { useLoggedInState } from "~/composables/use-logged-in-state";
import { useRecipeSearch } from "~/composables/recipes/use-recipe-search";

const props = defineProps<{
  /** Navigation offered as "Go to" commands while the query is empty. */
  sections?: AppNavSection[];
}>();

const open = defineModel<boolean>("open", { default: false });

const router = useRouter();
const route = useRoute();
const groupSlug = useNavGroupSlug();
const { isOwnGroup } = useLoggedInState();
const { recipeTinyImage } = useStaticRoutes();

const api = isOwnGroup.value ? useUserApi() : usePublicExploreApi(groupSlug.value).explore;
const search = useRecipeSearch(api);

const query = search.query;
const searching = computed(() => query.value.trim().length > 0);

interface Command {
  id: string;
  kind: "recipe" | "nav";
  title: string;
  description?: string;
  icon?: string;
  image?: string;
  run: () => void;
}

function flatten(items: AppNavItem[]): AppNavItem[] {
  return items.flatMap(item => (item.children ? flatten(item.children) : item.to ? [item] : []));
}

const navCommands = computed<Command[]>(() => (props.sections ?? [])
  .flatMap(section => flatten(section.items))
  .map(item => ({ id: `nav-${item.key}`, kind: "nav", title: item.title, icon: item.icon, run: () => router.push(item.to!) })));

const recipeCommands = computed<Command[]>(() => search.data.value.map((recipe: RecipeSummary) => ({
  id: `recipe-${recipe.id}`,
  kind: "recipe",
  title: recipe.name || "",
  description: recipe.description || "",
  image: recipe.image && recipe.id ? recipeTinyImage(recipe.id, recipe.image) : undefined,
  run: () => {
    if (recipe.slug) {
      router.push(`/g/${groupSlug.value}/r/${recipe.slug}`);
    }
  },
})));

const commands = computed(() => (searching.value ? recipeCommands.value : navCommands.value));
const activeIndex = ref(-1);
watch(commands, () => {
  activeIndex.value = -1;
});

const listEl = ref<HTMLElement | null>(null);
async function move(delta: number) {
  const max = commands.value.length - 1;
  activeIndex.value = Math.min(Math.max(activeIndex.value + delta, -1), max);
  await nextTick();
  listEl.value?.querySelector(`[data-index="${activeIndex.value}"]`)?.scrollIntoView({ block: "nearest" });
}

function activate(command: Command | undefined) {
  if (!command) {
    return;
  }
  open.value = false;
  command.run();
}

function onKeydown(event: KeyboardEvent) {
  if (event.isComposing) {
    return;
  }
  if (event.key === "ArrowDown") {
    event.preventDefault();
    void move(1);
  }
  else if (event.key === "ArrowUp") {
    event.preventDefault();
    void move(-1);
  }
  else if (event.key === "Enter") {
    event.preventDefault();
    activate(commands.value[Math.max(activeIndex.value, 0)]);
  }
}

// Reset on close; close when the route changes.
watch(open, (value) => {
  if (!value) {
    query.value = "";
    search.data.value = [];
    activeIndex.value = -1;
  }
});
watch(() => route.fullPath, () => {
  open.value = false;
});

// "/" (outside text fields) and Cmd/Ctrl+K open search from anywhere.
useEventListener(document, "keydown", (event: KeyboardEvent) => {
  const target = event.target as HTMLElement | null;
  const typing = !!target && (target.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName));
  if ((event.key === "k" || event.key === "K") && (event.metaKey || event.ctrlKey)) {
    event.preventDefault();
    open.value = !open.value;
  }
  else if (event.key === "/" && !typing && !open.value) {
    event.preventDefault();
    open.value = true;
  }
});

const activeId = computed(() => (activeIndex.value >= 0 ? `cmd-${commands.value[activeIndex.value]?.id}` : undefined));
</script>

<template>
  <DialogRoot v-model:open="open">
    <DialogPortal>
      <DialogOverlay class="fixed inset-0 z-[2050] bg-black/40 data-[state=open]:animate-in data-[state=open]:fade-in-0" />
      <DialogContent
        :aria-describedby="undefined"
        class="fixed inset-x-0 top-0 z-[2051] mx-auto flex max-h-dvh w-full flex-col overflow-hidden border bg-popover font-sans text-popover-foreground shadow-2xl outline-none sm:top-[12vh] sm:max-h-[70vh] sm:w-[min(640px,calc(100vw-2rem))] sm:rounded-panel data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-[0.98]"
        @open-auto-focus.prevent="($event.target as HTMLElement)?.querySelector('input')?.focus()"
      >
        <DialogTitle class="sr-only">
          {{ $t("search.search") }}
        </DialogTitle>
        <div class="flex items-center gap-3 border-b px-4">
          <SearchIcon class="size-5 shrink-0 text-muted-foreground" />
          <input
            v-model="query"
            type="search"
            role="combobox"
            aria-autocomplete="list"
            :aria-expanded="commands.length > 0"
            aria-controls="command-search-list"
            :aria-activedescendant="activeId"
            autocomplete="off"
            spellcheck="false"
            :placeholder="$t('search.search-placeholder')"
            :aria-label="$t('search.search')"
            class="h-14 min-w-0 flex-1 border-0 bg-transparent text-base text-foreground outline-none placeholder:text-muted-foreground [&::-webkit-search-cancel-button]:hidden"
            @keydown="onKeydown"
          >
          <span
            v-if="search.loading.value"
            class="size-4 animate-spin rounded-full border-2 border-muted-foreground/30 border-t-primary"
            role="status"
            :aria-label="$t('general.loading')"
          />
          <button
            type="button"
            class="inline-flex size-9 items-center justify-center rounded-item text-muted-foreground hover:bg-highlight hover:text-highlight-foreground"
            :aria-label="$t('general.close')"
            @click="open = false"
          >
            <XIcon class="size-5" />
          </button>
        </div>

        <div
          ref="listEl"
          class="min-h-0 flex-1 overflow-y-auto p-2"
        >
          <p
            class="m-0 px-2.5 pb-1.5 pt-1 text-[12.5px] font-semibold text-muted-foreground"
          >
            {{ searching ? $t("search.results") : $t("sidebar.go-to") }}
          </p>
          <ul
            id="command-search-list"
            role="listbox"
            :aria-label="searching ? $t('search.results') : $t('sidebar.go-to')"
            class="m-0 flex list-none flex-col gap-0.5 p-0"
          >
            <li
              v-for="(command, index) in commands"
              :id="`cmd-${command.id}`"
              :key="command.id"
              role="option"
              :data-index="index"
              :aria-selected="index === activeIndex"
              class="flex cursor-pointer items-center gap-3 rounded-control px-2.5 py-2 aria-selected:bg-highlight aria-selected:text-highlight-foreground hover:bg-highlight/60"
              @mousemove="activeIndex = index"
              @click="activate(command)"
            >
              <template v-if="command.kind === 'recipe'">
                <img
                  v-if="command.image"
                  :src="command.image"
                  alt=""
                  class="size-11 shrink-0 rounded-item bg-muted object-cover"
                  loading="lazy"
                >
                <span
                  v-else
                  class="flex size-11 shrink-0 items-center justify-center rounded-item bg-muted text-muted-foreground"
                >
                  <MdiIcon
                    :path="$globals.icons.primary"
                    class="size-5"
                  />
                </span>
                <span class="flex min-w-0 flex-col">
                  <span class="truncate font-serif text-[16px] leading-snug">{{ command.title }}</span>
                  <span
                    v-if="command.description"
                    class="truncate text-[13px] text-muted-foreground"
                  >{{ command.description }}</span>
                </span>
              </template>
              <template v-else>
                <MdiIcon
                  :path="command.icon"
                  class="size-[18px] text-muted-foreground"
                />
                <span class="text-[15px] font-medium">{{ command.title }}</span>
              </template>
            </li>
          </ul>
          <p
            v-if="searching && !search.loading.value && commands.length === 0"
            class="m-0 px-2.5 py-8 text-center text-sm text-muted-foreground"
            role="status"
          >
            {{ $t("search.no-results") }}
          </p>
        </div>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>
