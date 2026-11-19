<template>
  <Alert
    variant="warning"
    class="rounded-card px-4 py-3.5 font-sans"
  >
    <MdiIcon :path="$globals.icons.alert" />
    <AlertTitle
      v-if="title"
      class="font-semibold"
    >
      {{ title }}
    </AlertTitle>
    <AlertDescription v-if="description || $slots.default">
      <div v-if="description">
        {{ description }}
      </div>
      <div
        v-if="$slots.default"
        class="py-1 [&_a]:font-semibold [&_a]:text-brand-strong [&_a]:underline"
      >
        <slot />
      </div>
    </AlertDescription>
  </Alert>
</template>

<script setup lang="ts">
import { Alert, AlertDescription, AlertTitle } from "~/components/ui/alert";
import { MdiIcon } from "~/components/ui/mdi-icon";

defineProps({
  title: {
    type: String,
    required: false,
    default: "",
  },
  description: {
    type: String,
    required: false,
    default: "",
  },
});
</script>
