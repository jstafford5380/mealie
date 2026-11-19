<template>
  <div class="flex min-w-0 items-start gap-1.5 font-sans">
    <div class="min-w-0 flex-1">
      <ComboboxRoot
        v-model:open="open"
        :model-value="selected ?? []"
        :by="sameItem"
        multiple
        ignore-filter
        open-on-click
        :disabled="!!inputAttrs.disabled"
        @update:model-value="onSelect"
      >
        <ComboboxAnchor
          class="flex min-h-10 w-full flex-wrap items-center gap-1.5 rounded-control border border-input bg-card px-2 py-1.5 text-[15px] focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/25 data-[disabled]:opacity-60"
        >
          <MdiIcon
            v-if="icon"
            :path="icon"
            class="ms-0.5 size-4 shrink-0 text-muted-foreground"
          />
          <span
            v-for="(item, index) in selected ?? []"
            :key="item.id ?? index"
            class="inline-flex h-7 max-w-full items-center gap-1 rounded-full bg-highlight ps-3 pe-1 text-sm font-medium text-highlight-foreground"
          >
            <span class="truncate">{{ titleOf(item) }}</span>
            <button
              type="button"
              class="inline-flex size-5 items-center justify-center rounded-full hover:bg-primary hover:text-primary-foreground"
              :aria-label="`${$t('general.remove')}: ${titleOf(item)}`"
              @click.stop="removeByIndex(index)"
            >
              <XIcon class="size-3" />
            </button>
          </span>
          <ComboboxInput
            v-model="searchInput"
            :placeholder="(selected?.length ? '' : label) || $t('search.search')"
            :aria-label="label || $t('search.search')"
            class="h-7 min-w-24 flex-1 bg-transparent px-1 outline-none placeholder:text-muted-foreground/80"
            @keydown.backspace="onBackspace"
          />
        </ComboboxAnchor>
        <ComboboxPortal>
          <ComboboxContent
            position="popper"
            :side-offset="4"
            align="start"
            class="z-[2400] max-h-[min(16rem,var(--reka-combobox-content-available-height))] w-[var(--reka-combobox-trigger-width)] min-w-56 overflow-hidden rounded-control border bg-popover font-sans text-popover-foreground shadow-md"
          >
            <ComboboxViewport class="max-h-[inherit] overflow-y-auto p-1">
              <ComboboxEmpty
                v-if="!showCreate"
                class="px-3 py-4 text-center text-sm text-muted-foreground"
              >
                {{ showAdd ? $t('recipe.press-enter-to-create') : $t('search.no-results') }}
              </ComboboxEmpty>
              <ComboboxItem
                v-for="item in filteredItems"
                :key="item.id"
                :value="item"
                class="flex min-h-9 cursor-default select-none items-center gap-2 rounded-item px-2.5 py-1.5 text-[15px] outline-none data-[highlighted]:bg-highlight data-[highlighted]:text-highlight-foreground"
              >
                <span class="min-w-0 flex-1 truncate">{{ titleOf(item) }}</span>
                <CheckIcon
                  v-if="isSelected(item)"
                  class="size-4 text-primary"
                />
              </ComboboxItem>
              <ComboboxItem
                v-if="showCreate"
                :value="CREATE"
                class="flex min-h-9 cursor-default select-none items-center gap-2 rounded-item px-2.5 py-1.5 text-[15px] font-medium text-primary outline-none data-[highlighted]:bg-highlight"
              >
                <PlusIcon class="size-4" />
                {{ $t('general.create-name', { name: searchInput.trim() }) }}
              </ComboboxItem>
            </ComboboxViewport>
          </ComboboxContent>
        </ComboboxPortal>
      </ComboboxRoot>
    </div>
    <template v-if="showAdd">
      <Button
        variant="ghost"
        size="icon"
        :aria-label="$t('general.create')"
        :title="$t('general.create')"
        @click="dialog = true"
      >
        <PlusIcon class="size-4" />
      </Button>
      <RecipeOrganizerDialog
        v-model="dialog"
        :item-type="selectorType"
        @created-item="appendCreated"
      />
    </template>
  </div>
</template>

<script setup lang="ts" generic="T extends { id: string; name: string }">
import { Organizer, type RecipeOrganizer } from "~/lib/api/types/non-generated";
import { useCategoryStore, useFoodStore, useLabelStore, useHouseholdStore, useTagStore, useToolStore } from "~/composables/store";
import { useUserStore } from "~/composables/store/use-user-store";
import { CheckIcon, PlusIcon, XIcon } from "@lucide/vue";
import {
  ComboboxAnchor,
  ComboboxContent,
  ComboboxEmpty,
  ComboboxInput,
  ComboboxItem,
  ComboboxPortal,
  ComboboxRoot,
  ComboboxViewport,
} from "reka-ui";
import { Button } from "~/components/ui/button";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { normalize } from "~/composables/use-utils";

interface Props {
  selectorType: RecipeOrganizer;
  inputAttrs?: Record<string, any>;
  showAdd?: boolean;
  showLabel?: boolean;
  showIcon?: boolean;
  /** Kept for callers; the field has one look now. */
  variant?: "filled" | "underlined" | "outlined" | "plain" | "solo" | "solo-inverted" | "solo-filled";
}

const props = withDefaults(defineProps<Props>(), {
  inputAttrs: () => ({}),
  showAdd: true,
  showLabel: true,
  showIcon: true,
  variant: "outlined",
});

const selected = defineModel<T[] | undefined>({ required: true });

onMounted(() => {
  if (selected.value === undefined) {
    selected.value = [];
  }
});

const i18n = useI18n();
const { $globals } = useNuxtApp();

const label = computed(() => {
  if (!props.showLabel) {
    return "";
  }

  switch (props.selectorType) {
    case Organizer.Tag:
      return i18n.t("tag.tags");
    case Organizer.Category:
      return i18n.t("category.categories");
    case Organizer.Tool:
      return i18n.t("tool.tools");
    case Organizer.Food:
      return i18n.t("general.foods");
    case Organizer.Label:
      return i18n.t("data-pages.foods.food-label");
    case Organizer.Household:
      return i18n.t("household.households");
    case Organizer.User:
      return i18n.t("user.users");
    default:
      return i18n.t("general.organizer");
  }
});

const icon = computed(() => {
  if (!props.showIcon) {
    return "";
  }

  switch (props.selectorType) {
    case Organizer.Tag:
      return $globals.icons.tags;
    case Organizer.Category:
      return $globals.icons.categories;
    case Organizer.Tool:
      return $globals.icons.tools;
    case Organizer.Food:
      return $globals.icons.foods;
    case Organizer.Label:
      return $globals.icons.tags;
    case Organizer.Household:
      return $globals.icons.household;
    case Organizer.User:
      return $globals.icons.user;
    default:
      return $globals.icons.tags;
  }
});

function titleOf(item: any): string {
  return props.selectorType === Organizer.User ? (item?.fullName ?? item?.name ?? "") : (item?.name ?? "");
}

// ===========================================================================
// Store & Items Setup

const storeMap = {
  [Organizer.Category]: useCategoryStore(),
  [Organizer.Tag]: useTagStore(),
  [Organizer.Tool]: useToolStore(),
  [Organizer.Food]: useFoodStore(),
  [Organizer.Label]: useLabelStore(),
  [Organizer.Household]: useHouseholdStore(),
  [Organizer.User]: useUserStore(),
};

const activeStore = computed(() => {
  const { store } = storeMap[props.selectorType];
  return store.value;
});

const items = computed<any[]>(() => {
  const list = (activeStore.value as unknown as any[]) ?? [];
  return list;
});

function removeByIndex(index: number) {
  if (selected.value === undefined) {
    return;
  }

  const newSelected = selected.value.filter((_, i) => i !== index);
  selected.value = [...newSelected];
}

function appendCreated(item: any) {
  if (selected.value === undefined) {
    return;
  }

  selected.value = [...selected.value, item];
}

const open = ref(false);
const CREATE = { id: "__create__", name: "" };

const filteredItems = computed(() => {
  const term = normalize(searchInput.value.trim());
  return term ? items.value.filter(item => normalize(titleOf(item)).includes(term)) : items.value;
});
const showCreate = computed(() => {
  const term = searchInput.value.trim().toLowerCase();
  return props.showAdd && !!term && !items.value.some(item => titleOf(item).toLowerCase() === term);
});

function sameItem(a: any, b: any) {
  return !!a && !!b && (a.id ?? a.name) === (b.id ?? b.name);
}
function isSelected(item: any) {
  return (selected.value ?? []).some(s => sameItem(s, item));
}

function onSelect(value: any) {
  const list = (value ?? []) as any[];
  if (list.some(item => item?.id === CREATE.id)) {
    createItem();
    return;
  }
  selected.value = [...list];
}

function onBackspace() {
  // Backspace in an empty search box removes the last chip, like other chip inputs.
  if (!searchInput.value && selected.value?.length) {
    removeByIndex(selected.value.length - 1);
  }
}

async function createItem() {
  if (!searchInput.value) {
    return;
  }

  const actions = storeMap[props.selectorType].actions;
  // @ts-expect-error different organizer types have different required fields
  const newItem = await actions.createOne({ name: searchInput.value });
  if (newItem) {
    appendCreated(newItem);
  }
  searchInput.value = "";
}

const dialog = ref(false);

const searchInput = ref("");
</script>
