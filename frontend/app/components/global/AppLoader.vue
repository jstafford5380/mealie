<template>
  <div
    data-slot="app-loader"
    role="status"
    aria-live="polite"
    class="mx-auto my-3 flex flex-col items-center justify-center gap-3 text-center"
  >
    <Loader2Icon
      aria-hidden="true"
      class="animate-spin text-primary motion-reduce:animate-none"
      :class="sizeClass"
    />
    <div
      class="text-muted-foreground"
      :class="large ? 'text-lg' : 'text-[15px]'"
    >
      <slot>
        {{ (small || tiny) ? "" : waitingTextCalculated }}
      </slot>
      <span
        v-if="(small || tiny) && !$slots.default"
        class="sr-only"
      >{{ waitingTextCalculated }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Loader2Icon } from "@lucide/vue";

const props = defineProps({
  loading: {
    type: Boolean,
    default: true,
  },
  tiny: {
    type: Boolean,
    default: false,
  },
  small: {
    type: Boolean,
    default: false,
  },
  medium: {
    type: Boolean,
    default: true,
  },
  large: {
    type: Boolean,
    default: false,
  },
  waitingText: {
    type: String,
    default: undefined,
  },
});

const sizeClass = computed(() => {
  if (props.tiny) {
    return "size-5";
  }
  if (props.small) {
    return "size-8";
  }
  if (props.large) {
    return "size-16";
  }
  return "size-11";
});

const i18n = useI18n();
const waitingTextCalculated = props.waitingText == null ? i18n.t("general.loading") : props.waitingText;
</script>
