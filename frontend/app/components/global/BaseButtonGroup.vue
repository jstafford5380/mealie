<template>
  <TooltipProvider :delay-duration="200">
    <div
      role="toolbar"
      class="flex items-center gap-0.5"
      :class="stretch && 'w-full'"
    >
      <template
        v-for="btn in buttons"
        :key="(btn.children ? 'menu-' : 'btn-') + btn.event"
      >
        <BaseMenu
          v-if="btn.children"
          :large="large"
          :activator="btn"
          :children="btn.children"
          :stretch="stretch"
          :style="stretch ? `width: ${maxButtonWidth};` : ''"
          @menu="(childEvent) => $emit(childEvent)"
        />
        <Tooltip v-else>
          <TooltipTrigger as-child>
            <Button
              variant="ghost"
              :size="large ? 'icon-lg' : 'icon'"
              :class="colorClass(btn.color)"
              :disabled="btn.disabled || btn.loading"
              :aria-label="btn.text"
              :aria-busy="btn.loading ? 'true' : undefined"
              :style="stretch ? `width: ${maxButtonWidth};` : ''"
              @click="$emit(btn.event)"
            >
              <Spinner
                v-if="btn.loading"
                class="size-5"
              />
              <MdiIcon
                v-else
                :path="btn.icon"
                class="size-[22px]"
              />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="bottom">
            {{ btn.text }}
          </TooltipContent>
        </Tooltip>
      </template>
    </div>
  </TooltipProvider>
</template>

<script setup lang="ts">
import type { ButtonOption } from "./BaseMenu.vue";
import { Button } from "~/components/ui/button";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { Spinner } from "~/components/ui/spinner";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "~/components/ui/tooltip";
import BaseMenu from "./BaseMenu.vue";

const props = defineProps({
  buttons: {
    type: Array as () => ButtonOption[],
    required: true,
  },
  large: {
    type: Boolean,
    default: true,
  },
  stretch: {
    type: Boolean,
    default: false,
  },
});

const maxButtonWidth = computed(() => `${100 / props.buttons.length}%`);

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
