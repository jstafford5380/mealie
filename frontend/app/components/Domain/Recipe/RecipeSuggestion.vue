<template>
  <article class="overflow-hidden rounded-card border bg-card font-sans">
    <RecipeCardLineItem :recipe="recipe">
      <template
        v-if="recipe.description"
        #subtitle
      >
        {{ recipe.description }}
      </template>
    </RecipeCardLineItem>
    <div
      v-if="missingOrganizers.some(o => o.show) || substitutedFoods?.length"
      class="flex flex-col gap-2 border-t px-4 py-3"
    >
      <template
        v-for="(organizer, idx) in missingOrganizers"
        :key="idx"
      >
        <div
          v-if="organizer.show"
          class="flex flex-wrap items-center gap-1.5"
        >
          <span class="me-1 text-sm text-muted-foreground">{{ $t("recipe-finder.missing") }}:</span>
          <!-- pressing one adds it to the search, as if you had it -->
          <button
            v-for="item in organizer.items"
            :key="item.item.id"
            type="button"
            class="inline-flex h-7 items-center gap-1 rounded-full border px-2.5 text-[13px] font-semibold transition-colors disabled:opacity-60"
            :class="item.selected ? 'border-primary bg-primary text-primary-foreground' : 'border-input bg-card hover:border-primary/60'"
            :aria-pressed="item.selected"
            :title="$t('recipe-finder.i-have-this')"
            :disabled="disableCheckbox"
            @click="handleCheckbox(item)"
          >
            <CheckIcon
              v-if="item.selected"
              class="size-3.5"
            />
            <PlusIcon
              v-else
              class="size-3.5"
            />
            {{ organizer.getLabel(item.item as any) }}
          </button>
        </div>
      </template>
      <!-- what stands in for foods the user doesn't have; nothing to add here -->
      <div
        v-if="substitutedFoods?.length"
        class="flex flex-wrap items-center gap-1.5"
      >
        <span class="me-1 text-sm text-muted-foreground">{{ $t("recipe-finder.substituting") }}:</span>
        <span
          v-for="(substituted, idx) in substitutedFoods"
          :key="idx"
          class="inline-flex h-7 items-center gap-1 rounded-full bg-subtle px-2.5 text-[13px] font-semibold text-subtle-foreground"
        >
          <MdiIcon
            :path="$globals.icons.swapHorizontal"
            class="size-3.5"
          />
          {{ $t("recipe-finder.substitute-for-food", {
            substitute: foodLabel(substituted.substituteFood),
            food: foodLabel(substituted.food),
          }) }}
        </span>
      </div>
    </div>
  </article>
</template>

<script setup lang="ts">
import { CheckIcon, PlusIcon } from "@lucide/vue";
import RecipeCardLineItem from "./RecipeCardLineItem.vue";
import { MdiIcon } from "~/components/ui/mdi-icon";
import type {
  IngredientFoodOut,
  IngredientFoodSummary,
  RecipeSuggestionSubstitutedFood,
  RecipeSummary,
  ToolOut,
} from "~/lib/api/types/recipe";

interface Organizer {
  type: "food" | "tool";
  item: IngredientFoodOut | ToolOut;
  selected: boolean;
}

interface Props {
  recipe: RecipeSummary;
  missingFoods?: IngredientFoodOut[] | null;
  missingTools?: ToolOut[] | null;
  substitutedFoods?: RecipeSuggestionSubstitutedFood[] | null;
  disableCheckbox?: boolean;
}
const props = withDefaults(defineProps<Props>(), {
  missingFoods: null,
  missingTools: null,
  substitutedFoods: null,
  disableCheckbox: false,
});

// same label rule the missing-food chips use
function foodLabel(food: IngredientFoodOut | IngredientFoodSummary) {
  return food.pluralName || food.name;
}

const emit = defineEmits<{
  "add-food": [food: IngredientFoodOut];
  "remove-food": [food: IngredientFoodOut];
  "add-tool": [tool: ToolOut];
  "remove-tool": [tool: ToolOut];
}>();

const { $globals } = useNuxtApp();
const missingOrganizers = computed(() => [
  {
    type: "food",
    show: props.missingFoods?.length,
    icon: $globals.icons.foods,
    items: props.missingFoods
      ? props.missingFoods.map((food) => {
          return reactive({ type: "food", item: food, selected: false } as Organizer);
        })
      : [],
    getLabel: (item: IngredientFoodOut) => item.pluralName || item.name,
  },
  {
    type: "tool",
    show: props.missingTools?.length,
    icon: $globals.icons.tools,
    items: props.missingTools
      ? props.missingTools.map((tool) => {
          return reactive({ type: "tool", item: tool, selected: false } as Organizer);
        })
      : [],
    getLabel: (item: ToolOut) => item.name,
  },
]);

function handleCheckbox(organizer: Organizer) {
  if (props.disableCheckbox) {
    return;
  }

  organizer.selected = !organizer.selected;
  if (organizer.selected) {
    if (organizer.type === "food") {
      emit("add-food", organizer.item as IngredientFoodOut);
    }
    else {
      emit("add-tool", organizer.item as ToolOut);
    }
  }
  else {
    if (organizer.type === "food") {
      emit("remove-food", organizer.item as IngredientFoodOut);
    }
    else {
      emit("remove-tool", organizer.item as ToolOut);
    }
  }
}
</script>
