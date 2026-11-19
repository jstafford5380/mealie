<template>
  <div class="flex w-full flex-col gap-1.5 py-1.5 font-sans">
    <span
      v-if="label"
      class="text-sm font-semibold text-foreground"
    >{{ label }}</span>
    <SearchSelect
      v-model="selected"
      v-model:search="search"
      :items="filtered"
      :item-title="itemTitle"
      :item-key="itemKey"
      :placeholder="placeholder"
      :aria-label="label || placeholder"
      :clearable="clearable"
      :disabled="disabled"
      :autofocus="autofocus"
    >
      <template
        v-if="$slots.item"
        #item="slotProps"
      >
        <slot
          name="item"
          v-bind="slotProps"
        />
      </template>
    </SearchSelect>
  </div>
</template>

<script setup lang="ts" generic="T extends Record<string, any>">
import SearchSelect from "./SearchSelect.vue";
import { normalize } from "~/composables/use-utils";

/**
 * A labelled SearchSelect over a local list, filtered accent- and case-insensitively.
 * With `itemValue`, the model holds that field of the chosen item instead of the item.
 */
const props = withDefaults(defineProps<{
  items: T[];
  label?: string;
  placeholder?: string;
  itemTitle?: string;
  itemKey?: string;
  itemValue?: string;
  clearable?: boolean;
  disabled?: boolean;
  autofocus?: boolean;
}>(), {
  itemTitle: "name",
  itemKey: "id",
  clearable: true,
});

const model = defineModel<any>();
const search = ref("");

const filtered = computed(() => {
  const term = normalize(search.value.trim());
  const items = props.items || [];
  return term ? items.filter(i => normalize(String(i[props.itemTitle] ?? "")).includes(term)) : items;
});

const selected = computed<T | null>({
  get() {
    if (!props.itemValue) {
      return model.value ?? null;
    }
    return (props.items || []).find(i => i[props.itemValue!] === model.value) ?? null;
  },
  set(item) {
    model.value = props.itemValue ? (item ? item[props.itemValue] : null) : item;
  },
});
</script>
