<template>
  <Popover v-if="hasSubstitutions">
    <PopoverTrigger as-child>
      <!-- click, not hover alone: this is read in a kitchen, on a phone, where nothing hovers -->
      <button
        type="button"
        class="relative ms-1 inline-flex size-[1.4em] translate-y-[0.15em] items-center justify-center rounded-full align-baseline text-muted-foreground transition-colors before:absolute before:-inset-2 hover:bg-highlight hover:text-highlight-foreground"
        :aria-label="$t('recipe.substitutions')"
        @click.stop
      >
        <MdiIcon
          :path="$globals.icons.swapHorizontal"
          class="size-[1em]"
        />
      </button>
    </PopoverTrigger>
    <PopoverContent
      align="start"
      class="w-[min(360px,calc(100vw-2rem))] p-3 text-sm"
      @click.stop
    >
      <div
        v-for="section, sectionIndex in sections"
        :key="section.key"
        :class="[section.dimmed && 'text-muted-foreground', sectionIndex && 'mt-4']"
      >
        <div class="mb-1.5 border-b pb-1 text-xs font-semibold text-muted-foreground">
          {{ section.title }}
        </div>
        <div
          v-for="substitution, i in section.items"
          :key="i"
          class="leading-snug [&+&]:mt-2 [&_p]:m-0"
        >
          <template v-if="substitution.substituteFood">
            <span class="font-semibold">{{ substitutionFoodName(substitution, pluralFood) }}</span>
            <SafeMarkdown
              v-if="substitution.note"
              class="opacity-75"
              :source="substitution.note"
            />
          </template>
          <!-- with no food the note is the substitution itself, so it reads like one -->
          <SafeMarkdown
            v-else-if="substitution.note"
            class="font-semibold"
            :source="substitution.note"
          />
        </div>
      </div>
    </PopoverContent>
  </Popover>
</template>

<script setup lang="ts">
import { MdiIcon } from "~/components/ui/mdi-icon";
import { Popover, PopoverContent, PopoverTrigger } from "~/components/ui/popover";
import { substitutionFoodName, useFoodPlurality, useIngredientSubstitutions } from "~/composables/recipes";
import type { IngredientFoodSubstitution, RecipeIngredient } from "~/lib/api/types/recipe";

interface Props {
  ingredient: RecipeIngredient;
  scale?: number;
}

const props = withDefaults(defineProps<Props>(), {
  scale: 1,
});

const i18n = useI18n();
const { recipeSubstitutions, foodSubstitutions, hasSubstitutions } = useIngredientSubstitutions(() => props.ingredient);

// a substitute stands in for the food at this line's quantity and unit, so it takes the same
// plural form the food itself does -- both sections alike, since they sit under the one line
const { shouldPluralizeFood } = useFoodPlurality();
const pluralFood = computed(() => shouldPluralizeFood(props.ingredient, props.scale));

interface SubstitutionSection {
  key: string;
  title: string;
  items: IngredientFoodSubstitution[];
  dimmed: boolean;
}

// what this recipe says comes first and at full strength; what the food suggests everywhere
// sits behind it, and says so, which is what makes the first heading need no qualifier
const sections = computed<SubstitutionSection[]>(() => [
  {
    key: "recipe",
    title: i18n.t("recipe.substitutions"),
    items: recipeSubstitutions.value,
    dimmed: false,
  },
  {
    key: "food",
    title: i18n.t("recipe.commonly-substituted-with"),
    items: foodSubstitutions.value,
    dimmed: true,
  },
].filter(section => section.items.length));
</script>
