<script setup lang="ts" generic="T extends Record<string, any>">
import { AlertCircleIcon, CheckIcon, ChevronDownIcon, PlusIcon, XIcon } from "@lucide/vue";
import {
  ComboboxAnchor,
  ComboboxContent,
  ComboboxEmpty,
  ComboboxInput,
  ComboboxItem,
  ComboboxPortal,
  ComboboxRoot,
  ComboboxTrigger,
  ComboboxViewport,
} from "reka-ui";
import { cn } from "~/lib/utils";

/**
 * Searchable single select over objects (units, foods, recipes...). The caller filters
 * `items` from the `search` model, so server-side search works the same as local search.
 * With `creatable`, a "Create …" option appears when the search matches nothing exactly.
 */
const props = withDefaults(defineProps<{
  items: T[];
  itemTitle?: string;
  itemKey?: string;
  placeholder?: string;
  ariaLabel?: string;
  clearable?: boolean;
  creatable?: boolean;
  disabled?: boolean;
  /** Marks the field as needing attention (e.g. the parser found no match). */
  warning?: string;
  emptyText?: string;
  autofocus?: boolean;
}>(), {
  itemTitle: "name",
  itemKey: "id",
  clearable: true,
  creatable: false,
  disabled: false,
});

const model = defineModel<T | null | undefined>();
const search = defineModel<string>("search", { default: "" });
const emit = defineEmits<{ create: [name: string]; focus: []; blur: [] }>();

const CREATE = { __create: true } as unknown as T;
const open = ref(false);

const title = (item: T | null | undefined) => (item ? String(item[props.itemTitle] ?? "") : "");
const showCreate = computed(() => {
  const term = search.value.trim().toLowerCase();
  return props.creatable && !!term && !props.items.some(i => title(i).toLowerCase() === term);
});

function onSelect(value: unknown) {
  if (value === CREATE || (value as any)?.__create) {
    emit("create", search.value.trim());
    return;
  }
  model.value = value as T;
}

function clear() {
  model.value = null;
  search.value = "";
}

function compare(a: T, b: T) {
  if (!a || !b) {
    return a === b;
  }
  return a[props.itemKey] !== undefined ? a[props.itemKey] === b[props.itemKey] : title(a) === title(b);
}
</script>

<template>
  <!-- Reka's root keeps no classes, so layout classes land on this wrapper. -->
  <div class="min-w-0">
    <ComboboxRoot
      v-model:open="open"
      :model-value="model ?? undefined"
      :by="compare"
      :disabled="disabled"
      ignore-filter
      open-on-click
      @update:model-value="onSelect"
    >
      <ComboboxAnchor
        :class="cn(
          'group/ss flex h-10 w-full min-w-0 items-center rounded-control border bg-card text-[15px] transition-colors focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/25 data-[disabled]:opacity-60',
          warning ? 'border-brand-strong/70' : 'border-input',
        )"
      >
        <span
          v-if="warning"
          class="ps-2.5 text-brand-strong"
          :title="warning"
        >
          <AlertCircleIcon
            class="size-4"
            aria-hidden="true"
          />
          <span class="sr-only">{{ warning }}</span>
        </span>
        <ComboboxInput
          v-model="search"
          :display-value="title"
          :placeholder="placeholder"
          :aria-label="ariaLabel || placeholder"
          :auto-focus="autofocus"
          class="h-full w-0 min-w-0 flex-1 bg-transparent px-3 outline-none placeholder:text-muted-foreground/80"
          @focus="emit('focus')"
          @blur="emit('blur')"
        />
        <button
          v-if="clearable && model && !disabled"
          type="button"
          class="inline-flex size-7 shrink-0 items-center justify-center rounded-item text-muted-foreground opacity-0 transition-opacity hover:bg-highlight hover:text-foreground focus-visible:opacity-100 group-focus-within/ss:opacity-100 group-hover/ss:opacity-100"
          :aria-label="$t('general.clear')"
          @click="clear"
        >
          <XIcon class="size-3.5" />
        </button>
        <ComboboxTrigger
          class="inline-flex h-full w-8 shrink-0 items-center justify-center text-muted-foreground"
          tabindex="-1"
        >
          <ChevronDownIcon class="size-4" />
        </ComboboxTrigger>
      </ComboboxAnchor>

      <ComboboxPortal>
        <ComboboxContent
          position="popper"
          :side-offset="4"
          align="start"
          class="z-[2400] max-h-[min(16rem,var(--reka-combobox-content-available-height))] w-[var(--reka-combobox-trigger-width)] min-w-56 overflow-hidden rounded-control border bg-popover font-sans text-popover-foreground shadow-md data-[state=open]:animate-in data-[state=open]:fade-in-0"
        >
          <ComboboxViewport class="max-h-[inherit] overflow-y-auto p-1">
            <ComboboxEmpty
              v-if="!showCreate"
              class="px-3 py-4 text-center text-sm text-muted-foreground"
            >
              {{ emptyText || (creatable ? $t('recipe.press-enter-to-create') : $t('search.no-results')) }}
            </ComboboxEmpty>
            <ComboboxItem
              v-for="item in items"
              :key="item[itemKey] ?? title(item)"
              :value="item"
              class="relative flex min-h-9 cursor-default select-none items-center gap-2 rounded-item px-2.5 py-1.5 text-[15px] outline-none data-[highlighted]:bg-highlight data-[highlighted]:text-highlight-foreground"
            >
              <span class="min-w-0 flex-1 truncate">
                <slot
                  name="item"
                  :item="item"
                >{{ title(item) }}</slot>
              </span>
              <CheckIcon
                v-if="model && compare(model, item)"
                class="size-4 text-primary"
              />
            </ComboboxItem>
            <ComboboxItem
              v-if="showCreate"
              :value="CREATE"
              class="relative flex min-h-9 cursor-default select-none items-center gap-2 rounded-item px-2.5 py-1.5 text-[15px] font-medium text-primary outline-none data-[highlighted]:bg-highlight"
            >
              <PlusIcon class="size-4" />
              {{ $t('general.create-name', { name: search.trim() }) }}
            </ComboboxItem>
          </ComboboxViewport>
        </ComboboxContent>
      </ComboboxPortal>
    </ComboboxRoot>
  </div>
</template>
