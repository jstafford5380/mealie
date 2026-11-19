<template>
  <fieldset class="m-0 min-w-0 border-0 p-0 font-sans">
    <legend
      v-if="label"
      class="mb-1.5 p-0 text-sm font-semibold"
    >
      {{ label }}
    </legend>
    <div class="flex flex-wrap items-center gap-2">
      <label
        v-for="part in parts"
        :key="part.key"
        class="flex h-10 w-[7.5rem] items-center rounded-control border border-input bg-card pe-3 focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/25"
      >
        <input
          type="number"
          inputmode="numeric"
          min="0"
          :max="part.max"
          step="1"
          :value="part.value.value ?? ''"
          :aria-label="label ? `${label}: ${part.suffix}` : part.suffix"
          class="h-full w-0 min-w-0 flex-1 bg-transparent px-3 text-[15px] tabular-nums outline-none [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none"
          @input="part.value.value = toWhole(($event.target as HTMLInputElement).value, part.max)"
        >
        <span class="text-sm text-muted-foreground">{{ part.suffix }}</span>
      </label>
      <!-- Shown after the structured time, e.g. "3 hours" + "plus overnight" -->
      <input
        v-if="!hideText"
        v-model="text"
        type="text"
        :aria-label="label ? `${label}: ${$t('recipe.time-note')}` : $t('recipe.time-note')"
        :placeholder="$t('recipe.time-note-placeholder')"
        class="h-10 min-w-40 flex-1 rounded-control border border-input bg-card px-3 text-[15px] outline-none placeholder:text-muted-foreground/70 focus:border-ring focus:ring-3 focus:ring-ring/25"
      >
    </div>
  </fieldset>
</template>

<script setup lang="ts">
import { useRecipeTime } from "~/composables/recipes";

defineProps<{ label?: string; hideText?: boolean }>();

const { durationUnitLabel } = useRecipeTime();

const seconds = defineModel<number | null | undefined>("seconds", { required: true });
const text = defineModel<string | null | undefined>("text");

/** Keeps hours, minutes, and any leftover seconds under the database's 2^31 - 1 limit */
const MAX_HOURS = Math.floor((2 ** 31 - 1 - 3599) / 3600);

const hours = ref<number | null>(null);
const minutes = ref<number | null>(null);

function toSeconds(): number | null {
  // Imported times can carry seconds the inputs don't show, which shouldn't be lost on edit
  const leftover = (seconds.value ?? 0) % 60;
  const total = (hours.value ?? 0) * 3600 + (minutes.value ?? 0) * 60 + leftover;
  return total > 0 ? total : null;
}

watch(
  seconds,
  (value) => {
    // Only re-split outside changes, so typing "90" minutes isn't rewritten to 1 hour 30 mid-edit
    if ((value ?? null) === toSeconds()) {
      return;
    }
    hours.value = value ? Math.floor(value / 3600) : null;
    minutes.value = value ? Math.floor((value % 3600) / 60) : null;
  },
  { immediate: true },
);

function toWhole(raw: string, max?: number): number | null {
  if (raw === "") {
    return null;
  }
  const n = Math.max(0, Math.floor(Number(raw)));
  if (!Number.isFinite(n)) {
    return null;
  }
  return max !== undefined ? Math.min(n, max) : n;
}

const parts = computed(() => [
  { key: "h", value: hours, suffix: durationUnitLabel("hour"), max: MAX_HOURS },
  { key: "m", value: minutes, suffix: durationUnitLabel("minute"), max: undefined },
]);

watch([hours, minutes], () => {
  seconds.value = toSeconds();
});
</script>
