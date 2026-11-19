<template>
  <div class="mx-auto w-full max-w-[1100px] px-4 pb-16 pt-3 sm:px-6 lg:pt-8">
    <RecipeOrganizerPage
      v-if="store"
      :items="store"
      :icon="$globals.icons.categories"
      item-type="categories"
      @delete="actions.deleteOne"
      @update="actions.updateOne"
    >
      <template #title>
        {{ $t("category.categories") }}
      </template>
    </RecipeOrganizerPage>
  </div>
</template>

<script setup lang="ts">
import RecipeOrganizerPage from "~/components/Domain/Recipe/RecipeOrganizerPage.vue";
import { useCategoryStore } from "~/composables/store";

definePageMeta({
  middleware: ["auth", "group-only"],
});

const { store, actions } = useCategoryStore();
const i18n = useI18n();

useSeoMeta({
  title: i18n.t("category.categories"),
});
</script>
