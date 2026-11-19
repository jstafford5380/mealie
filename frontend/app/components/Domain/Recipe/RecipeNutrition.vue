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
  <div v-else-if="edit">
    <v-card class="mt-2">
      <v-card-title class="pt-2 pb-0">
        {{ $t("recipe.nutrition") }}
      </v-card-title>
      <v-card-subtitle class="pb-1">
        {{ $t("recipe.per-serving") }}
      </v-card-subtitle>
      <v-divider class="mx-2 my-1" />
      <v-card-text>
        <div
          v-for="(item, key, index) in modelValue"
          :key="index"
        >
          <v-number-input
            :model-value="parseNutritionValue(modelValue[key])"
            :label="labels[key].label"
            :suffix="labels[key].suffix"
            density="compact"
            autocomplete="off"
            variant="underlined"
            inset
            :precision="null"
            :min="0"
            @update:model-value="updateValue(key, $event)"
          />
        </div>
      </v-card-text>
    </v-card>
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

<style lang="scss" scoped></style>
