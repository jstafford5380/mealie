<template>
  <span
    v-bind="$attrs"
    class="inline-flex h-6 max-w-full items-center rounded-full px-2.5 font-sans text-[13px] font-semibold"
    :class="!label.color && 'bg-subtle text-subtle-foreground'"
    :style="label.color ? { backgroundColor: label.color, color: readableForeground(label.color) } : undefined"
  >
    <span class="truncate">{{ label.name }}</span>
  </span>
</template>

<script setup lang="ts">
import { readableForeground } from "~/lib/color";
import type { MultiPurposeLabelSummary } from "~/lib/api/types/recipe";

defineProps<{
  label: MultiPurposeLabelSummary;
}>();
</script>
