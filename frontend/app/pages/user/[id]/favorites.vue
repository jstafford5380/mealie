<template>
  <div class="mx-auto w-full max-w-[1100px] px-4 pb-16 pt-3 sm:px-6 lg:pt-8">
    <RecipeCardSection
      v-if="recipes && isOwnGroup"
      :icon="$globals.icons.heart"
      :title="$t('user.user-favorites')"
      :recipes="recipes"
      :query="query"
      @sort-recipes="assignSorted"
      @replace-recipes="replaceRecipes"
      @append-recipes="appendRecipes"
      @delete="removeRecipe"
    />
  </div>
</template>

<script setup lang="ts">
import RecipeCardSection from "~/components/Domain/Recipe/RecipeCardSection.vue";
import { useLazyRecipes } from "~/composables/recipes";
import { useLoggedInState } from "~/composables/use-logged-in-state";

definePageMeta({
  middleware: ["auth"],
});

const route = useRoute();
const i18n = useI18n();
const { isOwnGroup } = useLoggedInState();

useSeoMeta({
  title: i18n.t("general.favorites"),
});

const userId = route.params.id;
const query = { queryFilter: `favoritedBy.id = "${userId}"` };
const { recipes, appendRecipes, assignSorted, removeRecipe, replaceRecipes } = useLazyRecipes();
</script>

<style scoped></style>
