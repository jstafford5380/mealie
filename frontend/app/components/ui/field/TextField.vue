<script setup lang="ts">
import type { FormValidationRule } from "~/types/auto-forms";
import { EyeIcon, EyeOffIcon, XIcon } from "@lucide/vue";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { useFieldValidation } from "~/composables/forms/use-field-validation";
import { cn } from "~/lib/utils";
import FormFieldShell from "./FormFieldShell.vue";

defineOptions({ inheritAttrs: false });

const props = withDefaults(defineProps<{
  label?: string;
  hint?: string;
  placeholder?: string;
  type?: string;
  name?: string;
  rules?: FormValidationRule[];
  errorMessages?: string | string[];
  validateOn?: string;
  readonly?: boolean;
  disabled?: boolean;
  clearable?: boolean;
  autofocus?: boolean;
  autocomplete?: string;
  /** @mdi/js path shown inside the field, before the text. */
  prependIcon?: string;
  required?: boolean;
}>(), {
  type: "text",
  rules: () => [],
});

const model = defineModel<string | number | null | undefined>();
const emit = defineEmits<{ "click:clear": [] }>();

const field = useFieldValidation(model as Ref<unknown>, {
  rules: () => props.rules,
  errorMessages: () => props.errorMessages,
  name: () => props.name,
  validateOn: () => props.validateOn,
  disabled: () => props.disabled || undefined,
  readonly: () => props.readonly || undefined,
});

const inputId = computed(() => `input-${field.id.value}`);
const showPassword = ref(false);
const inputType = computed(() => (props.type === "password" && showPassword.value ? "text" : props.type));
const describedBy = computed(() => {
  if (field.visibleError.value) {
    return `${inputId.value}-error`;
  }
  return props.hint ? `${inputId.value}-hint` : undefined;
});

const inputEl = ref<HTMLInputElement | null>(null);
function clear() {
  model.value = null;
  emit("click:clear");
  inputEl.value?.focus();
}

defineExpose({ validate: field.validate, reset: field.reset, resetValidation: field.resetValidation, focus: () => inputEl.value?.focus() });
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
    <div
      :class="cn(
        'flex h-11 w-full items-center gap-2 rounded-control border border-input bg-card px-3 transition-[color,box-shadow]',
        'focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/25',
        field.visibleError.value && 'border-destructive focus-within:border-destructive focus-within:ring-destructive/20',
        field.isDisabled.value && 'cursor-not-allowed opacity-60',
        field.isReadonly.value && 'bg-muted',
      )"
    >
      <MdiIcon
        v-if="prependIcon"
        :path="prependIcon"
        class="size-[18px] text-muted-foreground"
      />
      <input
        :id="inputId"
        ref="inputEl"
        v-model="model"
        v-bind="$attrs"
        :type="inputType"
        :name="name"
        :placeholder="placeholder"
        :readonly="field.isReadonly.value"
        :disabled="field.isDisabled.value"
        :autofocus="autofocus"
        :autocomplete="autocomplete"
        :required="required"
        :aria-invalid="field.visibleError.value ? 'true' : undefined"
        :aria-describedby="describedBy"
        class="h-full min-w-0 flex-1 border-0 bg-transparent text-base text-foreground outline-none placeholder:text-muted-foreground disabled:cursor-not-allowed md:text-[15px]"
        @blur="field.onBlur"
      >
      <button
        v-if="clearable && model !== null && model !== undefined && model !== '' && !field.isReadonly.value && !field.isDisabled.value"
        type="button"
        class="inline-flex size-7 items-center justify-center rounded-item text-muted-foreground hover:bg-highlight hover:text-highlight-foreground"
        :aria-label="$t('general.clear')"
        @click="clear"
      >
        <XIcon class="size-4" />
      </button>
      <button
        v-if="type === 'password'"
        type="button"
        class="inline-flex size-8 items-center justify-center rounded-item text-muted-foreground hover:bg-highlight hover:text-highlight-foreground"
        :aria-label="showPassword ? $t('user.hide-password') : $t('user.show-password')"
        :aria-pressed="showPassword"
        @click="showPassword = !showPassword"
      >
        <EyeOffIcon
          v-if="showPassword"
          class="size-[18px]"
        />
        <EyeIcon
          v-else
          class="size-[18px]"
        />
      </button>
      <slot name="append-inner" />
    </div>
  </FormFieldShell>
</template>
