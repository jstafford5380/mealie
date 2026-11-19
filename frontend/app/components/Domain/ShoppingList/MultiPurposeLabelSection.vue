<template>
  <div class="handle flex min-h-11 cursor-grab touch-none items-center gap-3 rounded-control px-2 font-sans text-[15px] hover:bg-highlight/50 active:cursor-grabbing">
    <GripVerticalIcon class="size-4 shrink-0 text-muted-foreground" />
    <span
      class="size-3 shrink-0 rounded-full"
      :class="!labelColor && 'bg-muted-foreground/40'"
      :style="labelColor ? { backgroundColor: labelColor } : undefined"
      aria-hidden="true"
    />
    <span class="min-w-0 flex-1 truncate">{{ modelValue.label.name }}</span>
  </div>
</template>

<script setup lang="ts">
import { GripVerticalIcon } from "@lucide/vue";
import type { ShoppingListMultiPurposeLabelOut } from "~/lib/api/types/household";

const props = defineProps<{
  useColor?: boolean;
}>();
const modelValue = defineModel<ShoppingListMultiPurposeLabelOut>({ required: true });

const labelColor = ref<string | undefined>(props.useColor ? modelValue.value.label.color : undefined);
</script>
