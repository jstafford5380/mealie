<script setup lang="ts">
import { MdiIcon } from "~/components/ui/mdi-icon";
import { useStaticRoutes } from "~/composables/api";

/** A recipe's small image, or a quiet placeholder when it has none or it fails to load. */
const props = withDefaults(defineProps<{
  recipeId?: string | null;
  image?: string | null;
  alt?: string;
  size?: "tiny" | "small";
}>(), {
  recipeId: null,
  image: null,
  alt: "",
  size: "tiny",
});

const { recipeTinyImage, recipeSmallImage } = useStaticRoutes();
const failed = ref(false);
watch(() => [props.recipeId, props.image], () => {
  failed.value = false;
});
const src = computed(() => {
  if (!props.recipeId || !props.image || failed.value) {
    return "";
  }
  return props.size === "small"
    ? recipeSmallImage(props.recipeId, props.image)
    : recipeTinyImage(props.recipeId, props.image);
});
</script>

<template>
  <span class="relative flex shrink-0 items-center justify-center overflow-hidden bg-muted text-muted-foreground">
    <img
      v-if="src"
      :src="src"
      :alt="alt"
      loading="lazy"
      class="absolute inset-0 size-full object-cover"
      @error="failed = true"
    >
    <MdiIcon
      v-else
      :path="$globals.icons.primary"
      class="size-1/2 max-h-6 max-w-6 opacity-60"
    />
  </span>
</template>
