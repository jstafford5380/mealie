<template>
  <div class="inline-flex">
    <button
      type="button"
      v-bind="$attrs"
      :aria-label="$t('recipe.open-timeline')"
      :title="$t('recipe.open-timeline')"
      :class="buttonStyle
        ? 'inline-flex size-11 items-center justify-center rounded-full bg-card text-foreground shadow-sm ring-1 ring-border transition-colors hover:bg-highlight'
        : 'inline-flex size-9 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-highlight hover:text-foreground'"
      @click.prevent="toggleTimeline"
    >
      <MdiIcon
        :path="$globals.icons.timelineText"
        :class="buttonStyle ? 'size-6' : 'size-5'"
      />
    </button>
    <BaseDialog
      v-model="showTimeline"
      :title="$t('recipe.timeline')"
      :icon="$globals.icons.timelineText"
      width="70%"
    >
      <RecipeTimeline
        v-model="showTimeline"
        :query-filter="timelineAttrs.queryFilter"
      />
    </BaseDialog>
  </div>
</template>

<script setup lang="ts">
import { MdiIcon } from "~/components/ui/mdi-icon";
import RecipeTimeline from "./RecipeTimeline.vue";

defineOptions({ inheritAttrs: false });

interface Props {
  buttonStyle?: boolean;
  slug?: string;
  recipeName?: string;
}
const props = withDefaults(defineProps<Props>(), {
  buttonStyle: false,
  slug: "",
  recipeName: "",
});

const showTimeline = ref(false);

function toggleTimeline() {
  showTimeline.value = !showTimeline.value;
}

const timelineAttrs = computed(() => {
  return {
    queryFilter: `recipe.slug="${props.slug}"`,
  };
});
</script>
