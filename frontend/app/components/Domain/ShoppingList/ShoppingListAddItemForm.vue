<template>
  <!-- Docked above the bottom tab bar; it grows upward when "more options" opens, and its
       Save button scrolls with the options instead of falling below the screen. -->
  <div
    ref="target"
    class="fixed inset-x-3 z-[950] max-h-[calc(100dvh-9rem)] overflow-y-auto rounded-panel bg-background/95 p-1 shadow-lg backdrop-blur"
    :style="{ bottom: 'calc(5.25rem + env(safe-area-inset-bottom))' }"
  >
    <ShoppingListQuickAdd
      v-model="listItem"
      v-model:details="showDetails"
      suggestions-above
      :foods="foods"
      :labels="labels"
      :units="units"
      @save="$emit('save')"
    />
  </div>
</template>

<script setup lang="ts">
import type { ShoppingListItemOut } from "~/lib/api/types/household";
import type { MultiPurposeLabelOut } from "~/lib/api/types/labels";
import type { IngredientFoodOut, IngredientUnitOut } from "~/lib/api/types/recipe";
import ShoppingListQuickAdd from "./ShoppingListQuickAdd.vue";
import { onClickOutside } from "@vueuse/core";

// modelValue as reactive v-model
const listItem = defineModel<ShoppingListItemOut>({ required: true });

defineProps({
  labels: {
    type: Array as () => MultiPurposeLabelOut[],
    required: true,
  },
  units: {
    type: Array as () => IngredientUnitOut[],
    required: true,
  },
  foods: {
    type: Array as () => IngredientFoodOut[],
    required: true,
  },
});

defineEmits<{
  (e: "save"): void;
}>();

// The drawer only grows when "more options" is open; otherwise it's just the add field
const showDetails = ref(false);

const target = ref();
// Autocomplete menus are teleported outside the drawer, so selecting an item
// would otherwise register as an outside click and collapse the form
onClickOutside(target, () => showDetails.value = false, { ignore: [".v-overlay-container", "[data-reka-popper-content-wrapper]", "[role=listbox]"] });
</script>
