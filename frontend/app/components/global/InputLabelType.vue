<template>
  <div class="flex min-w-0 flex-col gap-1.5 font-sans">
    <span
      v-if="label"
      :id="labelId"
      class="text-sm font-semibold"
    >{{ label }}</span>
    <SearchSelect
      v-model="itemVal"
      v-model:search="searchInput"
      :items="filteredItems"
      :placeholder="placeholder || label"
      :aria-label="label"
      :creatable="create"
      :autofocus="autofocus"
      @create="emitCreate"
    />
  </div>
</template>

<script setup lang="ts">
import SearchSelect from "~/components/ui/field/SearchSelect.vue";
import type { MultiPurposeLabelSummary } from "~/lib/api/types/labels";
import type { IngredientFoodOut, IngredientUnitOut } from "~/lib/api/types/recipe";
import { useSearch } from "~/composables/use-search";

// v-model for the selected item
const modelValue = defineModel<MultiPurposeLabelSummary | IngredientFoodOut | IngredientUnitOut | null>({ default: () => null });

// support v-model:item-id binding
const itemId = defineModel<string | null | undefined>("item-id", { default: undefined });

const props = defineProps({
  items: {
    type: Array as () => Array<MultiPurposeLabelSummary | IngredientFoodOut | IngredientUnitOut>,
    required: true,
  },
  icon: {
    type: String,
    required: false,
    default: undefined,
  },
  create: {
    type: Boolean,
    default: false,
  },
  label: {
    type: String,
    default: "",
  },
  placeholder: {
    type: String,
    default: "",
  },
  autofocus: {
    type: Boolean,
    default: false,
  },
});

const labelId = `label-${useId()}`;

const emit = defineEmits<{
  (e: "create", val: string): void;
}>();

// Use the search composable
const { search: searchInput, filtered: filteredItems } = useSearch(computed(() => props.items));

const itemVal = computed({
  get: () => {
    if (!modelValue.value || Object.keys(modelValue.value).length === 0) {
      return null;
    }
    return modelValue.value;
  },
  set: (val: MultiPurposeLabelSummary | IngredientFoodOut | IngredientUnitOut | null | undefined) => {
    itemId.value = val?.id ?? null;
    modelValue.value = val ?? null;
  },
});

function emitCreate(name?: string) {
  const value = (name ?? searchInput.value).trim();
  if (!value || props.items.some(item => item.name === value)) {
    return;
  }
  emit("create", value);
  searchInput.value = "";
}
</script>
