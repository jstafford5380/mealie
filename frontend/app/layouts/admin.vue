<template>
  <AppShell
    :sections="sections"
    admin
  >
    <NuxtPage />
  </AppShell>
</template>

<script setup lang="ts">
import AppShell from "~/components/Layout/LayoutParts/AppShell.vue";
import { useAdminNavigation } from "~/composables/use-app-navigation";
import { useGlobalI18n } from "~/composables/use-global-i18n";

useGlobalI18n(); // ensure i18n is initialized
const { sections } = useAdminNavigation();
</script>
