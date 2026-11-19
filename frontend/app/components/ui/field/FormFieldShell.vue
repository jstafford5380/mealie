<script setup lang="ts">
/** Label, hint and error layout shared by the form controls in this folder. */
defineProps<{
  id: string;
  label?: string;
  hint?: string;
  error?: string;
  required?: boolean;
  disabled?: boolean;
}>();
</script>

<template>
  <div
    data-slot="form-field"
    class="flex w-full flex-col gap-1.5 py-1.5 font-sans"
    :data-invalid="error ? 'true' : undefined"
    :data-disabled="disabled ? 'true' : undefined"
  >
    <label
      v-if="label"
      :for="id"
      class="text-sm font-semibold text-foreground data-[disabled=true]:opacity-60"
      :data-disabled="disabled ? 'true' : undefined"
    >
      {{ label }}<span
        v-if="required"
        aria-hidden="true"
        class="text-destructive"
      > *</span>
    </label>
    <slot />
    <p
      v-if="error"
      :id="`${id}-error`"
      class="m-0 text-[13px] leading-snug text-destructive"
      role="alert"
    >
      {{ error }}
    </p>
    <p
      v-else-if="hint"
      :id="`${id}-hint`"
      class="m-0 text-[13px] leading-snug text-muted-foreground"
    >
      {{ hint }}
    </p>
  </div>
</template>
