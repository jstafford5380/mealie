<script setup lang="ts">
import type { AppCreateLink, AppNavItem, AppNavSection } from "~/composables/use-app-navigation";
import { ArrowLeftIcon, PanelLeftCloseIcon } from "@lucide/vue";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { ScrollArea } from "~/components/ui/scroll-area";
import { useAnnouncements } from "~/composables/use-announcements";
import { useLoggedInState } from "~/composables/use-logged-in-state";
import { useNavGroupSlug } from "~/composables/use-app-navigation";
import AppCreateMenu from "./AppCreateMenu.vue";
import AppShellNavList from "./AppShellNavList.vue";
import AppUserMenu from "./AppUserMenu.vue";

defineProps<{
  sections: AppNavSection[];
  cookbooks?: AppNavItem[];
  createLinks?: AppCreateLink[];
  /** Admin area: shows a link back to the app. */
  admin?: boolean;
  /** Desktop only: offer the collapse button. */
  collapsible?: boolean;
}>();

const emit = defineEmits<{
  "open-language": [];
  "open-announcements": [];
  "collapse": [];
}>();

const { $appInfo } = useNuxtApp();
const { loggedIn } = useLoggedInState();
const { announcementsEnabled, newAnnouncements } = useAnnouncements();
const groupSlug = useNavGroupSlug();
const homeLink = computed(() => (groupSlug.value ? `/g/${groupSlug.value}` : "/"));
</script>

<template>
  <div class="flex h-full flex-col bg-sidebar text-sidebar-foreground">
    <div class="flex h-16 shrink-0 items-center gap-2 px-4">
      <NuxtLink
        :to="homeLink"
        class="flex min-w-0 flex-1 items-center gap-2.5 rounded-item py-1 text-foreground no-underline focus-visible:outline-2 focus-visible:outline-sidebar-ring"
      >
        <img
          v-if="$appInfo.brandingLogoUrl"
          :src="$appInfo.brandingLogoUrl"
          alt=""
          class="size-8 rounded-item object-contain"
        >
        <span
          v-else
          class="flex size-8 shrink-0 items-center justify-center rounded-[9px] bg-brand text-brand-foreground"
        >
          <MdiIcon
            :path="$globals.icons.primary"
            class="size-[19px]"
          />
        </span>
        <span class="truncate text-[19px] font-bold tracking-tight">{{ $appInfo.brandingName }}</span>
      </NuxtLink>
      <button
        v-if="collapsible"
        type="button"
        class="inline-flex size-8 shrink-0 items-center justify-center rounded-item text-muted-foreground hover:bg-sidebar-highlight hover:text-sidebar-highlight-foreground"
        :aria-label="$t('sidebar.collapse-sidebar')"
        @click="emit('collapse')"
      >
        <PanelLeftCloseIcon class="size-[18px] rtl:-scale-x-100" />
      </button>
    </div>

    <div
      v-if="admin || createLinks?.length"
      class="px-3 pb-2"
    >
      <NuxtLink
        v-if="admin"
        :to="homeLink"
        class="flex h-10 items-center gap-2 rounded-item px-2.5 text-sm font-semibold text-primary no-underline hover:bg-sidebar-highlight"
      >
        <ArrowLeftIcon class="size-4 rtl:-scale-x-100" />
        {{ $t("sidebar.back-to-app") }}
      </NuxtLink>
      <AppCreateMenu
        v-else-if="createLinks?.length"
        :links="createLinks"
      />
    </div>

    <ScrollArea class="min-h-0 flex-1">
      <nav
        :aria-label="$t('sidebar.main-navigation')"
        class="flex flex-col gap-5 px-3 pb-4 pt-2"
      >
        <section
          v-for="section in sections"
          :key="section.key"
          class="flex flex-col gap-1"
        >
          <h2
            v-if="section.title"
            class="m-0 px-2.5 pb-1 text-[12.5px] font-semibold text-muted-foreground"
          >
            {{ section.title }}
          </h2>
          <AppShellNavList :items="section.items" />
        </section>
        <section
          v-if="cookbooks?.length"
          class="flex flex-col gap-1"
        >
          <h2 class="m-0 px-2.5 pb-1 text-[12.5px] font-semibold text-muted-foreground">
            {{ $t("cookbook.cookbooks") }}
          </h2>
          <AppShellNavList :items="cookbooks" />
        </section>
      </nav>
    </ScrollArea>

    <div class="flex shrink-0 flex-col gap-1 border-t border-sidebar-border p-3">
      <button
        v-if="loggedIn && announcementsEnabled"
        type="button"
        class="flex h-10 w-full items-center gap-3 rounded-item px-2.5 text-[14.5px] font-medium hover:bg-sidebar-highlight/70 hover:text-sidebar-highlight-foreground"
        @click="emit('open-announcements')"
      >
        <MdiIcon
          :path="$globals.icons.bullhornVariant"
          class="size-[19px] opacity-80"
        />
        <span class="flex-1 text-start">{{ $t("announcements.announcements") }}</span>
        <span
          v-if="newAnnouncements.length"
          class="inline-flex min-w-5 items-center justify-center rounded-full bg-brand px-1.5 text-xs font-bold text-brand-foreground"
        >
          {{ newAnnouncements.length }}
          <span class="sr-only">{{ $t("announcements.unread") }}</span>
        </span>
      </button>
      <AppUserMenu @open-language="emit('open-language')" />
    </div>
  </div>
</template>
