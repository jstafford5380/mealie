<template>
  <component
    :is="to ? NuxtLink : 'div'"
    :to="to || undefined"
    data-slot="stats-card"
    class="flex items-center gap-3 rounded-card border bg-card p-4 font-sans text-card-foreground"
    :class="to && 'transition-colors hover:border-primary/40 hover:bg-highlight/40 focus-visible:outline-2 focus-visible:outline-offset-2'"
    :style="minWidth ? { minWidth } : undefined"
  >
    <span class="flex size-10 shrink-0 items-center justify-center rounded-control bg-highlight text-highlight-foreground">
      <MdiIcon
        :path="activeIcon"
        class="size-[22px]"
      />
    </span>
    <span class="flex min-w-0 flex-col">
      <span class="text-sm text-muted-foreground">
        <slot name="title" />
      </span>
      <span class="text-xl font-bold tabular-nums">
        <slot name="value" />
      </span>
    </span>
  </component>
</template>

<script setup lang="ts">
import { MdiIcon } from "~/components/ui/mdi-icon";

const props = defineProps({
  icon: {
    type: String,
    default: null,
  },
  minWidth: {
    type: String,
    default: "",
  },
  to: {
    type: String,
    default: null,
  },
});

const NuxtLink = resolveComponent("NuxtLink");
const { $globals } = useNuxtApp();

const activeIcon = computed(() => {
  return props.icon ?? $globals.icons.primary;
});
</script>
