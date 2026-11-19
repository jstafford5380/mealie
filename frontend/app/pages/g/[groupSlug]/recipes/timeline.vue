<template>
  <div class="mx-auto w-full max-w-[760px] px-4 pb-16 pt-3 font-sans sm:px-6 lg:pt-8">
    <h1
      v-if="groupName"
      class="m-0 mb-2 text-[26px] font-bold tracking-tight sm:text-[32px]"
    >
      {{ $t("recipe.group-global-timeline", { groupName }) }}
    </h1>
    <RecipeTimeline
      v-if="queryFilter"
      v-model="ready"
      show-recipe-cards
      :query-filter="queryFilter"
    />
  </div>
</template>

<script setup lang="ts">
import { useUserApi } from "~/composables/api";
import RecipeTimeline from "~/components/Domain/Recipe/RecipeTimeline.vue";

definePageMeta({
  middleware: ["auth", "group-only"],
});

const i18n = useI18n();
const api = useUserApi();
const ready = ref<boolean>(false);

useSeoMeta({
  title: i18n.t("recipe.timeline"),
});

const groupName = ref<string>("");
const queryFilter = ref<string>("");
async function fetchHousehold() {
  const { data } = await api.households.getCurrentUserHousehold();
  if (data) {
    queryFilter.value = `recipe.group_id="${data.groupId}"`;
    groupName.value = data.group;
  }

  ready.value = true;
}

useAsyncData("house-hold", fetchHousehold);
</script>
