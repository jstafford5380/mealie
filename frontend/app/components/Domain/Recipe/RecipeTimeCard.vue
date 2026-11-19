<template>
  <dl
    v-if="_showCards"
    class="m-0 flex flex-wrap gap-x-6 gap-y-2 font-sans"
    :class="small ? 'text-sm' : 'text-base'"
  >
    <div
      v-for="time in times"
      :key="time.name"
      class="flex items-center gap-2"
    >
      <MdiIcon
        :path="time.icon"
        class="shrink-0 text-primary"
        :class="small ? 'size-4' : 'size-5'"
      />
      <div>
        <dt class="font-semibold opacity-80">
          {{ time.name }}
        </dt>
        <dd class="m-0 whitespace-nowrap">
          {{ time.value }}
        </dd>
      </div>
    </div>
  </dl>
</template>

<script setup lang="ts">
import { MdiIcon } from "~/components/ui/mdi-icon";
import { useRecipeTime } from "~/composables/recipes";

interface Props {
  prepTime?: string | null;
  totalTime?: string | null;
  performTime?: string | null;
  prepTimeSeconds?: number | null;
  totalTimeSeconds?: number | null;
  performTimeSeconds?: number | null;
  color?: string;
  small?: boolean;
}
const props = withDefaults(defineProps<Props>(), {
  prepTime: null,
  totalTime: null,
  performTime: null,
  prepTimeSeconds: null,
  totalTimeSeconds: null,
  performTimeSeconds: null,
  color: "accent custom-transparent",
  small: false,
});

const i18n = useI18n();
const { recipeTimeDisplay } = useRecipeTime();

const totalTime = computed(() => recipeTimeDisplay(props.totalTimeSeconds, props.totalTime));
const prepTime = computed(() => recipeTimeDisplay(props.prepTimeSeconds, props.prepTime));
const performTime = computed(() => recipeTimeDisplay(props.performTimeSeconds, props.performTime));

const _showCards = computed(() => {
  return [prepTime.value, totalTime.value, performTime.value].some(x => !!x);
});

const validateTotalTime = computed(() => {
  return totalTime.value ? { name: i18n.t("recipe.total-time"), value: totalTime.value } : null;
});

const validatePrepTime = computed(() => {
  return prepTime.value ? { name: i18n.t("recipe.prep-time"), value: prepTime.value } : null;
});

const validatePerformTime = computed(() => {
  return performTime.value ? { name: i18n.t("recipe.perform-time"), value: performTime.value } : null;
});

const { $globals } = useNuxtApp();
const times = computed(() => [
  validateTotalTime.value && { ...validateTotalTime.value, icon: $globals.icons.clockOutline },
  validatePrepTime.value && { ...validatePrepTime.value, icon: $globals.icons.knife },
  validatePerformTime.value && { ...validatePerformTime.value, icon: $globals.icons.potSteam },
].filter(Boolean) as { name: string; value: string; icon: string }[]);
</script>
