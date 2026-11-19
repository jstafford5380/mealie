<template>
  <!-- Reader -->
  <div
    v-if="!isEditForm"
    class="flex flex-col gap-6 font-sans"
  >
    <section
      v-if="recipe.recipeCategory.length > 0"
      :aria-label="$t('recipe.categories')"
    >
      <h2 class="m-0 mb-2 text-sm font-semibold text-muted-foreground">
        {{ $t("recipe.categories") }}
      </h2>
      <RecipeChips
        :items="recipe.recipeCategory"
        v-bind="$attrs"
      />
    </section>
    <section
      v-if="recipe.tags.length > 0"
      :aria-label="$t('tag.tags')"
    >
      <h2 class="m-0 mb-2 text-sm font-semibold text-muted-foreground">
        {{ $t("tag.tags") }}
      </h2>
      <RecipeChips
        :items="recipe.tags"
        url-prefix="tags"
        v-bind="$attrs"
      />
    </section>
    <RecipeNutrition
      v-if="recipe.settings.showNutrition"
      v-model="recipe.nutrition"
      :edit="false"
    />
    <RecipeAssets
      v-if="recipe.settings.showAssets"
      v-model="recipe.assets"
      :edit="false"
      :slug="recipe.slug"
      :recipe-id="recipe.id"
      :hero-image-url="heroImageUrl"
      :hero-image-alt="recipe.name"
    />
  </div>

  <!-- Editor -->
  <div
    v-else
    class="flex flex-col gap-5"
  >
    <div>
      <div class="mb-1.5 text-sm font-semibold">
        {{ $t("recipe.categories") }}
      </div>
      <RecipeOrganizerSelector
        v-model="recipe.recipeCategory"
        :return-object="true"
        :show-add="true"
        selector-type="categories"
      />
    </div>
    <div>
      <div class="mb-1.5 text-sm font-semibold">
        {{ $t("tag.tags") }}
      </div>
      <RecipeOrganizerSelector
        v-model="recipe.tags"
        :return-object="true"
        :show-add="true"
        selector-type="tags"
      />
    </div>
    <div>
      <div class="mb-1.5 text-sm font-semibold">
        {{ $t('tool.required-tools') }}
      </div>
      <RecipeOrganizerSelector
        v-model="recipe.tools"
        selector-type="tools"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { usePageState } from "~/composables/recipe-page/shared-state";
import { useStaticRoutes } from "~/composables/api";
import type { RecipeOut } from "~/lib/api/types/recipe";
import RecipeOrganizerSelector from "@/components/Domain/Recipe/RecipeOrganizerSelector.vue";
import RecipeNutrition from "~/components/Domain/Recipe/RecipeNutrition.vue";
import RecipeChips from "@/components/Domain/Recipe/RecipeChips.vue";
import RecipeAssets from "@/components/Domain/Recipe/RecipeAssets.vue";

const recipe = defineModel<RecipeOut>({ required: true });
const { isEditForm, imageKey } = usePageState(recipe.value.slug);
const { recipeImage } = useStaticRoutes();

const heroImageUrl = computed(() => recipe.value.image ? recipeImage(recipe.value.id, recipe.value.image, imageKey.value) : undefined);
</script>
