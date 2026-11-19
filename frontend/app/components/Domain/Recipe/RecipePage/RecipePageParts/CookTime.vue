<template>
  <div
    v-if="isEditMode"
    class="inline-flex flex-col gap-1 font-sans"
    @click.stop
  >
    <label
      class="flex h-9 w-32 items-center gap-1.5 rounded-control border border-input bg-card ps-2.5 pe-2.5 text-muted-foreground focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/25"
      :title="$t('recipe.step-duration-minutes')"
    >
      <ClockIcon
        class="size-4 shrink-0"
        aria-hidden="true"
      />
      <input
        type="number"
        inputmode="numeric"
        min="0"
        max="35791394"
        step="1"
        :value="inputMinutes ?? ''"
        :placeholder="$t('recipe.step-duration-placeholder')"
        :aria-label="$t('recipe.step-duration-minutes')"
        class="h-full w-0 min-w-0 flex-1 bg-transparent text-sm tabular-nums text-foreground outline-none [appearance:textfield] placeholder:text-muted-foreground/80 [&::-webkit-inner-spin-button]:appearance-none"
        @keypress="e => e.key === '-' && e.preventDefault()"
        @input="onInput"
      >
      <span class="text-xs">{{ $t("recipe.step-duration-unit") }}</span>
    </label>
    <span
      v-if="modelValue && modelValue % 60"
      class="max-w-64 text-xs text-muted-foreground"
    >{{ $t('recipe.step-duration-saved', { duration: formattedDuration }) }}</span>
  </div>
  <span
    v-else-if="modelValue"
    class="text-sm"
  >
    {{ formattedDuration }}
  </span>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { ClockIcon } from "@lucide/vue";

const props = defineProps<{
  modelValue?: number | null;
  isEditMode: boolean;
}>();
const emit = defineEmits<{ "update:modelValue": [value: number | null] }>();
const { t } = useI18n();
// Display whole minutes only; keep imported seconds untouched until the minutes change.
// The hint exposes any remainder before the user deliberately replaces it.
const inputMinutes = ref<number | null>(null);

function toSeconds(minutes: number | null) {
  return (minutes ?? 0) * 60 || null;
}

watch(
  () => props.modelValue,
  (value) => {
    // Only re-sync outside changes, so stepping down to 0 (saved as no duration) keeps showing 0
    if ((value ?? null) === toSeconds(inputMinutes.value)) return;
    inputMinutes.value = value ? Math.floor(value / 60) : null;
  },
  { immediate: true },
);

function onInput(event: Event) {
  const raw = (event.target as HTMLInputElement).value;
  updateDuration(raw === "" ? null : Math.min(35791394, Math.max(0, Math.floor(Number(raw)))));
}

function updateDuration(value: number | null) {
  if (value === inputMinutes.value) return;
  inputMinutes.value = value;
  emit("update:modelValue", toSeconds(value));
}

const formattedDuration = computed(() => {
  const seconds = props.modelValue ?? 0;
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainder = seconds % 60;
  return [
    hours ? t("recipe.step-duration-value-hours", { hours }) : "",
    minutes ? t("recipe.step-duration-value-minutes", { minutes }) : "",
    remainder ? t("recipe.step-duration-value-seconds", { seconds: remainder }) : "",
  ].filter(Boolean).join(" ");
});
</script>
