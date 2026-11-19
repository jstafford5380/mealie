<template>
  <div class="flex flex-col gap-6 font-sans">
    <section
      v-for="section, idx in sections"
      :key="idx"
      class="flex flex-col gap-2"
    >
      <h3 class="m-0 text-base font-semibold">
        {{ section.title }}
      </h3>
      <div class="grid gap-2 sm:grid-cols-2">
        <NuxtLink
          v-for="link, linkIdx in section.links"
          :key="linkIdx"
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
            <span class="block font-semibold">{{ link.text }}</span>
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
import { MdiIcon } from "~/components/ui/mdi-icon";

const i18n = useI18n();
const auth = useMealieAuth();
const groupSlug = computed(() => auth.user.value?.groupSlug);
const { $globals } = useNuxtApp();

const sections = computed(() => [
  {
    title: i18n.t("profile.data-migrations"),
    links: [
      {
        icon: $globals.icons.backupRestore,
        to: "/admin/backups",
        text: i18n.t("settings.backup.backup-restore"),
        description: i18n.t("admin.setup.restore-from-v1-backup"),
      },
      {
        icon: $globals.icons.import,
        to: "/group/migrations",
        text: i18n.t("migration.recipe-migration"),
        description: i18n.t("migration.migration-description"),
      },
    ],
  },
  {
    title: i18n.t("recipe.create-recipes"),
    links: [
      {
        icon: $globals.icons.createAlt,
        to: `/g/${groupSlug.value || ""}/r/create/new`,
        text: i18n.t("recipe.create-recipe"),
        description: i18n.t("recipe.create-recipe-description"),
      },
      {
        icon: $globals.icons.link,
        to: `/g/${groupSlug.value || ""}/r/create/url`,
        text: i18n.t("recipe.import-with-url"),
        description: i18n.t("recipe.scrape-recipe-description"),
      },
    ],
  },
  {
    title: i18n.t("user.manage-users"),
    links: [
      {
        icon: $globals.icons.group,
        to: "/admin/manage/users",
        text: i18n.t("user.manage-users"),
        description: i18n.t("user.manage-users-description"),
      },
      {
        icon: $globals.icons.user,
        to: "/user/profile",
        text: i18n.t("profile.manage-user-profile"),
        description: i18n.t("admin.setup.manage-profile-or-get-invite-link"),
      },
    ],
  },
]);
</script>
