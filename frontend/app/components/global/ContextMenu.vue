<template>
  <DropdownMenu :modal="false">
    <DropdownMenuTrigger as-child>
      <Button
        variant="ghost"
        size="icon-sm"
        class="print:hidden"
        :aria-label="$t('general.actions')"
        @click.prevent
      >
        <MdiIcon
          :path="$globals.icons.dotsVertical"
          class="size-5"
        />
      </Button>
    </DropdownMenuTrigger>
    <DropdownMenuContent
      :side="menuTop ? 'top' : 'bottom'"
      align="start"
      :side-offset="5"
      class="min-w-44 print:hidden"
    >
      <DropdownMenuItem
        v-for="(item, index) in items"
        :key="index"
        @select="$emit(item.event)"
      >
        <MdiIcon
          :path="item.icon"
          class="size-[18px]"
          :class="iconColor(item.color)"
        />
        {{ item.title }}
      </DropdownMenuItem>
    </DropdownMenuContent>
  </DropdownMenu>
</template>

<script setup lang="ts">
import type { ContextMenuItem } from "~/composables/use-context-presents";
import { Button } from "~/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "~/components/ui/dropdown-menu";
import { MdiIcon } from "~/components/ui/mdi-icon";

defineProps({
  items: {
    type: Array as () => ContextMenuItem[],
    required: true,
  },
  menuTop: {
    type: Boolean,
    default: true,
  },
});

function iconColor(color?: string) {
  switch (color) {
    case "error":
    case "red":
      return "text-destructive";
    case "success":
    case "primary":
      return "text-primary";
    case "warning":
      return "text-brand-strong";
    default:
      return "text-muted-foreground";
  }
}
</script>
