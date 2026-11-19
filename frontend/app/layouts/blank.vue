<template>
  <div class="app-shell-root">
    <div class="flex min-h-dvh flex-col bg-background font-sans text-foreground">
      <div
        v-if="$appInfo.demoStatus"
        role="status"
        class="sticky top-0 z-[1000] border-b border-brand/40 bg-brand-soft px-4 py-2 text-center text-sm font-semibold"
      >
        {{ $t("demo.info_message_with_version", { version: $appInfo.version }) }}
      </div>
      <main
        id="main-content"
        class="min-w-0 flex-1"
      >
        <NuxtPage />
      </main>
    </div>
    <TheSnackbar />
  </div>
</template>

<script setup lang="ts">
import TheSnackbar from "~/components/Layout/LayoutParts/TheSnackbar.vue";
</script>
