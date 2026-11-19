<template>
  <div
    class="inline-flex print:hidden"
    @click.prevent.stop
  >
    <DropdownMenu
      v-model:open="open"
      :modal="false"
    >
      <DropdownMenuTrigger as-child>
        <button
          type="button"
          :aria-label="$t('general.actions')"
          :class="fab
            ? 'inline-flex size-11 items-center justify-center rounded-full bg-card text-foreground shadow-sm ring-1 ring-border transition-colors hover:bg-highlight'
            : 'inline-flex size-9 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-highlight hover:text-foreground'"
          @pointerenter="load"
          @focus="load"
        >
          <MdiIcon
            :path="icon"
            :class="fab ? 'size-6' : 'size-5'"
          />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        :align="menuTop ? 'end' : 'end'"
        :side="menuTop ? 'top' : 'bottom'"
        class="min-w-56"
        @click.stop
      >
        <div
          v-if="!items.length"
          class="flex justify-center py-3"
        >
          <span class="size-5 animate-spin rounded-full border-2 border-muted border-t-primary" />
        </div>
        <DropdownMenuItem
          v-for="item in items"
          :key="item.event"
          :variant="item.event === 'delete' ? 'destructive' : 'default'"
          @select="content?.run(item.event)"
        >
          <MdiIcon
            :path="item.icon"
            class="size-4"
          />
          {{ item.title }}
        </DropdownMenuItem>
        <template v-if="useItems.recipeActions && actions.length">
          <DropdownMenuSeparator />
          <DropdownMenuItem
            v-for="(action, index) in actions"
            :key="index"
            @select="content?.executeRecipeAction(action)"
          >
            <MdiIcon
              :path="$globals.icons.linkVariantPlus"
              class="size-4"
            />
            {{ action.title }}
          </DropdownMenuItem>
        </template>
      </DropdownMenuContent>
    </DropdownMenu>
    <RecipeContextMenuContent
      v-if="isMenuContentLoaded"
      ref="content"
      v-bind="contentProps"
      @print="$emit('print')"
      @deleted="$emit('deleted', $event)"
      @mealplan-edit="$emit('mealplanEdit')"
      @mealplan-remove="$emit('mealplanRemove')"
    />
  </div>
</template>

<script setup lang="ts">
import type { GroupRecipeActionOut } from "~/lib/api/types/household";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "~/components/ui/dropdown-menu";
import { MdiIcon } from "~/components/ui/mdi-icon";
import type { RecipeOut } from "~/lib/api/types/recipe";
import type { ContextMenuIncludes } from "./RecipeContextMenuContent.vue";

export interface ContextMenuItem {
  title: string;
  icon: string;
  color?: string;
  event: string;
  isPublic: boolean;
}

interface Props {
  useItems?: Partial<ContextMenuIncludes>;
  appendItems?: ContextMenuItem[];
  leadingItems?: ContextMenuItem[];
  menuTop?: boolean;
  fab?: boolean;
  color?: string;
  slug: string;
  menuIcon?: string | null;
  name: string;
  recipe?: RecipeOut;
  recipeId: string;
  recipeScale?: number;
}

const props = withDefaults(defineProps<Props>(), {
  useItems: () => ({
    delete: true,
    edit: true,
    download: true,
    downloadPdf: true,
    duplicate: false,
    mealplanner: true,
    shoppingList: true,
    print: true,
    printPreferences: true,
    share: true,
    recipeActions: true,
  }),
  appendItems: () => [],
  leadingItems: () => [],
  menuTop: true,
  fab: false,
  color: "primary",
  menuIcon: null,
  recipe: undefined,
  recipeScale: 1,
});

defineEmits<{
  [key: string]: any;
  print: [];
  deleted: [slug: string];
  mealplanRemove: [];
  mealplanEdit: [];
}>();

const { $globals } = useNuxtApp();

const isMenuContentLoaded = ref(false);

const icon = computed(() => {
  return props.menuIcon || $globals.icons.dotsVertical;
});

// Props to pass to the content component (excluding internal wrapper props)
const contentProps = computed(() => {
  const { ...rest } = props;
  return rest;
});

// The items and their dialogs load on first hover, focus or open, so card grids stay light.
const open = ref(false);
function load() {
  isMenuContentLoaded.value = true;
}
watch(open, (value) => {
  if (value) {
    load();
  }
});

interface ContentApi {
  menuItems: ContextMenuItem[];
  recipeActions: GroupRecipeActionOut[];
  run: (event: string) => void;
  executeRecipeAction: (action: GroupRecipeActionOut) => void;
}
const content = ref<ContentApi | null>(null);
const items = computed<ContextMenuItem[]>(() => unref(content.value?.menuItems) ?? []);
const actions = computed<GroupRecipeActionOut[]>(() => unref(content.value?.recipeActions) ?? []);

const RecipeContextMenuContent = defineAsyncComponent(
  () => import("./RecipeContextMenuContent.vue"),
);
</script>
