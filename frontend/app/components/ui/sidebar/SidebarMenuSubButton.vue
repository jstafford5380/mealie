<script setup lang="ts">
import type { PrimitiveProps } from "reka-ui";
import type { HTMLAttributes } from "vue";
import { cn } from "~/lib/utils";
import { Primitive } from "reka-ui";

const props = withDefaults(defineProps<PrimitiveProps & {
  size?: "sm" | "md";
  isActive?: boolean;
  class?: HTMLAttributes["class"];
}>(), {
  as: "a",
  size: "md",
});
</script>

<template>
  <Primitive
    data-slot="sidebar-menu-sub-button"
    data-sidebar="menu-sub-button"
    :as="as"
    :as-child="asChild"
    :data-size="size"
    :data-active="isActive"
    :class="cn(
      'text-sidebar-foreground ring-sidebar-ring hover:bg-sidebar-highlight hover:text-sidebar-highlight-foreground active:bg-sidebar-highlight active:text-sidebar-highlight-foreground [&>svg]:text-sidebar-highlight-foreground flex h-7 min-w-0 -translate-x-px items-center gap-2 overflow-hidden rounded-control px-2 outline-hidden focus-visible:ring-2 disabled:pointer-events-none disabled:opacity-50 aria-disabled:pointer-events-none aria-disabled:opacity-50 [&>span:last-child]:truncate [&>svg]:size-4 [&>svg]:shrink-0',
      'data-[active=true]:bg-sidebar-highlight data-[active=true]:text-sidebar-highlight-foreground',
      size === 'sm' && 'text-xs',
      size === 'md' && 'text-sm',
      'group-data-[collapsible=icon]:hidden',
      props.class,
    )"
  >
    <slot />
  </Primitive>
</template>
