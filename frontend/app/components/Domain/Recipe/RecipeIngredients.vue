<template>
  <section
    v-if="value && value.length > 0"
    class="flex flex-col font-sans"
    :aria-label="$t('recipe.ingredients')"
  >
    <div
      v-if="!isCookMode"
      class="mb-2 flex items-center gap-2"
    >
      <h2 class="m-0 text-xl font-bold tracking-tight">
        {{ $t("recipe.ingredients") }}
      </h2>
      <AppButtonCopy
        btn-class="ms-auto"
        :copy-text="ingredientCopyText"
      />
    </div>
    <ul class="m-0 list-none p-0">
      <li
        v-for="(ingredient, index) in value"
        :key="'ingredient' + index"
      >
        <h3
          v-if="showTitleEditor[index]"
          class="mb-1 mt-4 border-b pb-1.5 text-[15px] font-semibold text-muted-foreground"
        >
          {{ ingredient.title }}
        </h3>
        <div
          class="group/ing flex cursor-pointer items-start gap-3 rounded-item py-2 transition-colors"
          @click="toggleChecked(index)"
        >
          <Checkbox
            :model-value="isChecked(index)"
            class="mt-0.5 size-5 shrink-0"
            :aria-labelledby="`${uid}-ing-${index}`"
            @click.stop
            @update:model-value="setChecked(index, !!$event)"
          />
          <RecipeIngredientListItem
            :id="`${uid}-ing-${index}`"
            :ingredient="ingredient"
            :scale="scale"
            show-substitutions
            class="min-w-0 flex-1 transition-opacity"
            :class="isChecked(index) && 'opacity-45 [&_.ing-inline]:line-through'"
          />
        </div>
      </li>
    </ul>
  </section>
</template>

<script setup lang="ts">
import { Checkbox } from "~/components/ui/checkbox";
import RecipeIngredientListItem from "./RecipeIngredientListItem.vue";
import { useSessionStorage } from "@vueuse/core";
import { useIngredientTextParser } from "~/composables/recipes";
import type { RecipeIngredient } from "~/lib/api/types/recipe";

interface Props {
  value?: RecipeIngredient[];
  scale?: number;
  isCookMode?: boolean;
  storageKey?: string;
}
const props = withDefaults(defineProps<Props>(), {
  value: () => [],
  scale: 1,
  isCookMode: false,
  storageKey: undefined,
});

const { parseIngredientText } = useIngredientTextParser();
const uid = useId();

function validateTitle(title?: string | null) {
  return !(title === undefined || title === "" || title === null);
}

const transientChecked = ref<Record<string, boolean>>({});
const sessionChecked = props.storageKey
  ? useSessionStorage<Record<string, boolean>>(props.storageKey, {})
  : null;
const showTitleEditor = computed(() => props.value.map(x => validateTitle(x.title)));

const ingredientCopyText = computed(() => {
  const components: string[] = [];
  props.value.forEach((ingredient) => {
    if (ingredient.title) {
      if (components.length) {
        components.push("");
      }

      components.push(`[${ingredient.title}]`);
    }

    components.push(parseIngredientText(ingredient, props.scale, false));
  });

  return components.join("\n");
});

function toggleChecked(index: number) {
  setChecked(index, !isChecked(index));
}

function checkedState() {
  return sessionChecked?.value ?? transientChecked.value;
}

function checkedKey(index: number) {
  const referenceId = props.value[index]?.referenceId;
  return referenceId ? `ref:${referenceId}` : `idx:${index}`;
}

function isChecked(index: number) {
  return !!checkedState()[checkedKey(index)];
}

function setChecked(index: number, value: boolean) {
  const state = checkedState();
  state[checkedKey(index)] = value;

  if (sessionChecked) {
    sessionChecked.value = { ...state };
  }
  else {
    transientChecked.value = { ...state };
  }
}
</script>
