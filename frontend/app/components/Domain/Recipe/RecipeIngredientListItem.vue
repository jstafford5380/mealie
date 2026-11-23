<template>
  <div class="ingredient-item text-[15.5px] leading-normal text-foreground">
    <SafeMarkdown
      v-if="amount ? amount.quantity : parsedIng.quantity"
      class="ing-inline ing-quantity font-semibold"
      :source="amount ? $n(amount.quantity) : parsedIng.quantity"
    />
    <template v-if="amount ? amount.unit : parsedIng.unit">
      <span class="font-semibold">{{ amount ? amount.unit : parsedIng.unit }}</span>{{ " " }}
    </template>
    <template v-if="parsedIng.note && !parsedIng.name">
      <SafeMarkdown
        class="ing-inline"
        :source="parsedIng.note"
      />
      <RecipeIngredientSubstitutions
        v-if="showSubstitutions"
        :ingredient="ingredient"
        :scale="scale"
      />
    </template>
    <template v-else-if="parsedIng.recipeLink">
      <SafeMarkdown
        class="ing-inline [&_a]:font-medium [&_a]:text-primary [&_a]:underline"
        :source="parsedIng.recipeLink"
      />
      <RecipeIngredientSubstitutions
        v-if="showSubstitutions"
        :ingredient="ingredient"
        :scale="scale"
      />
      <SafeMarkdown
        v-if="parsedIng.note"
        class="ing-note"
        :source="parsedIng.note"
      />
    </template>
    <template v-else>
      <SafeMarkdown
        v-if="parsedIng.name"
        class="ing-inline"
        :source="parsedIng.name"
      />
      <!-- sits before the note, which takes a full block row beneath -->
      <RecipeIngredientSubstitutions
        v-if="showSubstitutions"
        :ingredient="ingredient"
        :scale="scale"
      />
      <SafeMarkdown
        v-if="parsedIng.note"
        class="ing-note"
        :source="parsedIng.note"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import type { RecipeIngredient } from "~/lib/api/types/household";
import { useIngredientTextParser } from "~/composables/recipes";
import RecipeIngredientSubstitutions from "~/components/Domain/Recipe/RecipeIngredientSubstitutions.vue";

interface Props {
  ingredient: RecipeIngredient;
  amount?: { quantity: number; unit: string } | null;
  scale?: number;
  // off by default: the shopping list and the add-to-list dialog reuse this row, and a menu
  // button is noise in both. the recipe renderer opts in
  showSubstitutions?: boolean;
}
const props = withDefaults(defineProps<Props>(), {
  scale: 1,
  showSubstitutions: false,
});
const route = useRoute();
const auth = useMealieAuth();
const groupSlug = computed(() => route.params.groupSlug || auth.user?.value?.groupSlug || "");
const { useParsedIngredientText } = useIngredientTextParser();

const parsedIng = computed(() => {
  return useParsedIngredientText(props.ingredient, props.scale, true, groupSlug.value.toString());
});
</script>

<style>
/* Keeps quantity, unit and name in one inline flow so a quantity never wraps alone. */
.ingredient-item .ing-inline,
.ingredient-item .ing-inline > p {
  display: inline;
  margin: 0;
}
.ingredient-item .ing-quantity::after {
  content: " ";
}
.ingredient-item .ing-inline sup + span {
  letter-spacing: -0.05rem;
}
.ingredient-item .ing-note {
  display: block;
  margin-top: 2px;
  font-size: 0.86em;
  line-height: 1.35;
  color: var(--muted-foreground);
  word-break: break-word;
}
.ingredient-item .ing-note p {
  margin: 0;
}
</style>
