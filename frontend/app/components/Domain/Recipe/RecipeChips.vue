<template>
  <div
    v-if="items.length > 0"
    class="font-sans"
  >
    <h2
      v-if="title"
      class="mt-4"
    >
      {{ title }}
    </h2>
    <div class="flex flex-wrap gap-1.5">
      <button
        v-for="category in items.slice(0, limit)"
        :key="category.name"
        type="button"
        class="inline-flex items-center rounded-full bg-highlight font-medium text-highlight-foreground transition-colors hover:bg-primary hover:text-primary-foreground"
        :class="small ? 'h-6 px-2.5 text-xs' : 'h-8 px-3.5 text-sm'"
        @click.prevent="() => $emit('item-selected', category, urlPrefix)"
      >
        {{ truncateText(category.name) }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { CategoryOut, TagOut, ToolOut } from "~/lib/api/types/recipe";
import { truncateText as truncatePlainText } from "~/lib/sanitize/text";

export type UrlPrefixParam = "tags" | "categories" | "tools";

interface Props {
  truncate?: boolean;
  items?: CategoryOut[] | TagOut[] | ToolOut[];
  title?: boolean;
  urlPrefix?: UrlPrefixParam;
  limit?: number;
  small?: boolean;
  maxWidth?: string | null;
}
const props = withDefaults(defineProps<Props>(), {
  truncate: false,
  items: () => [],
  title: false,
  urlPrefix: "categories",
  limit: 999,
  small: false,
  maxWidth: null,
});

defineEmits(["item-selected"]);
function truncateText(text: string, length = 20, clamp = "...") {
  if (!props.truncate) return text;
  return truncatePlainText(text, length, clamp);
}
</script>
