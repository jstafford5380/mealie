<template>
  <hr
    data-slot="base-divider"
    class="border-0 mx-0 my-2 rounded-full"
    :style="{ width, height: thickness, backgroundColor: background }"
  >
</template>

<script setup lang="ts">
const props = defineProps({
  width: {
    type: String,
    default: "100px",
  },
  thickness: {
    type: String,
    default: "2px",
  },
  /** Legacy Vuetify colour name; "accent" (the default) is the marigold brand colour. */
  color: {
    type: String,
    default: "accent",
  },
});

const background = computed(() => {
  if (!props.color || props.color === "accent") {
    return "var(--brand)";
  }
  if (props.color === "primary") {
    return "var(--primary)";
  }
  return `rgb(var(--v-theme-${props.color}, 0 0 0))`;
});
</script>
