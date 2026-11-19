<script setup lang="ts">
import type { FormValidationRule } from "~/types/auto-forms";
import { useFieldValidation } from "~/composables/forms/use-field-validation";
import { Checkbox } from "../checkbox";

const props = withDefaults(defineProps<{
  label?: string;
  hint?: string;
  name?: string;
  rules?: FormValidationRule[];
  errorMessages?: string | string[];
  readonly?: boolean;
  disabled?: boolean;
}>(), {
  rules: () => [],
});

const model = defineModel<boolean | null | undefined>();

const field = useFieldValidation(model as Ref<unknown>, {
  rules: () => props.rules,
  errorMessages: () => props.errorMessages,
  name: () => props.name,
  disabled: () => props.disabled || undefined,
  readonly: () => props.readonly || undefined,
});

const inputId = computed(() => `input-${field.id.value}`);
const checked = computed({
  get: () => !!model.value,
  set: (value: boolean | "indeterminate") => {
    if (!field.isReadonly.value) {
      model.value = value === true;
    }
  },
});

defineExpose({ validate: field.validate, reset: field.reset, resetValidation: field.resetValidation });
</script>

<template>
  <div
    data-slot="form-field"
    class="flex w-full items-start gap-3 py-2 font-sans"
    :data-disabled="field.isDisabled.value ? 'true' : undefined"
  >
    <Checkbox
      :id="inputId"
      v-model="checked"
      :name="name"
      :disabled="field.isDisabled.value"
      :aria-readonly="field.isReadonly.value ? 'true' : undefined"
      :aria-describedby="hint || field.visibleError.value ? `${inputId}-desc` : undefined"
      class="mt-0.5 size-5"
    />
    <div class="flex min-w-0 flex-col gap-0.5">
      <span class="flex items-center gap-1.5">
        <label
          :for="inputId"
          class="text-[15px] font-medium leading-snug text-foreground"
          :class="field.isDisabled.value && 'opacity-60'"
        >
          <slot name="label">{{ label }}</slot>
        </label>
        <slot name="append-label" />
      </span>
      <p
        v-if="field.visibleError.value || hint"
        :id="`${inputId}-desc`"
        class="m-0 text-[13px] leading-snug"
        :class="field.visibleError.value ? 'text-destructive' : 'text-muted-foreground'"
      >
        {{ field.visibleError.value || hint }}
      </p>
    </div>
  </div>
</template>
