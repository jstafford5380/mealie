<template>
  <div class="flex flex-col gap-3 rounded-card border border-s-4 border-s-primary bg-card p-3 font-sans">
    <InputLabelType
      v-model="listItem.food"
      v-model:item-id="listItem.foodId!"
      :items="foods"
      :label="$t('shopping-list.food')"
      :autofocus="autoFocus === 'food'"
      create
      @create="createAssignFood"
    />
    <ShoppingListItemDetails
      v-model="listItem"
      :labels="labels"
      :units="units"
      @save="$emit('save')"
    />
    <div class="flex flex-wrap items-center gap-2">
      <Button
        variant="ghost"
        class="text-destructive hover:text-destructive"
        @click="$emit('delete')"
      >
        <Trash2Icon class="size-4" />
        {{ $t('general.delete') }}
      </Button>
      <Button
        variant="ghost"
        class="ms-auto"
        @click="$emit('cancel')"
      >
        {{ $t('general.cancel') }}
      </Button>
      <Button @click="$emit('save')">
        {{ $t('general.save') }}
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Trash2Icon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import { useShoppingListItemEditor } from "~/composables/shopping-list-page/use-shopping-list-item-editor";
import type { ShoppingListItemOut } from "~/lib/api/types/household";
import type { MultiPurposeLabelOut } from "~/lib/api/types/labels";
import type { IngredientFoodOut, IngredientUnitOut } from "~/lib/api/types/recipe";
import ShoppingListItemDetails from "./ShoppingListItemDetails.vue";

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

// const emit = defineEmits<["save", "cancel", "delete"]>();
defineEmits<{
  (e: "save" | "cancel" | "delete"): void;
}>();

const { createAssignFood } = useShoppingListItemEditor(listItem);

watch(
  () => listItem.value.quantity,
  (newQty) => {
    if (!newQty) {
      listItem.value.quantity = 0;
    }
  },
);

watch(
  () => listItem.value.food,
  (newFood) => {
    listItem.value.label = newFood?.label || null;
    listItem.value.labelId = listItem.value.label?.id || null;
  },
);

const autoFocus = computed(() => (!listItem.value.food && listItem.value.note ? "note" : "food"));
</script>
