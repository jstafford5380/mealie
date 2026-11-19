<template>
  <div class="mx-auto flex w-full max-w-[1400px] flex-col gap-6 px-4 pb-16 pt-6 font-sans sm:px-6 lg:px-8">
    <h1 class="m-0 text-[28px] font-bold tracking-tight text-foreground sm:text-[32px]">
      {{ $t("general.recipes") }}
    </h1>
    <RecipeExplorerToday
      v-if="isOwnGroup"
      :group-slug="groupSlug"
    />
    <RecipeExplorerPageSearch
      ref="searchComponent"
      @ready="onSearchReady"
    />
    <RecipeCardSection
      v-if="ready"
      :recipes="recipes"
      :query="searchQuery"
      disable-sort
      @item-selected="onItemSelected"
      @replace-recipes="replaceRecipes"
      @append-recipes="appendRecipes"
    />
  </div>
</template>

<script setup lang="ts">
import RecipeExplorerPageSearch from "./RecipeExplorerPageParts/RecipeExplorerPageSearch.vue";
import RecipeExplorerToday from "./RecipeExplorerPageParts/RecipeExplorerToday.vue";
import { useLoggedInState } from "~/composables/use-logged-in-state";
import RecipeCardSection from "~/components/Domain/Recipe/RecipeCardSection.vue";
import { useLazyRecipes } from "~/composables/recipes";

const auth = useMealieAuth();
const route = useRoute();

const { isOwnGroup } = useLoggedInState();
const groupSlug = computed(() => route.params.groupSlug as string || auth.user.value?.groupSlug || "");

const { recipes, appendRecipes, replaceRecipes } = useLazyRecipes(isOwnGroup.value ? null : groupSlug.value);

const ready = ref(false);
const searchComponent = ref<InstanceType<typeof RecipeExplorerPageSearch>>();

const searchQuery = computed(() => {
  return searchComponent.value?.passedQueryWithSeed || {};
});

function onSearchReady() {
  ready.value = true;
}

function onItemSelected(item: any, urlPrefix: string) {
  searchComponent.value?.filterItems(item, urlPrefix);
}
</script>
