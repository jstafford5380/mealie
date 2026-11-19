<template>
  <slot />
</template>

<script setup lang="ts">
import { provideFieldGroup } from "~/composables/forms/use-field-validation";

/**
 * Validation scope for part of a page (the role a nested `<v-form>` played): fields inside
 * validate together through the exposed `validate()`, separately from the rest of the page.
 */
const group = provideFieldGroup({ isolated: true });
defineExpose(group);
</script>
