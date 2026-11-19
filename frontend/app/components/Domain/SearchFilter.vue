<template>
  <Popover v-model:open="state.menu">
    <PopoverTrigger as-child>
      <button
        type="button"
        class="inline-flex h-9 items-center gap-2 rounded-full border px-3 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
        :class="selectedCount > 0
          ? 'border-primary bg-highlight text-highlight-foreground'
          : 'border-input bg-card text-foreground hover:bg-highlight/60'"
      >
        <slot />
        <span
          v-if="selectedCount > 0"
          class="inline-flex min-w-5 items-center justify-center rounded-full bg-primary px-1.5 text-xs font-bold text-primary-foreground"
        >
          {{ selectedCount }}
          <span class="sr-only">{{ $t("search.selected") }}</span>
        </span>
        <ChevronDownIcon class="size-4 opacity-70" />
      </button>
    </PopoverTrigger>
    <PopoverContent
      align="start"
      class="w-[min(360px,calc(100vw-2rem))] p-0"
    >
      <div class="flex flex-col gap-3 p-3">
        <label class="flex h-10 items-center gap-2 rounded-control border border-input bg-card px-3 focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/25">
          <SearchIcon class="size-4 text-muted-foreground" />
          <input
            v-model="searchInput"
            type="search"
            autocomplete="off"
            :aria-label="$t('search.search')"
            :placeholder="$t('search.search')"
            class="min-w-0 flex-1 border-0 bg-transparent text-[15px] outline-none placeholder:text-muted-foreground"
          >
        </label>
        <div class="flex items-center gap-2">
          <div
            v-if="requireAll != undefined"
            role="radiogroup"
            :aria-label="$t('search.match')"
            class="flex rounded-control bg-subtle p-0.5"
          >
            <button
              v-for="option in combinatorOptions"
              :key="option.value"
              type="button"
              role="radio"
              :aria-checked="combinator === option.value"
              class="h-8 rounded-item px-3 text-sm font-medium text-muted-foreground aria-checked:bg-card aria-checked:text-foreground aria-checked:shadow-sm"
              @click="combinator = option.value"
            >
              {{ option.label }}
            </button>
          </div>
          <button
            type="button"
            class="ms-auto h-8 rounded-item px-2.5 text-sm font-semibold text-primary hover:bg-highlight disabled:opacity-50"
            :disabled="selectedCount === 0 && !searchInput"
            @click="clearSelection"
          >
            {{ $t("search.clear-selection") }}
          </button>
        </div>
      </div>
      <Separator />
      <div
        v-if="filtered.length > 0"
        ref="viewport"
        class="relative h-[300px] overflow-y-auto overscroll-contain"
        :role="radio ? 'radiogroup' : 'group'"
        @scroll="onScroll"
      >
        <div :style="{ height: `${filtered.length * ROW_HEIGHT}px` }">
          <label
            v-for="row in visibleRows"
            :key="row.item.id"
            class="absolute inset-x-0 flex cursor-pointer items-center gap-3 px-3 text-[15px] hover:bg-highlight/60"
            :style="{ top: `${row.index * ROW_HEIGHT}px`, height: `${ROW_HEIGHT}px` }"
          >
            <input
              v-if="radio"
              type="radio"
              :name="radioName"
              class="size-[18px] accent-[var(--primary)]"
              :checked="selectedIds.has(row.item.id)"
              @click="toggleRadio(row.item)"
            >
            <input
              v-else
              type="checkbox"
              class="size-[18px] rounded accent-[var(--primary)]"
              :checked="selectedIds.has(row.item.id)"
              @change="toggleItem(row.item)"
            >
            <span class="truncate">{{ row.item.name }}</span>
          </label>
        </div>
      </div>
      <p
        v-else
        role="status"
        class="m-0 px-3 py-8 text-center text-sm text-muted-foreground"
      >
        {{ $t("search.no-results") }}
      </p>
    </PopoverContent>
  </Popover>
</template>

<script setup lang="ts">
import type { ISearchableItem } from "~/composables/use-search";
import { ChevronDownIcon, SearchIcon } from "@lucide/vue";
import { Popover, PopoverContent, PopoverTrigger } from "~/components/ui/popover";
import { Separator } from "~/components/ui/separator";
import { useSearch } from "~/composables/use-search";

const props = defineProps({
  items: {
    type: Array as () => ISearchableItem[],
    required: true,
  },
  requireAll: {
    type: Boolean,
    default: undefined,
  },
  radio: {
    type: Boolean,
    default: false,
  },
});

const modelValue = defineModel<ISearchableItem[]>();

const emit = defineEmits<{
  (e: "update:requireAll", value: boolean | undefined): void;
}>();

const i18n = useI18n();
const radioName = `filter-${useId()}`;

const state = reactive({
  menu: false,
});

const { search: searchInput, filtered } = useSearch(computed(() => props.items));

const combinatorOptions = computed(() => [
  { value: "hasAll", label: i18n.t("search.has-all") },
  { value: "hasAny", label: i18n.t("search.has-any") },
]);

const combinator = computed({
  get: () => (props.requireAll ? "hasAll" : "hasAny"),
  set: (value: string) => {
    emit("update:requireAll", value === "hasAll");
  },
});

const selected = computed<ISearchableItem[]>({
  get: () => modelValue.value ?? [],
  set: (value: ISearchableItem[]) => {
    modelValue.value = value;
  },
});

const selectedCount = computed(() => selected.value.length);
const selectedIds = computed(() => new Set(selected.value.map(item => item.id)));

function toggleItem(item: ISearchableItem) {
  selected.value = selectedIds.value.has(item.id)
    ? selected.value.filter(existing => existing.id !== item.id)
    : [...selected.value, item];
}

// A second click on the chosen radio clears it.
function toggleRadio(item: ISearchableItem) {
  selected.value = selectedIds.value.has(item.id) ? [] : [item];
}

function clearSelection() {
  selected.value = [];
  searchInput.value = "";
}

// Virtualised list: only the rows in view (plus a margin) are rendered.
const ROW_HEIGHT = 40;
const OVERSCAN = 6;
const viewport = ref<HTMLElement | null>(null);
const scrollTop = ref(0);
function onScroll() {
  scrollTop.value = viewport.value?.scrollTop ?? 0;
}
watch(filtered, () => {
  scrollTop.value = 0;
  if (viewport.value) {
    viewport.value.scrollTop = 0;
  }
});
const visibleRows = computed(() => {
  const start = Math.max(0, Math.floor(scrollTop.value / ROW_HEIGHT) - OVERSCAN);
  const end = Math.min(filtered.value.length, Math.ceil((scrollTop.value + 300) / ROW_HEIGHT) + OVERSCAN);
  return filtered.value.slice(start, end).map((item, offset) => ({ item, index: start + offset }));
});
</script>
