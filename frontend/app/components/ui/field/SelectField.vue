<script setup lang="ts">
import type { AcceptableValue } from "reka-ui";
import type { FormValidationRule } from "~/types/auto-forms";
import { useFieldValidation } from "~/composables/forms/use-field-validation";
import { cn } from "~/lib/utils";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../select";
import FormFieldShell from "./FormFieldShell.vue";

/**
 * Single-value select. Items are objects; `itemTitle`/`itemValue` name their fields
 * (Vuetify's item-title/item-value), or plain strings.
 */
const props = withDefaults(defineProps<{
  items: Array<Record<string, any> | string | number>;
  itemTitle?: string;
  itemValue?: string;
  label?: string;
  hint?: string;
  placeholder?: string;
  name?: string;
  rules?: FormValidationRule[];
  errorMessages?: string | string[];
  validateOn?: string;
  readonly?: boolean;
  disabled?: boolean;
  required?: boolean;
}>(), {
  itemTitle: "title",
  itemValue: "value",
  rules: () => [],
});

const model = defineModel<AcceptableValue | null | undefined>();

const field = useFieldValidation(model as Ref<unknown>, {
  rules: () => props.rules,
  errorMessages: () => props.errorMessages,
  name: () => props.name,
  validateOn: () => props.validateOn,
  disabled: () => props.disabled || undefined,
  readonly: () => props.readonly || undefined,
});

const inputId = computed(() => `input-${field.id.value}`);
const options = computed(() => props.items.map((item) => {
  if (typeof item !== "object" || item === null) {
    return { title: String(item), value: item as AcceptableValue };
  }
  return { title: String(item[props.itemTitle] ?? ""), value: (item[props.itemValue] ?? item[props.itemTitle]) as AcceptableValue };
}));
const describedBy = computed(() => {
  if (field.visibleError.value) {
    return `${inputId.value}-error`;
  }
  return props.hint ? `${inputId.value}-hint` : undefined;
});

function onOpenChange(open: boolean) {
  if (!open) {
    field.onBlur();
  }
}

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
    <Select
      v-model="model"
      :name="name"
      :disabled="field.isDisabled.value || field.isReadonly.value"
      :required="required"
      @update:open="onOpenChange"
    >
      <SelectTrigger
        :id="inputId"
        :aria-invalid="field.visibleError.value ? 'true' : undefined"
        :aria-describedby="describedBy"
        :class="cn('h-11! w-full bg-card text-base md:text-[15px]', field.isReadonly.value && 'bg-muted opacity-100')"
      >
        <SelectValue :placeholder="placeholder" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem
          v-for="option in options"
          :key="String(option.value)"
          :value="option.value"
        >
          {{ option.title }}
        </SelectItem>
      </SelectContent>
    </Select>
  </FormFieldShell>
</template>
