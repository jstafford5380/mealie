<script setup lang="ts">
import type { AppCreateLink } from "~/composables/use-app-navigation";
import { MenuIcon } from "@lucide/vue";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { useNavGroupSlug } from "~/composables/use-app-navigation";
import AppCreateMenu from "./AppCreateMenu.vue";

/** Phone tab bar for members in their own group: the three daily destinations, create, and everything else. */
defineProps<{
  createLinks: AppCreateLink[];
}>();
const emit = defineEmits<{ more: [] }>();

const { $globals } = useNuxtApp();
const i18n = useI18n();
const route = useRoute();
const groupSlug = useNavGroupSlug();

const tabs = computed(() => [
  {
    key: "recipes",
    title: i18n.t("general.recipes"),
    icon: $globals.icons.silverwareForkKnife,
    to: `/g/${groupSlug.value}`,
    active: route.path === `/g/${groupSlug.value}` || route.path.startsWith(`/g/${groupSlug.value}/r/`),
  },
  {
    key: "plan",
    title: i18n.t("sidebar.section-plan"),
    icon: $globals.icons.calendarMultiselect,
    to: "/household/mealplan/planner/view",
    active: route.path.startsWith("/household/mealplan"),
  },
  {
    key: "lists",
    title: i18n.t("sidebar.tab-lists"),
    icon: $globals.icons.formatListCheck,
    to: "/shopping-lists",
    active: route.path.startsWith("/shopping-lists"),
  },
]);

const tabClass = "flex no-underline min-w-0 flex-1 flex-col items-center justify-center gap-1 rounded-item px-1 py-1 text-[11.5px] font-semibold text-muted-foreground aria-[current=page]:text-primary focus-visible:outline-2 focus-visible:outline-ring";
</script>

<template>
  <nav
    :aria-label="$t('sidebar.main-navigation')"
    class="fixed inset-x-0 bottom-0 z-[1000] flex h-[calc(64px+env(safe-area-inset-bottom))] items-start border-t bg-card/95 px-2 pt-1.5 pb-[env(safe-area-inset-bottom)] backdrop-blur md:hidden print:hidden"
  >
    <NuxtLink
      v-for="tab in tabs.slice(0, 2)"
      :key="tab.key"
      :to="tab.to"
      :class="tabClass"
      :aria-current="tab.active ? 'page' : undefined"
    >
      <MdiIcon
        :path="tab.icon"
        class="size-6"
      />
      <span class="max-w-full truncate">{{ tab.title }}</span>
    </NuxtLink>
    <div class="flex flex-1 justify-center">
      <AppCreateMenu
        :links="createLinks"
        variant="fab"
      />
    </div>
    <NuxtLink
      :to="tabs[2]!.to"
      :class="tabClass"
      :aria-current="tabs[2]!.active ? 'page' : undefined"
    >
      <MdiIcon
        :path="tabs[2]!.icon"
        class="size-6"
      />
      <span class="max-w-full truncate">{{ tabs[2]!.title }}</span>
    </NuxtLink>
    <button
      type="button"
      :class="tabClass"
      @click="emit('more')"
    >
      <MenuIcon class="size-6" />
      <span>{{ $t("sidebar.more") }}</span>
    </button>
  </nav>
</template>
