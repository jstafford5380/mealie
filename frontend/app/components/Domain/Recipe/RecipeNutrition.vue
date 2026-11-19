<template>
  <section
    v-if="showViewer"
    class="font-sans"
    :aria-label="$t('recipe.nutrition')"
  >
    <h2 class="m-0 text-sm font-semibold text-muted-foreground">
      {{ $t("recipe.nutrition") }}
      <span class="font-normal">· {{ $t("recipe.per-serving") }}</span>
    </h2>
    <dl class="m-0 mt-2 divide-y divide-border/70 rounded-card border bg-card px-4 text-[15px]">
      <div
        v-for="(item, key) in renderedList"
        :key="key"
        class="flex items-baseline justify-between gap-4 py-2"
      >
        <dt class="text-muted-foreground">
          {{ item.label }}
        </dt>
        <dd class="m-0 font-semibold tabular-nums">
          {{ item.value }}<span class="ms-0.5 font-normal text-muted-foreground">{{ item.suffix }}</span>
        </dd>
      </div>
    </dl>
  </section>
  <div
    v-else-if="edit"
    class="grid grid-cols-2 gap-4 font-sans sm:grid-cols-3"
  >
    <p class="col-span-full m-0 text-sm text-muted-foreground">
      {{ $t("recipe.per-serving") }}
    </p>
    <label
      v-for="(item, key) in modelValue"
      :key="key"
      class="flex flex-col gap-1.5"
    >
      <span class="text-sm font-semibold">{{ labels[key]?.label ?? key }}</span>
      <span class="flex h-10 items-center rounded-control border border-input bg-card pe-3 focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/25">
        <input
          type="number"
          inputmode="decimal"
          min="0"
          step="any"
          autocomplete="off"
          :value="parseNutritionValue(modelValue[key]) ?? ''"
          class="h-full w-0 min-w-0 flex-1 bg-transparent px-3 text-[15px] tabular-nums outline-none [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none"
          @input="updateValue(key, ($event.target as HTMLInputElement).value === '' ? null : Math.max(0, Number(($event.target as HTMLInputElement).value)))"
        >
        <span class="text-sm text-muted-foreground">{{ labels[key]?.suffix }}</span>
      </span>
    </label>
  </div>
</template>

<script setup lang="ts">
import { parseNutritionValue, useNutritionLabels } from "~/composables/recipes";
import type { Nutrition } from "~/lib/api/types/recipe";
import type { NutritionLabelType } from "~/composables/recipes/use-recipe-nutrition";

interface Props {
  edit?: boolean;
}
const props = withDefaults(defineProps<Props>(), {
  edit: true,
});

const modelValue = defineModel<Nutrition>({ required: true });

const { labels } = useNutritionLabels();
const valueNotNull = computed(() => {
  let key: keyof Nutrition;
  for (key in modelValue.value) {
    if (modelValue.value[key] !== null) {
      return true;
    }
  }
  return false;
});

const showViewer = computed(() => !props.edit && valueNotNull.value);

function updateValue(key: number | string, value: number | null) {
  modelValue.value = { ...modelValue.value, [key]: value?.toString() ?? null };
}

// Build a new list that only contains nutritional information that has a value
const renderedList = computed(() => {
  return Object.entries(labels).reduce((item: NutritionLabelType, [key, label]) => {
    if (modelValue.value[key]?.trim()) {
      item[key] = {
        ...label,
        value: modelValue.value[key],
      };
    }
    return item;
  }, {});
});
</script>
