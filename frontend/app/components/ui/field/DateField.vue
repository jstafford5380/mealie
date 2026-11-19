<script setup lang="ts">
import { CalendarIcon } from "@lucide/vue";
import FormFieldShell from "./FormFieldShell.vue";

/**
 * A date picker on the browser's own date input: phones get their native picker,
 * keyboards can type, and the value is a Date at local midnight.
 */
const props = defineProps<{
  label?: string;
  hint?: string;
  min?: Date | null;
  max?: Date | null;
  disabled?: boolean;
  required?: boolean;
}>();
const model = defineModel<Date | null | undefined>();
const id = `date-${useId()}`;

function toInput(date?: Date | null) {
  if (!date || Number.isNaN(date.getTime())) {
    return "";
  }
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}
function onInput(event: Event) {
  const raw = (event.target as HTMLInputElement).value;
  if (!raw) {
    if (!props.required) {
      model.value = null;
    }
    return;
  }
  const [y, m, d] = raw.split("-").map(Number);
  model.value = new Date(y!, m! - 1, d!);
}
</script>

<template>
  <FormFieldShell
    :id="id"
    :label="label"
    :hint="hint"
    :required="required"
    :disabled="disabled"
  >
    <div class="flex h-10 w-full items-center gap-2 rounded-control border border-input bg-card px-3 focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/25">
      <CalendarIcon
        class="size-4 shrink-0 text-muted-foreground"
        aria-hidden="true"
      />
      <input
        :id="id"
        type="date"
        :value="toInput(model)"
        :min="toInput(min) || undefined"
        :max="toInput(max) || undefined"
        :disabled="disabled"
        :required="required"
        :aria-describedby="hint ? `${id}-hint` : undefined"
        class="h-full min-w-0 flex-1 bg-transparent text-[15px] outline-none [color-scheme:light] dark:[color-scheme:dark]"
        @change="onInput"
      >
    </div>
  </FormFieldShell>
</template>
