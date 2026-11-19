<template>
  <div class="flex flex-col gap-4 font-sans">
    <ParseDialogChangeParser
      v-model="state.parser"
      :available-parsers="availableParsers"
      :show-nlp-language-hint="showNlpLanguageHint"
      @update:model-value="$emit('changeParser', $event)"
      @parse="$emit('parse')"
    />
    <h3 class="m-0 text-center text-lg font-semibold">
      {{ $t("recipe.parser.review-parsed-ingredients") }}
    </h3>
    <VueDraggable
      v-model="parsedIngs"
      handle=".handle"
      :delay="250"
      :delay-on-touch-only="true"
      class="flex flex-col gap-4"
      v-bind="{
        animation: 200,
        group: 'recipe-ingredients',
        disabled: false,
        ghostClass: 'ghost',
      }"
      @start="drag = true"
      @end="drag = false"
    >
      <RecipeIngredientEditor
        v-for="(ingredient, index) in parsedIngs"
        :key="ingredient.ingredient.referenceId ?? index"
        v-model="ingredient.ingredient"
        enable-drag-handle
        enable-context-menu
        :delete-disabled="parsedIngs.length <= 1"
        @delete="parsedIngs.splice(index, 1)"
        @insert-above="insertNewIngredient(index)"
        @insert-below="insertNewIngredient(index + 1)"
      >
        <template #before-divider>
          <p
            v-if="ingredient.input"
            class="m-0 mt-1 text-xs text-muted-foreground"
          >
            {{ $t("recipe.original-text-with-value", { originalText: ingredient.input }) }}
          </p>
        </template>
      </RecipeIngredientEditor>
    </VueDraggable>
  </div>
</template>

<script setup lang="ts">
import { VueDraggable } from "vue-draggable-plus";
import type { MenuItem } from "~/components/global/BaseOverflowButton.vue";
import type { ParsedIngredient } from "~/lib/api/types/recipe";
import type { Parser } from "~/lib/api/user/recipes/recipe";

defineEmits<{
  parse: [];
  changeParser: [Parser];
}>();
const props = defineProps<{
  availableParsers: MenuItem[];
  parser: Parser;
  showNlpLanguageHint: boolean;
}>();
const parsedIngs = defineModel<ParsedIngredient[]>({ required: true });

const state = reactive({
  parser: props.parser,
});

const drag = ref(false);

function insertNewIngredient(index: number) {
  const ing = {
    input: "",
    confidence: {},
    ingredient: {
      quantity: 0,
      referenceId: uuid4(),
    },
  } as ParsedIngredient;

  parsedIngs.value.splice(index, 0, ing);
}
</script>
