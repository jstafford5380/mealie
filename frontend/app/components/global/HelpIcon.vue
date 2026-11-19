<template>
  <div class="inline-flex">
    <Popover v-model:open="open">
      <PopoverTrigger as-child>
        <Button
          variant="ghost"
          :size="small ? 'icon-sm' : 'icon'"
          :aria-label="$t('general.help')"
          @click.stop
          @mouseenter="open = true"
        >
          <MdiIcon
            :path="$globals.icons.help"
            :class="small ? 'size-[18px]' : 'size-5'"
          />
        </Button>
      </PopoverTrigger>
      <PopoverContent
        side="top"
        :align="right ? 'start' : 'end'"
        class="max-w-[300px] text-sm leading-relaxed"
        @mouseleave="open = false"
      >
        <slot />
      </PopoverContent>
    </Popover>
  </div>
</template>

<script setup lang="ts">
import { Button } from "~/components/ui/button";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { Popover, PopoverContent, PopoverTrigger } from "~/components/ui/popover";

defineProps({
  small: {
    type: Boolean,
    default: false,
  },
  right: {
    type: Boolean,
    default: false,
  },
});

const open = ref(false);
</script>
