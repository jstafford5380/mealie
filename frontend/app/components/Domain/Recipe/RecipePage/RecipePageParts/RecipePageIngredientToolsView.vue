<template>
  <div class="flex flex-col gap-6 font-sans">
    <RecipeIngredients
      :value="recipe.recipeIngredient"
      :scale="scale"
      :is-cook-mode="isCookMode"
      :storage-key="ingredientStorageKey"
    />
    <section
      v-if="!isEditMode && recipe.tools && recipe.tools.length > 0"
      :aria-label="$t('tool.required-tools')"
    >
      <h2
        class="m-0 mb-2 font-bold tracking-tight"
        :class="isCookMode ? 'text-base' : 'text-xl'"
      >
        {{ $t('tool.required-tools') }}
      </h2>
      <ul class="m-0 list-none p-0">
        <li
          v-for="(tool, index) in recipe.tools"
          :key="index"
        >
          <label class="flex cursor-pointer items-center gap-3 py-2 text-[15.5px]">
            <Checkbox
              v-model="recipeTools[index]!.onHand"
              class="size-5"
              @update:model-value="updateTool(index)"
            />
            <span :class="recipeTools[index]?.onHand && 'text-muted-foreground'">{{ tool.name }}</span>
          </label>
        </li>
      </ul>
    </section>
  </div>
</template>

<script setup lang="ts">
import { Checkbox } from "~/components/ui/checkbox";
import type { RecipeToolWithOnHand } from "~/composables/store/use-tool-store";
import { useLoggedInState } from "~/composables/use-logged-in-state";
import { usePageState, usePageUser } from "~/composables/recipe-page/shared-state";
import { useToolStore } from "~/composables/store";
import type { RecipeOut } from "~/lib/api/types/recipe";
import RecipeIngredients from "~/components/Domain/Recipe/RecipeIngredients.vue";

interface Props {
  recipe: RecipeOut;
  scale: number;
  isCookMode?: boolean;
  ingredientStorageKey?: string;
}
const props = withDefaults(defineProps<Props>(), {
  isCookMode: false,
  ingredientStorageKey: undefined,
});

const { isOwnGroup } = useLoggedInState();

const toolStore = isOwnGroup.value ? useToolStore() : null;
const { user } = usePageUser();
const { isEditMode } = usePageState(props.recipe.slug);

const recipeTools = ref<RecipeToolWithOnHand[]>([]);
watch(() => props.recipe.tools, () => {
  if (!(user.householdSlug && toolStore)) {
    recipeTools.value = props.recipe.tools.map(tool => ({ ...tool, onHand: false }) as RecipeToolWithOnHand);
  }
  else {
    recipeTools.value = props.recipe.tools.map((tool) => {
      const onHand = tool.householdsWithTool?.includes(user.householdSlug) || false;
      return { ...tool, onHand } as RecipeToolWithOnHand;
    });
  }
}, { immediate: true });

function updateTool(index: number) {
  if (user.id && user.householdSlug && toolStore) {
    const tool = recipeTools.value[index];
    if (tool.onHand && !tool.householdsWithTool?.includes(user.householdSlug)) {
      if (!tool.householdsWithTool) {
        tool.householdsWithTool = [user.householdSlug];
      }
      else {
        tool.householdsWithTool.push(user.householdSlug);
      }
    }
    else if (!tool.onHand && tool.householdsWithTool?.includes(user.householdSlug)) {
      tool.householdsWithTool = tool.householdsWithTool.filter(household => household !== user.householdSlug);
    }

    toolStore.actions.updateOne(tool);
  }
  else {
    console.log("no user, skipping server update");
  }
}
</script>
