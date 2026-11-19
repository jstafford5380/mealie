<template>
  <div
    data-slot="card-section-title"
    class="flex flex-col pb-3"
    :class="{ 'mt-8': section }"
  >
    <component
      :is="size === 'large' ? 'h2' : 'h3'"
      class="flex items-center gap-2 font-semibold tracking-tight text-foreground"
      :class="titleClass"
    >
      <slot name="prepend-title" />
      <MdiIcon
        v-if="icon"
        :path="icon"
        class="size-5 text-muted-foreground"
      />
      {{ title }}
      <slot name="append-title" />
    </component>
    <p
      v-if="$slots.default"
      class="mt-1.5 mb-0 max-w-[70ch] text-[15px] leading-relaxed text-muted-foreground"
    >
      <slot />
    </p>
    <Separator class="mt-3" />
  </div>
</template>

<script setup lang="ts">
import { MdiIcon } from "~/components/ui/mdi-icon";
import { Separator } from "~/components/ui/separator";

type Size = "large" | "medium" | "small";

const props = defineProps({
  title: {
    type: String,
    required: true,
  },
  size: {
    type: String as () => Size,
    default: "large",
  },
  icon: {
    type: String,
    default: "",
  },
  section: {
    type: Boolean,
    default: false,
  },
});

const titleClass = computed(() => {
  switch (props.size) {
    case "small":
      return "text-base";
    case "medium":
      return "text-lg";
    default:
      return "text-xl";
  }
});
</script>
