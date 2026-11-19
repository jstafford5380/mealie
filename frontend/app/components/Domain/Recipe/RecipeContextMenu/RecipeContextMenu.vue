<template>
  <div class="text-center">
    <v-menu
      offset-y
      start
      :eager="isMenuContentLoaded"
      :bottom="!menuTop"
      :nudge-bottom="!menuTop ? '5' : '0'"
      :top="menuTop"
      :nudge-top="menuTop ? '5' : '0'"
      allow-overflow
      close-delay="125"
      content-class="d-print-none"
      @update:model-value="onMenuToggle"
    >
      <template #activator="{ props: activatorProps }">
        <button
          type="button"
          v-bind="activatorProps"
          :aria-label="$t('general.actions')"
          :class="fab
            ? 'inline-flex size-11 items-center justify-center rounded-full bg-card text-foreground shadow-sm ring-1 ring-border transition-colors hover:bg-highlight'
            : 'inline-flex size-9 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-highlight hover:text-foreground'"
          @click.prevent
        >
          <MdiIcon
            :path="icon"
            :class="fab ? 'size-6' : 'size-5'"
          />
        </button>
      </template>

      <RecipeContextMenuContent
        v-if="isMenuContentLoaded"
        v-bind="contentProps"
        @print="$emit('print')"
        @deleted="$emit('deleted', $event)"
        @mealplan-edit="$emit('mealplanEdit')"
        @mealplan-remove="$emit('mealplanRemove')"
      />
    </v-menu>
  </div>
</template>

<script setup lang="ts">
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

function onMenuToggle(isOpen: boolean) {
  if (isOpen && !isMenuContentLoaded.value) {
    isMenuContentLoaded.value = true;
  }
}

const RecipeContextMenuContent = defineAsyncComponent(
  () => import("./RecipeContextMenuContent.vue"),
);
</script>
