<template>
  <div class="grid grid-cols-[minmax(0,5fr)_minmax(0,7fr)] gap-3 font-sans">
    <label class="flex flex-col gap-1.5">
      <span class="text-sm font-semibold">{{ $t('form.quantity-label-abbreviated') }}</span>
      <input
        :value="listItem.quantity ?? ''"
        type="number"
        min="0"
        step="any"
        inputmode="decimal"
        class="h-10 w-full rounded-control border border-input bg-card px-3 text-[15px] tabular-nums outline-none focus:border-ring focus:ring-3 focus:ring-ring/25"
        @input="listItem.quantity = Math.max(0, Number(($event.target as HTMLInputElement).value) || 0)"
        @keydown.enter.prevent="emit('save')"
      >
    </label>
    <InputLabelType
      v-model="listItem.unit"
      v-model:item-id="listItem.unitId!"
      :items="units"
      :label="$t('recipe.unit')"
      create
      @create="createAssignUnit"
    />
  </div>
  <label class="flex flex-col gap-1.5 font-sans">
    <span class="text-sm font-semibold">{{ $t('shopping-list.note') }}</span>
    <textarea
      v-model="listItem.note"
      rows="1"
      autocapitalize="none"
      class="field-sizing-content min-h-10 w-full resize-none rounded-control border border-input bg-card px-3 py-2 text-[15px] outline-none focus:border-ring focus:ring-3 focus:ring-ring/25"
      @keypress="handleNoteKeyPress"
    />
  </label>
  <div class="flex flex-wrap items-end gap-3 font-sans">
    <div class="min-w-48 flex-1">
      <InputLabelType
        v-model="listItem.label"
        v-model:item-id="listItem.labelId!"
        :items="labels"
        :label="$t('shopping-list.label')"
      />
    </div>
    <Button
      v-if="listItem.labelId && listItem.food && listItem.labelId !== listItem.food.labelId"
      variant="outline"
      @click="assignLabelToFood"
    >
      <MdiIcon
        :path="$globals.icons.tagArrowRight"
        class="size-4"
      />
      {{ $t('shopping-list.save-label') }}
    </Button>
  </div>
</template>

<script setup lang="ts">
import { Button } from "~/components/ui/button";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { useShoppingListItemEditor } from "~/composables/shopping-list-page/use-shopping-list-item-editor";
import type { ShoppingListItemOut } from "~/lib/api/types/household";
import type { MultiPurposeLabelOut } from "~/lib/api/types/labels";
import type { IngredientUnitOut } from "~/lib/api/types/recipe";

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
});

const emit = defineEmits<{ (e: "save"): void }>();

const { assignLabelToFood, createAssignUnit } = useShoppingListItemEditor(listItem);

function handleNoteKeyPress(event: KeyboardEvent) {
  // Save on Enter
  if (!event.shiftKey && event.key === "Enter") {
    event.preventDefault();
    emit("save");
  }
}
</script>
