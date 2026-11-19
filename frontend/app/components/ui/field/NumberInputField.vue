<script setup lang="ts">
import type { FormValidationRule } from "~/types/auto-forms";
import { MinusIcon, PlusIcon } from "@lucide/vue";
import { useFieldValidation } from "~/composables/forms/use-field-validation";
import { cn } from "~/lib/utils";
import FormFieldShell from "./FormFieldShell.vue";

const props = withDefaults(defineProps<{
  label?: string;
  hint?: string;
  name?: string;
  rules?: FormValidationRule[];
  errorMessages?: string | string[];
  validateOn?: string;
  readonly?: boolean;
  disabled?: boolean;
  min?: number;
  max?: number;
  step?: number;
  /** Decimal places kept; null keeps the value as typed. */
  precision?: number | null;
  /** Vuetify control-variant; "hidden" removes the +/- buttons. */
  controlVariant?: "split" | "default" | "hidden" | "stacked";
}>(), {
  step: 1,
  precision: 0,
  controlVariant: "default",
  rules: () => [],
});

const model = defineModel<number | null | undefined>();

const field = useFieldValidation(model as Ref<unknown>, {
  rules: () => props.rules,
  errorMessages: () => props.errorMessages,
  name: () => props.name,
  validateOn: () => props.validateOn,
  disabled: () => props.disabled || undefined,
  readonly: () => props.readonly || undefined,
});

const inputId = computed(() => `input-${field.id.value}`);
const locked = computed(() => field.isDisabled.value || field.isReadonly.value);

function normalize(value: number): number {
  let next = value;
  if (props.min !== undefined) {
    next = Math.max(props.min, next);
  }
  if (props.max !== undefined) {
    next = Math.min(props.max, next);
  }
  if (props.precision !== null && props.precision !== undefined) {
    next = Number(next.toFixed(props.precision));
  }
  return next;
}

function onInput(event: Event) {
  const raw = (event.target as HTMLInputElement).value;
  model.value = raw === "" ? null : Number(raw);
}

function onChange(event: Event) {
  const raw = (event.target as HTMLInputElement).value;
  if (raw !== "" && !Number.isNaN(Number(raw))) {
    model.value = normalize(Number(raw));
  }
  field.onBlur();
}

function stepBy(direction: 1 | -1) {
  model.value = normalize((model.value ?? props.min ?? 0) + direction * props.step);
}

defineExpose({ validate: field.validate, reset: field.reset, resetValidation: field.resetValidation });
</script>

<template>
  <FormFieldShell
    :id="inputId"
    :label="label"
    :hint="hint"
    :error="field.visibleError.value"
    :disabled="field.isDisabled.value"
  >
    <div
      :class="cn(
        'flex h-11 w-full max-w-60 items-center rounded-control border border-input bg-card transition-[color,box-shadow] focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/25',
        field.visibleError.value && 'border-destructive',
        field.isDisabled.value && 'opacity-60',
      )"
    >
      <button
        v-if="controlVariant !== 'hidden'"
        type="button"
        class="inline-flex h-full w-11 shrink-0 items-center justify-center text-muted-foreground hover:text-foreground disabled:opacity-40"
        :disabled="locked || (min !== undefined && (model ?? min) <= min)"
        :aria-label="$t('general.decrease')"
        @click="stepBy(-1)"
      >
        <MinusIcon class="size-4" />
      </button>
      <input
        :id="inputId"
        type="number"
        inputmode="decimal"
        :value="model ?? ''"
        :name="name"
        :min="min"
        :max="max"
        :step="precision === 0 ? step : 'any'"
        :readonly="field.isReadonly.value"
        :disabled="field.isDisabled.value"
        :aria-invalid="field.visibleError.value ? 'true' : undefined"
        :aria-describedby="field.visibleError.value ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined"
        class="h-full min-w-0 flex-1 border-0 bg-transparent text-center text-base tabular-nums outline-none [appearance:textfield] md:text-[15px] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
        @input="onInput"
        @change="onChange"
      >
      <button
        v-if="controlVariant !== 'hidden'"
        type="button"
        class="inline-flex h-full w-11 shrink-0 items-center justify-center text-muted-foreground hover:text-foreground disabled:opacity-40"
        :disabled="locked || (max !== undefined && (model ?? max) >= max)"
        :aria-label="$t('general.increase')"
        @click="stepBy(1)"
      >
        <PlusIcon class="size-4" />
      </button>
    </div>
  </FormFieldShell>
</template>
