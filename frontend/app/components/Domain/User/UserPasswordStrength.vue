<template>
  <div class="flex flex-col gap-1.5 pb-2 font-sans">
    <div class="flex items-center justify-between text-sm">
      <span class="font-semibold">{{ $t("user.password-strength", { strength: pwStrength.strength.value }) }}</span>
    </div>
    <div
      class="h-2 overflow-hidden rounded-full bg-muted"
      role="meter"
      :aria-valuenow="Math.min(100, Math.round(pwStrength.score.value))"
      aria-valuemin="0"
      aria-valuemax="100"
      :aria-label="$t('user.password-strength', { strength: pwStrength.strength.value })"
    >
      <div
        class="h-full rounded-full transition-[width,background-color] duration-300"
        :class="BAR_COLORS[pwStrength.color.value] || 'bg-primary'"
        :style="{ width: `${Math.min(100, Math.max(4, pwStrength.score.value))}%` }"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { usePasswordStrength } from "~/composables/use-passwords";

const modelValue = defineModel<string>({ default: "" });
const i18n = useI18n();

const pwStrength = usePasswordStrength(modelValue, i18n);

const BAR_COLORS: Record<string, string> = {
  error: "bg-destructive",
  warning: "bg-brand",
  info: "bg-primary/60",
  success: "bg-primary",
};
</script>
