<template>
  <div class="flex flex-col gap-3 font-sans">
    <!-- toolbar -->
    <div class="flex flex-wrap items-center gap-2">
      <label class="flex h-10 min-w-0 flex-1 basis-56 items-center gap-2 rounded-control border border-input bg-card px-3 focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/25 sm:max-w-sm">
        <SearchIcon class="size-4 shrink-0 text-muted-foreground" />
        <input
          v-model="search"
          type="search"
          :placeholder="$t('search.search')"
          :aria-label="$t('search.search')"
          class="h-full min-w-0 flex-1 bg-transparent text-[15px] outline-none"
        >
      </label>
      <div class="ms-auto flex flex-wrap items-center gap-2">
        <slot name="button-row" />
        <DropdownMenu :modal="false">
          <DropdownMenuTrigger as-child>
            <button
              type="button"
              class="inline-flex size-10 items-center justify-center rounded-control border bg-card text-muted-foreground hover:bg-highlight hover:text-foreground"
              :aria-label="$t('data-pages.table-options')"
              :title="$t('data-pages.table-options')"
            >
              <EllipsisIcon class="size-4" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            align="end"
            class="min-w-52"
          >
            <template v-if="tableConfig.hideColumns">
              <DropdownMenuLabel>{{ $t('data-pages.columns') }}</DropdownMenuLabel>
              <DropdownMenuCheckboxItem
                v-for="header in localHeaders"
                :key="header.value"
                :model-value="header.show"
                @select.prevent
                @update:model-value="header.show = $event"
              >
                {{ header.text }}
              </DropdownMenuCheckboxItem>
              <DropdownMenuSeparator />
            </template>
            <DropdownMenuItem @select="downloadAsJson(data, 'export.json')">
              <DownloadIcon class="size-4" />
              {{ $t('data-pages.download-all-json') }}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>

    <!-- bulk bar: only while rows are selected -->
    <div
      v-if="bulkActions.length > 0 && selected.length > 0"
      class="flex flex-wrap items-center gap-2 rounded-card border border-primary/30 bg-primary/8 px-3 py-2"
    >
      <span class="text-sm font-semibold">{{ $t('data-pages.selected-count', selected.length) }}</span>
      <Button
        variant="ghost"
        size="sm"
        @click="selected = []"
      >
        {{ $t('data-pages.clear-selection') }}
      </Button>
      <div class="ms-auto flex flex-wrap gap-2">
        <Button
          v-for="action in bulkActions"
          :key="action.event"
          size="sm"
          :variant="action.event.startsWith('delete') ? 'destructive' : 'outline'"
          @click="runBulk(action)"
        >
          <MdiIcon
            :path="action.icon"
            class="size-4"
          />
          {{ action.text }}
        </Button>
      </div>
    </div>

    <div class="overflow-x-auto rounded-card border bg-card">
      <table class="w-full border-collapse text-[14.5px]">
        <thead>
          <tr class="border-b bg-muted/40 text-left">
            <th
              v-if="bulkActions.length > 0"
              class="w-11 ps-4"
            >
              <Checkbox
                :model-value="allPageSelected ? true : somePageSelected ? 'indeterminate' : false"
                :aria-label="$t('data-pages.select-all')"
                @update:model-value="togglePage"
              >
                <template #default="{ modelValue }">
                  <MinusIcon
                    v-if="modelValue === 'indeterminate'"
                    class="size-3.5"
                  />
                  <CheckIcon
                    v-else
                    class="size-3.5"
                  />
                </template>
              </Checkbox>
            </th>
            <th
              v-for="header in visibleHeaders"
              :key="header.value"
              class="h-11 px-3 text-[13px] font-semibold whitespace-nowrap text-muted-foreground"
              :class="alignClass(header.align)"
              :aria-sort="sortKey === header.value ? (sortDesc ? 'descending' : 'ascending') : undefined"
            >
              <button
                v-if="header.sortable"
                type="button"
                class="inline-flex items-center gap-1 rounded-item hover:text-foreground"
                @click="toggleSort(header.value)"
              >
                {{ header.text }}
                <ArrowUpIcon
                  v-if="sortKey === header.value"
                  class="size-3.5 transition-transform"
                  :class="sortDesc && 'rotate-180'"
                />
                <ArrowUpDownIcon
                  v-else
                  class="size-3.5 opacity-40"
                />
              </button>
              <template v-else>
                {{ header.text }}
              </template>
            </th>
            <th
              v-if="rowActions"
              class="w-24"
            >
              <span class="sr-only">{{ $t('general.actions') }}</span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="item in pageItems"
            :key="rowKey(item)"
            class="border-b last:border-b-0 hover:bg-muted/30"
            :class="isSelected(item) && 'bg-primary/6'"
          >
            <td
              v-if="bulkActions.length > 0"
              class="ps-4"
            >
              <Checkbox
                :model-value="isSelected(item)"
                :aria-label="$t('data-pages.select-item', { name: itemName(item) })"
                @update:model-value="toggleItem(item)"
              />
            </td>
            <td
              v-for="header, column in visibleHeaders"
              :key="header.value"
              class="px-3 py-2.5"
              :class="[alignClass(header.align), column === 0 && 'min-w-40 font-medium']"
            >
              <slot
                :name="'item.' + header.value"
                v-bind="{ item }"
              >
                {{ item[header.value] }}
              </slot>
            </td>
            <td
              v-if="rowActions"
              class="pe-2 text-end whitespace-nowrap"
            >
              <button
                type="button"
                class="inline-flex size-9 items-center justify-center rounded-full text-muted-foreground hover:bg-highlight hover:text-foreground"
                :aria-label="$t('data-pages.edit-item', { name: itemName(item) })"
                :title="$t('general.edit')"
                @click="$emit('edit-one', item)"
              >
                <PencilIcon class="size-4" />
              </button>
              <button
                type="button"
                class="inline-flex size-9 items-center justify-center rounded-full text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                :aria-label="$t('data-pages.delete-item', { name: itemName(item) })"
                :title="$t('general.delete')"
                @click="$emit('delete-one', item)"
              >
                <Trash2Icon class="size-4" />
              </button>
            </td>
          </tr>
          <tr v-if="!pageItems.length">
            <td
              :colspan="visibleHeaders.length + 2"
              class="px-4 py-10 text-center text-sm text-muted-foreground"
            >
              <span
                v-if="loading"
                class="inline-flex items-center gap-2"
              >
                <LoaderCircleIcon class="size-4 animate-spin" />
                {{ $t('general.loading') }}
              </span>
              <template v-else>
                {{ search ? $t('search.no-results') : $t('data-pages.nothing-here-yet') }}
              </template>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- footer -->
    <div class="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-muted-foreground">
      <slot name="button-bottom" />
      <span class="ms-auto tabular-nums">
        {{ $t('data-pages.range-of-total', { start: rangeStart, end: rangeEnd, total: filtered.length }) }}
      </span>
      <label class="flex items-center gap-2">
        {{ $t('data-pages.per-page') }}
        <select
          v-model.number="pageSize"
          class="h-9 rounded-control border border-input bg-card px-2 text-foreground"
        >
          <option
            v-for="size in PAGE_SIZES"
            :key="size"
            :value="size"
          >
            {{ size === -1 ? $t('data-pages.all-rows') : size }}
          </option>
        </select>
      </label>
      <div class="flex items-center gap-1">
        <button
          type="button"
          class="inline-flex size-9 items-center justify-center rounded-full hover:bg-highlight disabled:opacity-40"
          :disabled="page <= 1"
          :aria-label="$t('general.previous')"
          @click="page -= 1"
        >
          <ChevronLeftIcon class="size-4 rtl:rotate-180" />
        </button>
        <button
          type="button"
          class="inline-flex size-9 items-center justify-center rounded-full hover:bg-highlight disabled:opacity-40"
          :disabled="page >= pageCount"
          :aria-label="$t('general.next')"
          @click="page += 1"
        >
          <ChevronRightIcon class="size-4 rtl:rotate-180" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  ArrowUpDownIcon,
  ArrowUpIcon,
  CheckIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  DownloadIcon,
  EllipsisIcon,
  LoaderCircleIcon,
  MinusIcon,
  PencilIcon,
  SearchIcon,
  Trash2Icon,
} from "@lucide/vue";
import { Button } from "~/components/ui/button";
import { Checkbox } from "~/components/ui/checkbox";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "~/components/ui/dropdown-menu";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { downloadAsJson, normalize } from "~/composables/use-utils";

export interface TableConfig {
  hideColumns: boolean;
  canExport: boolean;
}

export interface TableHeaders {
  text: string;
  value: string;
  show: boolean;
  align?: "start" | "center" | "end";
  sortable?: boolean;
  sort?: (a: any, b: any) => number;
}

export interface BulkAction {
  icon: string;
  text: string;
  event: string;
}

const props = defineProps({
  tableConfig: {
    type: Object as () => TableConfig,
    default: () => ({
      hideColumns: false,
      canExport: false,
    }),
  },
  headers: {
    type: Array as () => TableHeaders[],
    required: true,
  },
  data: {
    type: Array as () => any[],
    required: true,
  },
  bulkActions: {
    type: Array as () => BulkAction[],
    default: () => [],
  },
  initialSort: {
    type: String,
    default: "id",
  },
  initialSortDesc: {
    type: Boolean,
    default: false,
  },
  /** Per-row Edit and Delete buttons. */
  rowActions: {
    type: Boolean,
    default: true,
  },
  /** Leave the rows selected after a bulk action, for pages whose actions open a dialog first. */
  keepSelection: {
    type: Boolean,
    default: false,
  },
  loading: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits<{
  (e: "delete-one" | "edit-one", item: any): void;
  (e: "bulk-action", event: string, items: any[]): void;
}>();

// ===========================================================
// Columns
// A local copy, so hiding a column here doesn't change the page's header config
const localHeaders = ref(props.headers.map(h => ({ ...h })));
watch(() => props.headers, (headers) => {
  localHeaders.value = headers.map(h => ({ ...h }));
}, { deep: true });

const visibleHeaders = computed(() => localHeaders.value.filter(h => h.show));

function alignClass(align?: TableHeaders["align"]) {
  return align === "center" ? "text-center" : align === "end" ? "text-end" : "text-start";
}

function rowKey(item: any) {
  return item.id ?? item.slug ?? item.name;
}

function itemName(item: any) {
  return item.name || item.title || item.id || "";
}

// ===========================================================
// Search: every visible column's text, accent- and case-insensitive
const search = ref("");
const filtered = computed(() => {
  const query = normalize(search.value.trim());
  if (!query) {
    return props.data || [];
  }
  return (props.data || []).filter(item => visibleHeaders.value.some((h) => {
    const value = item[h.value];
    if (value === null || value === undefined) {
      return false;
    }
    const text = typeof value === "object" ? (value.name ?? JSON.stringify(value)) : String(value);
    return normalize(text).includes(query);
  }));
});

// ===========================================================
// Sort
const sortKey = ref(props.initialSort);
const sortDesc = ref(props.initialSortDesc);

function toggleSort(key: string) {
  if (sortKey.value !== key) {
    sortKey.value = key;
    sortDesc.value = false;
  }
  else if (!sortDesc.value) {
    sortDesc.value = true;
  }
  else {
    // third click goes back to the unsorted order
    sortKey.value = "";
    sortDesc.value = false;
  }
}

function compareValues(a: unknown, b: unknown) {
  if (a === b) {
    return 0;
  }
  if (a === null || a === undefined || a === "") {
    return 1;
  }
  if (b === null || b === undefined || b === "") {
    return -1;
  }
  if (typeof a === "number" && typeof b === "number") {
    return a - b;
  }
  if (typeof a === "boolean" && typeof b === "boolean") {
    return a === b ? 0 : a ? -1 : 1;
  }
  const textA = typeof a === "object" ? String((a as { name?: string }).name ?? "") : String(a);
  const textB = typeof b === "object" ? String((b as { name?: string }).name ?? "") : String(b);
  return textA.localeCompare(textB, undefined, { numeric: true, sensitivity: "base" });
}

const sorted = computed(() => {
  if (!sortKey.value) {
    return filtered.value;
  }
  const header = localHeaders.value.find(h => h.value === sortKey.value);
  const key = sortKey.value;
  const list = [...filtered.value].sort((a, b) => (header?.sort ? header.sort(a[key], b[key]) : compareValues(a[key], b[key])));
  return sortDesc.value ? list.reverse() : list;
});

// ===========================================================
// Pages
const PAGE_SIZES = [15, 30, 60, -1];
const pageSize = ref(15);
const page = ref(1);
const pageCount = computed(() => (pageSize.value === -1 ? 1 : Math.max(1, Math.ceil(sorted.value.length / pageSize.value))));
watch([search, pageSize], () => {
  page.value = 1;
});
watch(pageCount, (count) => {
  if (page.value > count) {
    page.value = count;
  }
});
const pageItems = computed(() => (pageSize.value === -1
  ? sorted.value
  : sorted.value.slice((page.value - 1) * pageSize.value, page.value * pageSize.value)));
const rangeStart = computed(() => (sorted.value.length ? (pageSize.value === -1 ? 1 : (page.value - 1) * pageSize.value + 1) : 0));
const rangeEnd = computed(() => (pageSize.value === -1 ? sorted.value.length : Math.min(page.value * pageSize.value, sorted.value.length)));

// ===========================================================
// Selection
// Bound so a page can keep acting on the rows (its bulk dialogs read them after the event)
const selected = defineModel<any[]>("selected", { default: () => [] });
const selectedKeys = computed(() => new Set(selected.value.map(rowKey)));

function isSelected(item: any) {
  return selectedKeys.value.has(rowKey(item));
}

function toggleItem(item: any) {
  selected.value = isSelected(item)
    ? selected.value.filter(i => rowKey(i) !== rowKey(item))
    : [...selected.value, item];
}

const allPageSelected = computed(() => pageItems.value.length > 0 && pageItems.value.every(isSelected));
const somePageSelected = computed(() => pageItems.value.some(isSelected));

function togglePage() {
  if (allPageSelected.value) {
    const pageKeys = new Set(pageItems.value.map(rowKey));
    selected.value = selected.value.filter(i => !pageKeys.has(rowKey(i)));
  }
  else {
    selected.value = [...selected.value, ...pageItems.value.filter(i => !isSelected(i))];
  }
}

// Rows that disappear from the data (deleted elsewhere) drop out of the selection
watch(() => props.data, (data) => {
  const keys = new Set((data || []).map(rowKey));
  selected.value = selected.value.filter(i => keys.has(rowKey(i)));
});

function runBulk(action: BulkAction) {
  emit("bulk-action", action.event, selected.value);
  if (!props.keepSelection) {
    selected.value = [];
  }
}
</script>
