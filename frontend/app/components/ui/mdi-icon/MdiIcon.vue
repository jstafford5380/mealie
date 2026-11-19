<script setup lang="ts">
import type { HTMLAttributes } from "vue";
import { cn } from "~/lib/utils";

/**
 * Renders an @mdi/js path string (the values in `$globals.icons`) as an inline SVG.
 * Decorative by default; pass `label` when the icon is the only content of a control.
 */
const props = defineProps<{
  path?: string | null;
  label?: string;
  class?: HTMLAttributes["class"];
}>();
</script>

<template>
  <svg
    v-if="props.path"
    data-slot="mdi-icon"
    viewBox="0 0 24 24"
    fill="currentColor"
    :role="props.label ? 'img' : undefined"
    :aria-label="props.label"
    :aria-hidden="props.label ? undefined : 'true'"
    :class="cn('size-5 shrink-0', props.class)"
  >
    <path :d="props.path" />
  </svg>
</template>
