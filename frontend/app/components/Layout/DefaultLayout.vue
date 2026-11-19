<template>
  <AppShell
    :sections="sections"
    :cookbooks="cookbookItems"
    :create-links="createLinks"
  >
    <NuxtPage />
  </AppShell>
</template>

<script setup lang="ts">
import AppShell from "~/components/Layout/LayoutParts/AppShell.vue";
import { useAppNavigation } from "~/composables/use-app-navigation";

const { sections, cookbookItems, createLinks } = useAppNavigation();
</script>
