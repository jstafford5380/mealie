<template>
  <div
    data-slot="page-title"
    class="mt-4 flex flex-col gap-3"
  >
    <slot name="header" />
    <section class="flex flex-col gap-1">
      <h1 class="m-0 text-2xl font-bold tracking-tight text-foreground sm:text-[28px]">
        <slot name="title">
          👋 Here's a Title
        </slot>
      </h1>
      <div
        v-if="$slots.default"
        class="max-w-[70ch] text-[15px] leading-relaxed text-muted-foreground"
      >
        <slot />
      </div>
    </section>
    <section
      v-if="$slots.content"
      class="flex"
    >
      <slot name="content" />
    </section>
    <Separator
      v-if="divider"
      class="my-2"
    />
  </div>
</template>

<script setup lang="ts">
import { Separator } from "~/components/ui/separator";

defineProps({
  divider: {
    type: Boolean,
    default: false,
  },
});
</script>
