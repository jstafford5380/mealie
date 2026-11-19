<script setup lang="ts">
import type { FormValidationRule } from "~/types/auto-forms";
import { useFieldValidation } from "~/composables/forms/use-field-validation";
import { cn } from "~/lib/utils";
import FormFieldShell from "./FormFieldShell.vue";

defineOptions({ inheritAttrs: false });

const props = withDefaults(defineProps<{
  label?: string;
  hint?: string;
  placeholder?: string;
  name?: string;
  rules?: FormValidationRule[];
  errorMessages?: string | string[];
  validateOn?: string;
  readonly?: boolean;
  disabled?: boolean;
  rows?: number | string;
  /** Grow with the content instead of scrolling. */
  autoGrow?: boolean;
  required?: boolean;
}>(), {
  rows: 3,
  autoGrow: true,
  rules: () => [],
});

const model = defineModel<string | null | undefined>();

const field = useFieldValidation(model as Ref<unknown>, {
  rules: () => props.rules,
  errorMessages: () => props.errorMessages,
  name: () => props.name,
  validateOn: () => props.validateOn,
  disabled: () => props.disabled || undefined,
  readonly: () => props.readonly || undefined,
});

const inputId = computed(() => `input-${field.id.value}`);
const describedBy = computed(() => {
  if (field.visibleError.value) {
    return `${inputId.value}-error`;
  }
  return props.hint ? `${inputId.value}-hint` : undefined;
});

// Auto-grow: CSS field-sizing where supported, otherwise resize to the content height.
const textareaEl = ref<HTMLTextAreaElement | null>(null);
const supportsFieldSizing = typeof CSS !== "undefined" && CSS.supports("field-sizing", "content");
function fitContent() {
  const el = textareaEl.value;
  if (!props.autoGrow || supportsFieldSizing || !el) {
    return;
  }
  el.style.height = "auto";
  el.style.height = `${el.scrollHeight + 2}px`;
}
watch(model, () => nextTick(fitContent));
onMounted(fitContent);

defineExpose({ validate: field.validate, reset: field.reset, resetValidation: field.resetValidation });
</script>

<template>
  <FormFieldShell
    :id="inputId"
    :label="label"
    :hint="hint"
    :error="field.visibleError.value"
    :required="required"
    :disabled="field.isDisabled.value"
  >
    <textarea
      :id="inputId"
      ref="textareaEl"
      v-model="model"
      v-bind="$attrs"
      :name="name"
      :rows="rows"
      :placeholder="placeholder"
      :readonly="field.isReadonly.value"
      :disabled="field.isDisabled.value"
      :required="required"
      :aria-invalid="field.visibleError.value ? 'true' : undefined"
      :aria-describedby="describedBy"
      :class="cn(
        'w-full min-w-0 rounded-control border border-input bg-card px-3 py-2.5 text-base leading-relaxed text-foreground outline-none transition-[color,box-shadow] placeholder:text-muted-foreground md:text-[15px]',
        'focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/25 disabled:cursor-not-allowed disabled:opacity-60',
        autoGrow ? 'field-sizing-content resize-none' : 'resize-y',
        field.visibleError.value && 'border-destructive focus-visible:border-destructive focus-visible:ring-destructive/20',
        field.isReadonly.value && 'bg-muted',
      )"
      :style="autoGrow ? { minHeight: `calc(${rows}lh + 1.25rem)` } : undefined"
      @blur="field.onBlur"
    />
  </FormFieldShell>
</template>
