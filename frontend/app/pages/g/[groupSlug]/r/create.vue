<template>
  <div class="mx-auto w-full max-w-[860px] px-4 pb-16 pt-3 font-sans sm:px-6 lg:pt-8">
    <header class="mb-4">
      <h1 class="m-0 text-[26px] font-bold tracking-tight sm:text-[32px]">
        {{ $t('recipe.recipe-creation') }}
      </h1>
      <p class="m-0 mt-1 text-[15px] text-muted-foreground">
        {{ $t('recipe.select-one-of-the-various-ways-to-create-a-recipe') }}
      </p>
    </header>

    <!-- one tab per way in; scrolls sideways on phones -->
    <nav
      class="-mx-4 mb-6 overflow-x-auto border-b px-4 sm:mx-0 sm:px-0"
      :aria-label="$t('recipe.recipe-creation')"
    >
      <ul class="m-0 flex w-max list-none items-center gap-1 p-0">
        <li
          v-for="page in visibleSubpages"
          :key="page.value"
        >
          <NuxtLink
            :to="{ path: `/g/${groupSlug}/r/create/${page.value}`, query: route.query }"
            class="-mb-px inline-flex h-11 items-center gap-2 border-b-2 px-3 text-[15px] font-medium whitespace-nowrap no-underline transition-colors"
            :class="subpage === page.value ? 'border-primary text-foreground' : 'border-transparent text-muted-foreground hover:text-foreground'"
            :aria-current="subpage === page.value ? 'page' : undefined"
          >
            <MdiIcon
              :path="page.icon"
              class="size-4"
            />
            {{ page.text }}
          </NuxtLink>
        </li>
      </ul>
    </nav>

    <section>
      <NuxtPage />
    </section>

    <AdvancedOnly>
      <p class="m-0 mt-10 text-center text-sm">
        <NuxtLink
          to="/group/migrations"
          class="font-semibold text-primary no-underline hover:underline"
        >
          {{ $t('recipe.looking-for-migrations') }}
        </NuxtLink>
      </p>
    </AdvancedOnly>
  </div>
</template>

<script setup lang="ts">
import type { MenuItem } from "~/components/global/BaseOverflowButton.vue";
import { MdiIcon } from "~/components/ui/mdi-icon";
import AdvancedOnly from "~/components/global/AdvancedOnly.vue";
import { useGroupSelf } from "~/composables/use-groups";

definePageMeta({
  middleware: ["auth", "group-only"],
});

const i18n = useI18n();
const auth = useMealieAuth();
const { $globals } = useNuxtApp();
const { group } = useGroupSelf();

useSeoMeta({
  title: i18n.t("general.create"),
});

const subpages = computed<MenuItem[]>(() => [
  {
    icon: $globals.icons.link,
    text: i18n.t("recipe.import-with-url"),
    value: "url",
  },
  {
    icon: $globals.icons.link,
    text: i18n.t("recipe.bulk-url-import"),
    value: "bulk",
  },
  {
    icon: $globals.icons.codeTags,
    text: i18n.t("recipe.import-from-html-or-json"),
    value: "html",
  },
  {
    icon: $globals.icons.autoFix,
    text: i18n.t("recipe.import-with-ai"),
    value: "ai",
    hide: !group.value?.aiProviderSettings?.aiEnabled,
  },
  {
    icon: $globals.icons.edit,
    text: i18n.t("recipe.create-recipe"),
    value: "new",
  },
  {
    icon: $globals.icons.zip,
    text: i18n.t("recipe.import-with-zip"),
    value: "zip",
  },
  {
    icon: $globals.icons.robot,
    text: i18n.t("recipe.debug-scraper"),
    value: "debug",
  },
]);

const route = useRoute();
const router = useRouter();
const groupSlug = computed(() => route.params.groupSlug || auth.user.value?.groupSlug || "");

const subpage = computed({
  set(subpage: string) {
    router.push({ path: `/g/${groupSlug.value}/r/create/${subpage}`, query: route.query });
  },
  get() {
    return route.path.split("/").pop() ?? "url";
  },
});

const visibleSubpages = computed(() => subpages.value.filter(page => !page.hide) as (MenuItem & { value: string; icon: string })[]);
</script>
