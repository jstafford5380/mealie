<template>
  <span
    class="inline-flex shrink-0 items-center justify-center overflow-hidden bg-brand text-brand-foreground"
    :style="{ width: `${size}px`, height: `${size}px`, borderRadius: `${Math.round(size * 0.28)}px` }"
  >
    <slot>
      <img
        v-if="$appInfo.brandingLogoUrl"
        :src="$appInfo.brandingLogoUrl"
        alt=""
        class="size-full object-contain"
      >
      <MdiIcon
        v-else
        :path="$globals.icons.primary"
        :style="{ width: `${Math.round(size * 0.6)}px`, height: `${Math.round(size * 0.6)}px` }"
      />
    </slot>
  </span>
</template>

<script setup lang="ts">
import { MdiIcon } from "~/components/ui/mdi-icon";

withDefaults(defineProps<{ size?: number }>(), { size: 56 });
</script>
