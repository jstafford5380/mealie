<template>
  <div class="app-shell-root">
    <div class="flex min-h-dvh flex-col bg-background font-sans text-foreground">
      <header class="sticky top-0 z-[1000] flex h-14 shrink-0 items-center border-b bg-background/90 px-4 backdrop-blur print:hidden">
        <NuxtLink
          :to="homeLink"
          class="flex items-center gap-2.5 rounded-item text-[17px] no-underline font-bold tracking-tight text-foreground"
        >
          <img
            v-if="$appInfo.brandingLogoUrl"
            :src="$appInfo.brandingLogoUrl"
            alt=""
            class="size-7 rounded-item object-contain"
          >
          <span
            v-else
            class="flex size-7 items-center justify-center rounded-[8px] bg-brand text-brand-foreground"
          >
            <MdiIcon
              :path="$globals.icons.primary"
              class="size-4"
            />
          </span>
          {{ $appInfo.brandingName }}
        </NuxtLink>
      </header>
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
import { MdiIcon } from "~/components/ui/mdi-icon";
import { useNavGroupSlug } from "~/composables/use-app-navigation";
import { useGlobalI18n } from "~/composables/use-global-i18n";

useGlobalI18n(); // ensure i18n is initialized
const groupSlug = useNavGroupSlug();
const homeLink = computed(() => (groupSlug.value ? `/g/${groupSlug.value}` : "/"));
</script>
