<template>
  <DropdownMenu :modal="false">
    <DropdownMenuTrigger as-child>
      <slot
        name="activator"
        v-bind="{ props: {} }"
      >
        <Button
          variant="ghost"
          :size="large ? 'icon-lg' : 'icon'"
          :aria-label="activator.text"
          :class="cn(stretch && 'w-full', colorClass(activator.color))"
          :disabled="activator.disabled"
        >
          <Spinner
            v-if="activator.loading || children.some(({ loading }) => loading)"
            class="size-5"
          />
          <MdiIcon
            v-else
            :path="activator.icon"
            class="size-[22px]"
          />
        </Button>
      </slot>
    </DropdownMenuTrigger>
    <DropdownMenuContent
      align="start"
      class="max-h-[80vh] min-w-48 overflow-y-auto"
    >
      <BaseMenuItems
        :children="children"
        @menu="(childEvent) => $emit('menu', childEvent)"
      />
    </DropdownMenuContent>
  </DropdownMenu>
</template>

<script setup lang="ts">
import { Button } from "~/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuTrigger } from "~/components/ui/dropdown-menu";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { Spinner } from "~/components/ui/spinner";
import { cn } from "~/lib/utils";
import BaseMenuItems from "./BaseMenuItems.vue";

export interface ButtonOption {
  icon?: string;
  color?: string;
  text: string;
  event: string;
  children?: ButtonOption[];
  disabled?: boolean;
  divider?: boolean;
  loading?: boolean;
}

defineEmits<{
  menu: [string];
}>();

withDefaults(defineProps<{
  activator: ButtonOption;
  children: ButtonOption[];
  large?: boolean;
  stretch?: boolean;
}>(), {
  large: true,
  stretch: false,
});

function colorClass(color?: string) {
  switch (color) {
    case "error":
    case "red":
      return "text-destructive hover:text-destructive";
    case "success":
    case "primary":
      return "text-primary hover:text-primary";
    case "warning":
      return "text-brand-strong hover:text-brand-strong";
    default:
      return undefined;
  }
}
</script>
