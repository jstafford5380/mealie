<script setup lang="ts">
import type { AppCreateLink, AppNavItem, AppNavSection } from "~/composables/use-app-navigation";
import { MenuIcon, PanelLeftOpenIcon, SearchIcon } from "@lucide/vue";
import { useLocalStorage, useMediaQuery } from "@vueuse/core";
import { DialogContent, DialogOverlay, DialogPortal, DialogRoot, DialogTitle } from "reka-ui";
import AnnouncementDialog from "~/components/Domain/Announcement/AnnouncementDialog.vue";
import { Kbd } from "~/components/ui/kbd";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { useNavGroupSlug } from "~/composables/use-app-navigation";
import { useLoggedInState } from "~/composables/use-logged-in-state";
import AppCommandSearch from "./AppCommandSearch.vue";
import AppShellBottomNav from "./AppShellBottomNav.vue";
import AppShellSidebar from "./AppShellSidebar.vue";
import TheSnackbar from "./TheSnackbar.vue";

/**
 * Application frame: persistent sidebar on large screens (collapsible), a slide-over
 * navigation sheet below that, a phone tab bar for members, and global search.
 * <v-app> stays as the root only so pages that still use Vuetify keep its context.
 */
const props = withDefaults(defineProps<{
  sections: AppNavSection[];
  cookbooks?: AppNavItem[];
  createLinks?: AppCreateLink[];
  admin?: boolean;
  /** Hide search (the basic layout has no search or navigation). */
  search?: boolean;
}>(), {
  cookbooks: () => [],
  createLinks: () => [],
  admin: false,
  search: true,
});

const { $appInfo } = useNuxtApp();
const route = useRoute();
const groupSlug = useNavGroupSlug();
const { isOwnGroup } = useLoggedInState();

const isDesktop = useMediaQuery("(min-width: 1024px)");
const collapsed = useLocalStorage("mealie-sidebar-collapsed", false);
const sheetOpen = ref(false);
const searchOpen = ref(false);
const languageOpen = ref(false);
const announcementsOpen = ref(false);

watch(() => route.fullPath, () => {
  sheetOpen.value = false;
});
watch(isDesktop, (desktop) => {
  if (desktop) {
    sheetOpen.value = false;
  }
});

const showBottomNav = computed(() => !props.admin && isOwnGroup.value && props.createLinks.length > 0);
const homeLink = computed(() => (groupSlug.value ? `/g/${groupSlug.value}` : "/"));

function openLanguage() {
  sheetOpen.value = false;
  languageOpen.value = true;
}
function openAnnouncements() {
  sheetOpen.value = false;
  announcementsOpen.value = true;
}
</script>

<template>
  <v-app class="app-shell-root">
    <a
      href="#main-content"
      class="sr-only z-[3000] rounded-control bg-primary px-4 py-2 font-sans font-semibold text-primary-foreground focus:not-sr-only focus:fixed focus:start-3 focus:top-3"
    >{{ $t("sidebar.skip-to-content") }}</a>

    <div class="flex min-h-dvh w-full bg-background font-sans text-foreground">
      <!-- Desktop sidebar -->
      <aside
        v-if="isDesktop && !collapsed"
        class="sticky top-0 h-dvh w-64 shrink-0 border-e border-sidebar-border print:hidden"
      >
        <AppShellSidebar
          :sections="sections"
          :cookbooks="cookbooks"
          :create-links="createLinks"
          :admin="admin"
          collapsible
          @collapse="collapsed = true"
          @open-language="openLanguage"
          @open-announcements="openAnnouncements"
        />
      </aside>

      <div class="flex min-w-0 flex-1 flex-col">
        <header class="sticky top-0 z-[1000] flex h-14 shrink-0 items-center gap-2 border-b bg-background/90 px-3 backdrop-blur sm:px-5 print:hidden">
          <button
            v-if="!isDesktop || collapsed"
            type="button"
            class="inline-flex size-10 items-center justify-center rounded-control text-foreground hover:bg-highlight"
            :aria-label="isDesktop ? $t('sidebar.expand-sidebar') : $t('sidebar.open-navigation')"
            :aria-expanded="isDesktop ? false : sheetOpen"
            @click="isDesktop ? (collapsed = false) : (sheetOpen = true)"
          >
            <PanelLeftOpenIcon
              v-if="isDesktop"
              class="size-5 rtl:-scale-x-100"
            />
            <MenuIcon
              v-else
              class="size-5"
            />
          </button>
          <NuxtLink
            v-if="!isDesktop || collapsed"
            :to="homeLink"
            class="flex min-w-0 items-center gap-2 rounded-item pe-1 text-[17px] no-underline font-bold tracking-tight text-foreground"
          >
            <img
              v-if="$appInfo.brandingLogoUrl"
              :src="$appInfo.brandingLogoUrl"
              alt=""
              class="size-7 rounded-item object-contain"
            >
            <span
              v-else
              class="flex size-7 shrink-0 items-center justify-center rounded-[8px] bg-brand text-brand-foreground"
            >
              <MdiIcon
                :path="$globals.icons.primary"
                class="size-4"
              />
            </span>
            <span class="truncate max-sm:hidden">{{ $appInfo.brandingName }}</span>
          </NuxtLink>

          <template v-if="search">
            <button
              type="button"
              class="ms-auto flex h-10 items-center gap-2.5 rounded-control border border-input bg-card px-3 text-[15px] text-muted-foreground transition-colors hover:border-ring/50 sm:ms-0 sm:w-full sm:max-w-md lg:max-w-lg"
              :aria-label="$t('search.search')"
              aria-haspopup="dialog"
              @click="searchOpen = true"
            >
              <SearchIcon class="size-[18px]" />
              <span class="max-sm:hidden">{{ $t("search.search-placeholder") }}</span>
              <span class="ms-auto flex items-center gap-1 max-sm:hidden">
                <Kbd>/</Kbd>
              </span>
            </button>
          </template>
          <slot name="header-end" />
        </header>

        <main
          id="main-content"
          tabindex="-1"
          class="min-w-0 flex-1 outline-none"
          :class="showBottomNav && 'max-md:pb-[calc(76px+env(safe-area-inset-bottom))]'"
        >
          <slot />
        </main>
      </div>
    </div>

    <!-- Navigation sheet (tablets and phones) -->
    <DialogRoot v-model:open="sheetOpen">
      <DialogPortal>
        <DialogOverlay class="fixed inset-0 z-[2050] bg-black/45 data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=closed]:animate-out data-[state=closed]:fade-out-0" />
        <DialogContent
          :aria-describedby="undefined"
          class="fixed inset-y-0 start-0 z-[2051] w-[min(300px,86vw)] border-e border-sidebar-border font-sans shadow-xl outline-none data-[state=open]:animate-in data-[state=open]:slide-in-from-start data-[state=closed]:animate-out data-[state=closed]:slide-out-to-start"
        >
          <DialogTitle class="sr-only">
            {{ $t("sidebar.main-navigation") }}
          </DialogTitle>
          <AppShellSidebar
            :sections="sections"
            :cookbooks="cookbooks"
            :create-links="createLinks"
            :admin="admin"
            @open-language="openLanguage"
            @open-announcements="openAnnouncements"
          />
        </DialogContent>
      </DialogPortal>
    </DialogRoot>

    <AppShellBottomNav
      v-if="showBottomNav"
      :create-links="createLinks"
      @more="sheetOpen = true"
    />

    <AppCommandSearch
      v-if="search"
      v-model:open="searchOpen"
      :sections="sections"
    />
    <AnnouncementDialog v-model="announcementsOpen" />
    <LanguageDialog v-model="languageOpen" />
    <TheSnackbar />
  </v-app>
</template>

<style>
/* Vuetify's application wrapper stays only as a context provider for legacy pages. */
.app-shell-root.v-application {
  background: var(--background) !important;
}
.app-shell-root > .v-application__wrap {
  min-height: 100dvh;
}
</style>
