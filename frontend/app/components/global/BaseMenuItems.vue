<template>
  <template
    v-for="(child, idx) in children"
    :key="idx"
  >
    <DropdownMenuSub v-if="child.children">
      <DropdownMenuSubTrigger :disabled="child.disabled">
        <MdiIcon
          :path="child.icon"
          class="size-[18px] text-muted-foreground"
        />
        {{ child.text }}
      </DropdownMenuSubTrigger>
      <DropdownMenuSubContent class="max-h-[80vh] min-w-48 overflow-y-auto">
        <BaseMenuItems
          :children="child.children"
          @menu="(childEvent) => $emit('menu', childEvent)"
        />
      </DropdownMenuSubContent>
    </DropdownMenuSub>
    <DropdownMenuItem
      v-else
      :disabled="child.disabled"
      @select="$emit('menu', child.event)"
    >
      <MdiIcon
        :path="child.icon"
        class="size-[18px] text-muted-foreground"
      />
      {{ child.text }}
    </DropdownMenuItem>
    <DropdownMenuSeparator v-if="child.divider" />
  </template>
</template>

<script setup lang="ts">
import type { ButtonOption } from "./BaseMenu.vue";
import {
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
} from "~/components/ui/dropdown-menu";
import { MdiIcon } from "~/components/ui/mdi-icon";

defineEmits<{
  menu: [string];
}>();

defineProps<{
  children: ButtonOption[];
}>();
</script>
