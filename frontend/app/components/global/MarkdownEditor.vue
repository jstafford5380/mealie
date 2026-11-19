<template>
  <div class="flex flex-col gap-1.5 font-sans">
    <div
      v-if="label || displayPreview"
      class="flex items-center gap-2"
    >
      <span
        v-if="label"
        class="text-sm font-semibold"
      >{{ label }}</span>
      <button
        v-if="displayPreview"
        type="button"
        class="ms-auto inline-flex items-center gap-1.5 rounded-item px-2 py-1 text-xs font-semibold text-muted-foreground hover:bg-highlight hover:text-foreground"
        :aria-pressed="previewState"
        @click="previewState = !previewState"
      >
        <MdiIcon
          :path="previewState ? $globals.icons.edit : $globals.icons.eye"
          class="size-3.5"
        />
        {{ previewState ? $t('general.edit') : $t('markdown-editor.preview-markdown-button-label') }}
      </button>
    </div>
    <textarea
      v-if="!previewState"
      v-model="modelValue"
      rows="4"
      :aria-label="label || textareaProps.label || textareaProps.placeholder"
      :placeholder="textareaProps.placeholder"
      class="field-sizing-content min-h-24 w-full resize-y rounded-control border border-input bg-card px-3 py-2 text-[15.5px] leading-relaxed outline-none placeholder:text-muted-foreground/80 focus:border-ring focus:ring-3 focus:ring-ring/25"
    />
    <SafeMarkdown
      v-else
      class="min-h-24 rounded-control border border-dashed px-3 py-2 text-[15.5px] leading-relaxed [&_p]:m-0 [&_p+p]:mt-2 [&_img]:max-w-full [&_img]:rounded-item"
      :source="modelValue"
    />
    <span
      v-if="textareaProps.hint && !previewState"
      class="text-xs text-muted-foreground"
    >{{ textareaProps.hint }}</span>
  </div>
</template>

<script setup lang="ts">
import { MdiIcon } from "~/components/ui/mdi-icon";

const props = defineProps({
  label: {
    type: String,
    default: "",
  },
  preview: {
    type: Boolean,
    default: undefined,
  },
  displayPreview: {
    type: Boolean,
    default: true,
  },
  textarea: {
    type: Object as () => unknown,
    default: () => ({}),
  },
});

const emit = defineEmits<{
  (e: "input:preview", value: boolean): void;
}>();

const modelValue = defineModel<string>("modelValue");

// Vuetify textarea props the callers pass; only these are still meaningful.
const textareaProps = computed(() => (props.textarea ?? {}) as { hint?: string; placeholder?: string; label?: string });

const fallbackPreview = ref(false);
const previewState = computed({
  get: () => props.preview ?? fallbackPreview.value,
  set: (val: boolean) => {
    if (props.preview) {
      emit("input:preview", val);
    }
    else {
      fallbackPreview.value = val;
    }
  },
});
</script>
