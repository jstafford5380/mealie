<template>
  <div
    v-if="user"
    class="mx-auto flex w-full max-w-[900px] flex-col gap-10 px-4 pb-16 pt-3 font-sans sm:px-6 lg:pt-8"
  >
    <header class="flex flex-wrap items-center gap-4">
      <UserAvatar
        :tooltip="false"
        size="72"
        :user-id="user.id"
      />
      <div class="min-w-0 flex-1">
        <h1 class="m-0 text-[26px] font-bold tracking-tight sm:text-[32px]">
          {{ $t('profile.welcome-user', [user.fullName]) }}
        </h1>
        <p class="m-0 mt-1 text-[15px] text-muted-foreground">
          {{ $t('profile.description') }}
        </p>
      </div>
      <Button
        v-if="user.canInvite"
        variant="outline"
        @click="inviteDialog = true"
      >
        <MdiIcon
          :path="$globals.icons.accountPlusOutline"
          class="size-4"
        />
        {{ $t('profile.get-invite-link') }}
      </Button>
      <UserInviteDialog v-model="inviteDialog" />
    </header>

    <section v-if="Object.keys(filteredStats).length">
      <h2 class="m-0 text-base font-semibold">
        {{ $t('profile.household-statistics') }}
      </h2>
      <p class="m-0 mt-1 mb-3 text-sm text-muted-foreground">
        {{ $t('profile.household-statistics-description') }}
      </p>
      <div class="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5">
        <NuxtLink
          v-for="(value, key) in filteredStats"
          :key="key"
          :to="getStatsTo(key)"
          class="flex flex-col gap-1 rounded-card border bg-card px-4 py-3 text-foreground no-underline transition-colors hover:border-primary/50"
        >
          <span class="flex items-center gap-1.5 text-sm text-muted-foreground">
            <MdiIcon
              :path="getStatsIcon(key)"
              class="size-4"
            />
            {{ getStatsTitle(key) }}
          </span>
          <span class="text-[26px] font-bold tabular-nums">{{ value }}</span>
        </NuxtLink>
      </div>
    </section>

    <section
      v-for="section in sections"
      :key="section.title"
    >
      <h2 class="m-0 text-base font-semibold">
        {{ section.title }}
      </h2>
      <p class="m-0 mt-1 mb-3 text-sm text-muted-foreground">
        {{ section.description }}
      </p>
      <div class="grid gap-2 sm:grid-cols-2">
        <NuxtLink
          v-for="link in section.links"
          :key="link.to"
          :to="link.to"
          class="group flex items-start gap-3 rounded-card border bg-card p-4 text-foreground no-underline transition-colors hover:border-primary/50 hover:bg-primary/5"
        >
          <span class="inline-flex size-10 shrink-0 items-center justify-center rounded-full bg-subtle text-subtle-foreground">
            <MdiIcon
              :path="link.icon"
              class="size-5"
            />
          </span>
          <span class="min-w-0 flex-1">
            <span class="block font-semibold">{{ link.title }}</span>
            <span class="mt-0.5 block text-sm text-muted-foreground">{{ link.description }}</span>
          </span>
          <ChevronRightIcon class="mt-2.5 size-4 shrink-0 text-muted-foreground group-hover:text-foreground rtl:rotate-180" />
        </NuxtLink>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ChevronRightIcon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { useUserApi } from "~/composables/api";
import UserAvatar from "@/components/Domain/User/UserAvatar.vue";
import { useAsyncKey } from "~/composables/use-utils";
import type { UserOut } from "~/lib/api/types/user";
import UserInviteDialog from "~/components/Domain/User/UserInviteDialog.vue";

definePageMeta({
  name: "UserProfile",
  middleware: ["auth"],
  scrollToTop: true,
});

const i18n = useI18n();
const auth = useMealieAuth();
const { $appInfo } = useNuxtApp();
const route = useRoute();
const groupSlug = computed(() => route.params.groupSlug || auth.user.value?.groupSlug || "");

useSeoMeta({
  title: i18n.t("settings.profile"),
});

const user = computed<UserOut | null>(() => {
  const authUser = auth.user.value;
  if (!authUser) return null;

  // Override canInvite if password login is disabled
  const canInvite = !$appInfo.allowPasswordLogin ? false : authUser.canInvite;

  return {
    ...authUser,
    canInvite,
  };
});

const inviteDialog = ref(false);
const api = useUserApi();

const { data: stats } = useAsyncData(useAsyncKey(), async () => {
  const { data } = await api.households.statistics();

  if (data) {
    return data;
  }
});

const filteredStats = computed(() => {
  const statsData = stats.value;
  if (!statsData) return {};
  if (!user.value?.canManage) {
    const { totalUsers, ...rest } = statsData;
    return rest;
  }
  return statsData;
});

const statsText: { [key: string]: string } = {
  totalRecipes: i18n.t("general.recipes"),
  totalUsers: i18n.t("user.users"),
  totalCategories: i18n.t("sidebar.categories"),
  totalTags: i18n.t("sidebar.tags"),
  totalTools: i18n.t("tool.tools"),
};

function getStatsTitle(key: string) {
  return statsText[key] ?? "unknown";
}

const { $globals } = useNuxtApp();

const iconText: { [key: string]: string } = {
  totalUsers: $globals.icons.user,
  totalCategories: $globals.icons.categories,
  totalTags: $globals.icons.tags,
  totalTools: $globals.icons.potSteam,
};

function getStatsIcon(key: string) {
  return iconText[key] ?? $globals.icons.primary;
}

const statsTo = computed<{ [key: string]: string }>(() => {
  return {
    totalRecipes: `/g/${groupSlug.value}/`,
    totalUsers: "/household/members",
    totalCategories: `/g/${groupSlug.value}/recipes/categories`,
    totalTags: `/g/${groupSlug.value}/recipes/tags`,
    totalTools: `/g/${groupSlug.value}/recipes/tools`,
  };
});

function getStatsTo(key: string) {
  return statsTo.value[key] ?? "unknown";
}

// Each section lists only the pages this user can open, as the old cards did
const sections = computed(() => {
  const u = user.value;
  if (!u) {
    return [];
  }
  const advanced = !!u.advanced;
  const all = [
    {
      title: i18n.t("profile.personal"),
      description: i18n.t("profile.personal-description"),
      links: [
        { show: true, to: "/user/profile/edit", icon: $globals.icons.user, title: i18n.t("profile.user-settings"), description: i18n.t("profile.user-settings-description") },
        { show: advanced, to: "/user/profile/api-tokens", icon: $globals.icons.api, title: i18n.t("settings.token.api-tokens"), description: i18n.t("profile.api-tokens-description") },
      ],
    },
    {
      title: i18n.t("household.household"),
      description: i18n.t("profile.household-description"),
      links: [
        { show: !!u.canManageHousehold, to: "/household", icon: $globals.icons.household, title: i18n.t("profile.household-settings"), description: i18n.t("profile.household-settings-description") },
        { show: true, to: `/g/${groupSlug.value}/cookbooks`, icon: $globals.icons.book, title: i18n.t("sidebar.cookbooks"), description: i18n.t("profile.cookbooks-description") },
        { show: !!u.canManage, to: "/household/members", icon: $globals.icons.group, title: i18n.t("profile.members"), description: i18n.t("profile.members-description") },
        { show: advanced && !!u.canManageHousehold, to: "/household/webhooks", icon: $globals.icons.webhook, title: i18n.t("settings.webhooks.webhooks"), description: i18n.t("profile.webhooks-description") },
        { show: advanced && !!u.canManageHousehold, to: "/household/notifiers", icon: $globals.icons.bellPlus, title: i18n.t("profile.notifiers"), description: i18n.t("profile.notifiers-description") },
      ],
    },
    {
      title: i18n.t("group.group"),
      description: i18n.t("profile.group-description"),
      links: [
        { show: !!u.canManage, to: "/group", icon: $globals.icons.cog, title: i18n.t("profile.group-settings"), description: i18n.t("profile.group-settings-description") },
        { show: !!u.canOrganize, to: "/group/data/foods", icon: $globals.icons.database, title: i18n.t("profile.manage-data"), description: i18n.t("profile.manage-data-description") },
        { show: advanced, to: "/group/migrations", icon: $globals.icons.import, title: i18n.t("profile.data-migrations"), description: i18n.t("profile.data-migrations-description") },
      ],
    },
  ];
  return all
    .map(section => ({ ...section, links: section.links.filter(link => link.show) }))
    .filter(section => section.links.length);
});
</script>
