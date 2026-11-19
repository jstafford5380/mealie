<template>
  <component
    :is="recipeRoute ? NuxtLink : 'div'"
    :to="recipeRoute"
    :role="recipeRoute ? undefined : 'button'"
    :tabindex="recipeRoute ? undefined : 0"
    :aria-pressed="!recipeRoute && active ? 'true' : undefined"
    class="flex min-h-14 items-center gap-3 rounded-control px-2 py-1.5 font-sans text-foreground no-underline transition-colors hover:bg-highlight/60 focus-visible:outline-2 focus-visible:outline-ring"
    :class="[active && 'bg-highlight text-highlight-foreground', !recipeRoute && 'cursor-pointer']"
    @keydown.enter.self="!recipeRoute && ($event.target as HTMLElement).click()"
    @keydown.space.self.prevent="!recipeRoute && ($event.target as HTMLElement).click()"
  >
    <RecipeThumb
      :recipe-id="recipe.id"
      :image="recipe.image"
      class="h-10 w-14 rounded-item"
    />
    <span class="min-w-0 flex-1">
      <span class="block truncate text-[15px] font-medium">{{ recipe.name }}</span>
      <span
        v-if="$slots.subtitle"
        class="block truncate text-sm text-muted-foreground"
      ><slot name="subtitle" /></span>
    </span>
    <span
      v-if="$slots.append"
      class="shrink-0"
    ><slot name="append" /></span>
  </component>
</template>

<script setup lang="ts">
import RecipeThumb from "./RecipeThumb.vue";
import type { RecipeSummary } from "~/lib/api/types/recipe";

interface Props {
  recipe: RecipeSummary;
  active?: boolean;
  disableLink?: boolean;
}
const props = withDefaults(defineProps<Props>(), {
  active: false,
  disableLink: false,
});

const NuxtLink = resolveComponent("NuxtLink");
const auth = useMealieAuth();
const route = useRoute();

const groupSlug = computed(() => route.params.groupSlug as string || auth.user.value?.groupSlug || "");
const recipeRoute = computed(() => {
  if (props.disableLink || !props.recipe.slug) {
    return undefined;
  }

  return `/g/${groupSlug.value}/r/${props.recipe.slug}`;
});
</script>
