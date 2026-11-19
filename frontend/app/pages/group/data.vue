<template>
  <div class="mx-auto w-full max-w-[1100px] px-4 pb-16 pt-3 font-sans sm:px-6 lg:pt-8">
    <header class="mb-4">
      <h1 class="m-0 text-[26px] font-bold tracking-tight sm:text-[32px]">
        {{ $t('data-pages.data-management') }}
      </h1>
      <p class="m-0 mt-1 max-w-[65ch] text-[15px] text-muted-foreground">
        {{ $t('data-pages.data-management-intro') }}
      </p>
    </header>

    <!-- one row of tabs; scrolls sideways on phones -->
    <nav
      class="-mx-4 mb-6 overflow-x-auto border-b px-4 sm:mx-0 sm:px-0"
      :aria-label="$t('data-pages.data-management')"
    >
      <ul class="m-0 flex w-max list-none items-center gap-1 p-0">
        <template
          v-for="group, groupIndex in DATA_TYPE_GROUPS"
          :key="groupIndex"
        >
          <li
            v-if="groupIndex > 0"
            class="mx-1 h-5 w-px bg-border"
            aria-hidden="true"
          />
          <li
            v-for="option in group"
            :key="option.to"
          >
            <NuxtLink
              :to="option.to"
              class="-mb-px inline-flex h-11 items-center border-b-2 px-3 text-[15px] font-medium whitespace-nowrap no-underline transition-colors"
              :class="route.path.startsWith(option.to) ? 'border-primary text-foreground' : 'border-transparent text-muted-foreground hover:text-foreground'"
              :aria-current="route.path.startsWith(option.to) ? 'page' : undefined"
            >
              {{ option.text }}
            </NuxtLink>
          </li>
        </template>
      </ul>
    </nav>

    <NuxtPage />
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: ["auth", "can-organize-only"],
});

const i18n = useI18n();
const route = useRoute();

// Grouped the way people think of them: recipes, shopping data, organizers
const DATA_TYPE_GROUPS = computed(() => [
  [
    { text: i18n.t("general.recipes"), to: "/group/data/recipes" },
    { text: i18n.t("recipe.recipe-actions"), to: "/group/data/recipe-actions" },
  ],
  [
    { text: i18n.t("general.foods"), to: "/group/data/foods" },
    { text: i18n.t("general.units"), to: "/group/data/units" },
    { text: i18n.t("data-pages.labels.labels"), to: "/group/data/labels" },
  ],
  [
    { text: i18n.t("category.categories"), to: "/group/data/categories" },
    { text: i18n.t("tag.tags"), to: "/group/data/tags" },
    { text: i18n.t("tool.tools"), to: "/group/data/tools" },
  ],
]);

useSeoMeta({
  title: i18n.t("data-pages.data-management"),
});
</script>
