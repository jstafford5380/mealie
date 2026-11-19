<template>
  <div
    v-if="items"
    class="font-sans"
  >
    <RecipeOrganizerDialog
      v-model="dialogs.organizer"
      :item-type="itemType"
    />

    <BaseDialog
      v-if="deleteTarget"
      v-model="dialogs.delete"
      :title="$t('general.delete-with-name', { name: $t(translationKey) })"
      color="error"
      :icon="$globals.icons.alertCircle"
      can-confirm
      @confirm="deleteOne()"
    >
      <div class="flex flex-col gap-3 px-6 pb-2 text-[15px]">
        <p class="m-0">
          {{ $t("general.confirm-delete-generic-with-name", { name: $t(translationKey) }) }}
        </p>
        <p class="m-0 rounded-control bg-muted px-3 py-2 font-semibold">
          {{ deleteTarget.name }}
        </p>
      </div>
    </BaseDialog>

    <BaseDialog
      v-if="updateTarget"
      v-model="dialogs.update"
      :title="$t('general.update')"
      :icon="$globals.icons.edit"
      can-confirm
      @confirm="updateOne()"
    >
      <div class="px-6 pb-2">
        <TextField
          v-model="updateTarget.name"
          autofocus
          :label="$t('general.name')"
        />
        <CheckboxField
          v-if="itemType === Organizer.Tool"
          v-model="updateTarget.onHand"
          :label="$t('tool.on-hand')"
        />
      </div>
    </BaseDialog>

    <header class="mb-4 flex flex-wrap items-center gap-3">
      <h1 class="m-0 flex flex-1 items-center gap-2.5 text-[26px] font-bold tracking-tight sm:text-[32px]">
        <slot name="title" />
      </h1>
      <Button @click="dialogs.organizer = true">
        <PlusIcon class="size-4" />
        {{ $t('general.create') }}
      </Button>
    </header>

    <label class="mb-6 flex h-11 max-w-md items-center gap-2 rounded-control border border-input bg-card px-3 focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/25">
      <SearchIcon class="size-4 shrink-0 text-muted-foreground" />
      <input
        v-model="searchString"
        type="search"
        autofocus
        :placeholder="$t('search.search-placeholder')"
        :aria-label="$t('search.search')"
        class="h-full min-w-0 flex-1 bg-transparent text-[15px] outline-none"
      >
    </label>

    <p
      v-if="!fuzzyItems.length"
      class="m-0 rounded-card border border-dashed px-4 py-8 text-center text-sm text-muted-foreground"
    >
      {{ searchString ? $t('search.no-results') : $t('data-pages.nothing-here-yet') }}
    </p>

    <section
      v-for="(itms, key) in itemsSorted"
      :key="key"
      class="mb-6"
    >
      <h2
        v-if="isTitle(key)"
        class="m-0 mb-2 text-sm font-bold text-muted-foreground"
      >
        {{ key }}
      </h2>
      <ul class="m-0 grid list-none gap-2 p-0 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        <template
          v-for="item in itms"
          :key="item?.id"
        >
          <li
            v-if="item"
            class="flex min-w-0 items-center rounded-card border bg-card pe-1 transition-colors hover:border-primary/50"
          >
            <NuxtLink
              :to="`/g/${groupSlug}?${itemType}=${item.id}`"
              class="flex min-w-0 flex-1 items-center gap-3 py-3 ps-4 text-foreground no-underline"
            >
              <MdiIcon
                :path="icon"
                class="size-5 shrink-0 text-muted-foreground"
              />
              <span class="truncate font-semibold">{{ item.name }}</span>
            </NuxtLink>
            <DropdownMenu :modal="false">
              <DropdownMenuTrigger as-child>
                <button
                  type="button"
                  class="inline-flex size-9 shrink-0 items-center justify-center rounded-full text-muted-foreground hover:bg-highlight hover:text-foreground"
                  :aria-label="$t('general.options-for', { name: item.name })"
                >
                  <EllipsisVerticalIcon class="size-4" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem @select="openUpdateDialog(item)">
                  <PencilIcon class="size-4" />
                  {{ $t('general.edit') }}
                </DropdownMenuItem>
                <DropdownMenuItem
                  variant="destructive"
                  @select="confirmDelete(item)"
                >
                  <Trash2Icon class="size-4" />
                  {{ $t('general.delete') }}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </li>
        </template>
      </ul>
    </section>
  </div>
</template>

<script setup lang="ts" generic="T extends { id: string; name: string; slug: string; onHand?: boolean }">
import { EllipsisVerticalIcon, PencilIcon, PlusIcon, SearchIcon, Trash2Icon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "~/components/ui/dropdown-menu";
import CheckboxField from "~/components/ui/field/CheckboxField.vue";
import TextField from "~/components/ui/field/TextField.vue";
import { MdiIcon } from "~/components/ui/mdi-icon";
import Fuse from "fuse.js";
import RecipeOrganizerDialog from "~/components/Domain/Recipe/RecipeOrganizerDialog.vue";
import { Organizer, type RecipeOrganizer } from "~/lib/api/types/non-generated";
import { useRouteQuery } from "~/composables/use-router";
import { deepCopy } from "~/composables/use-utils";

const props = defineProps<{
  items: T[];
  icon: string;
  itemType: RecipeOrganizer;
}>();

const emit = defineEmits<{
  update: [item: T];
  delete: [id: string];
}>();

const state = reactive({
  // Search Options
  options: {
    ignoreLocation: true,
    shouldSort: true,
    threshold: 0.2,
    location: 0,
    distance: 20,
    findAllMatches: true,
    maxPatternLength: 32,
    minMatchCharLength: 1,
    keys: ["name"],
  },
});

const auth = useMealieAuth();
const route = useRoute();
const groupSlug = computed(() => route.params.groupSlug as string || auth.user?.value?.groupSlug || "");

// =================================================================
// Context Menu

const dialogs = ref({
  organizer: false,
  update: false,
  delete: false,
});

const translationKey = computed<string>(() => {
  const typeMap = {
    categories: "category.category",
    tags: "tag.tag",
    tools: "tool.tool",
    foods: "shopping-list.food",
    households: "household.household",
  };
  return typeMap[props.itemType] || "";
});

const deleteTarget = shallowRef<T | null>(null);
const updateTarget = ref<T | null>(null) as Ref<T | null>;

function confirmDelete(item: T) {
  deleteTarget.value = item;
  dialogs.value.delete = true;
}

function deleteOne() {
  if (!deleteTarget.value) {
    return;
  }

  emit("delete", deleteTarget.value.id);
}

function openUpdateDialog(item: T) {
  updateTarget.value = deepCopy(item);
  dialogs.value.update = true;
}

function updateOne() {
  if (!updateTarget.value) {
    return;
  }

  emit("update", updateTarget.value);
}

// ================================================================
// Search Functions

const searchString = useRouteQuery("q", "");

const fuse = computed(() => {
  return new Fuse(props.items, state.options);
});

const fuzzyItems = computed<T[]>(() => {
  if (searchString.value.trim() === "") {
    return props.items;
  }
  const result = fuse.value.search(searchString.value.trim() as string);
  return result.map(x => x.item);
});

// =================================================================
// Sorted Items

const itemsSorted = computed(() => {
  const byLetter: { [key: string]: Array<T> } = {};

  if (!fuzzyItems.value) {
    return byLetter;
  }

  [...fuzzyItems.value]
    .sort((a, b) => a.name.localeCompare(b.name))
    .forEach((item) => {
      const letter = item.name[0].toUpperCase();
      if (!byLetter[letter]) {
        byLetter[letter] = [];
      }
      byLetter[letter].push(item);
    });

  return byLetter;
});

function isTitle(str: number | string) {
  return typeof str === "string" && str.length === 1;
}
</script>
