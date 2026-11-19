<template>
  <ul
    class="m-0 grid list-none grid-cols-1 gap-2 p-0 font-sans"
    :class="tile && 'sm:grid-cols-2'"
  >
    <li
      v-for="recipe, index in recipes"
      :key="recipe.id || recipe.slug"
      class="min-w-0 overflow-hidden rounded-card border bg-card"
    >
      <RecipeCardLineItem
        :recipe="recipe"
        :disable-link="disabled"
      >
        <template
          v-if="showDescription || (listItem && listItemDescriptions[index])"
          #subtitle
        >
          <span v-if="showDescription">{{ recipe.description }}</span>
          <SafeInlineHtml
            v-if="listItem && listItemDescriptions[index]"
            :html="listItemDescriptions[index]"
          />
        </template>
        <template #append>
          <slot
            :name="'actions-' + recipe.id"
            :v-bind="{ item: recipe }"
          />
        </template>
      </RecipeCardLineItem>
    </li>
  </ul>
</template>

<script setup lang="ts">
import RecipeCardLineItem from "./RecipeCardLineItem.vue";
import { useFraction } from "~/composables/recipes/use-fraction";
import type { ShoppingListItemOut } from "~/lib/api/types/household";
import type { RecipeSummary } from "~/lib/api/types/recipe";

interface Props {
  recipes: RecipeSummary[];
  listItem?: ShoppingListItemOut;
  tile?: boolean;
  showDescription?: boolean;
  disabled?: boolean;
}
const props = withDefaults(defineProps<Props>(), {
  listItem: undefined,
  tile: false,
  showDescription: false,
  disabled: false,
});

const { frac } = useFraction();
const listItemDescriptions = computed<string[]>(() => {
  if (
    props.recipes.length === 1 // we don't need to specify details if there's only one recipe ref
    || !props.listItem?.recipeReferences
    || props.listItem.recipeReferences.length !== props.recipes.length
  ) {
    return props.recipes.map(_ => "");
  }

  const listItemDescriptions: string[] = [];
  for (let i = 0; i < props.recipes.length; i++) {
    const itemRef = props.listItem?.recipeReferences[i];
    const quantity = (itemRef.recipeQuantity || 1) * (itemRef.recipeScale || 1);

    let listItemDescription = "";
    if (props.listItem.unit?.fraction) {
      const fraction = frac(quantity, 10, true);
      if (fraction[0] !== undefined && fraction[0] > 0) {
        listItemDescription += fraction[0];
      }

      if (fraction[1] > 0) {
        listItemDescription += ` <sup>${fraction[1]}</sup>&frasl;<sub>${fraction[2]}</sub>`;
      }
      else {
        listItemDescription = (quantity).toString();
      }
    }
    else {
      listItemDescription = (Math.round(quantity * 100) / 100).toString();
    }

    if (props.listItem.unit) {
      const unitDisplay = props.listItem.unit.useAbbreviation && props.listItem.unit.abbreviation
        ? props.listItem.unit.abbreviation
        : props.listItem.unit.name;

      listItemDescription += ` ${unitDisplay}`;
    }
    if (props.listItem.food) {
      const foodName = props.listItem.food.name;
      listItemDescription += ` ${foodName}`;
    }

    if (itemRef.recipeNote) {
      listItemDescription += `, ${itemRef.recipeNote}`;
    }

    listItemDescriptions.push(listItemDescription);
  }

  return listItemDescriptions;
});
</script>
