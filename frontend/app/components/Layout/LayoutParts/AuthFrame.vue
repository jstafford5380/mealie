<template>
  <!-- Shared frame for sign-in, registration and password pages: brand, one card, quiet links -->
  <div class="flex min-h-dvh flex-col items-center bg-background px-4 py-10 font-sans sm:justify-center sm:py-16">
    <div
      class="flex w-full flex-col gap-6"
      :class="wide ? 'max-w-2xl' : 'max-w-md'"
    >
      <div class="flex items-center gap-3">
        <AppLogo :size="44" />
        <span class="text-[22px] font-bold tracking-tight">{{ $appInfo.brandingName }}</span>
      </div>

      <slot name="above" />

      <section class="rounded-panel border bg-card p-6 shadow-sm sm:p-8">
        <header
          v-if="title"
          class="mb-6"
        >
          <h1 class="m-0 text-[26px] font-bold tracking-tight">
            {{ title }}
          </h1>
          <p
            v-if="description"
            class="m-0 mt-1.5 text-[15px] text-muted-foreground"
          >
            {{ description }}
          </p>
        </header>
        <slot />
      </section>

      <slot name="below" />

      <nav
        v-if="links"
        class="flex flex-wrap items-center justify-center gap-x-5 gap-y-1 text-sm"
        :aria-label="$t('about.about')"
      >
        <a
          v-for="link in footerLinks"
          :key="link.href"
          :href="link.href"
          target="_blank"
          rel="noopener"
          class="inline-flex items-center gap-1.5 text-muted-foreground no-underline hover:text-foreground"
        >
          <MdiIcon
            :path="link.icon"
            class="size-4"
          />
          {{ link.text }}
        </a>
      </nav>
    </div>
  </div>
</template>

<script setup lang="ts">
import { MdiIcon } from "~/components/ui/mdi-icon";

withDefaults(defineProps<{
  title?: string;
  description?: string;
  /** Show the Sponsor / GitHub / Docs links under the card. */
  links?: boolean;
  wide?: boolean;
}>(), {
  links: true,
  wide: false,
});

const i18n = useI18n();
const { $globals } = useNuxtApp();
const footerLinks = computed(() => [
  { text: i18n.t("about.sponsor"), icon: $globals.icons.heart, href: "https://github.com/sponsors/hay-kot" },
  { text: i18n.t("about.github"), icon: $globals.icons.github, href: "https://github.com/mealie-recipes/mealie" },
  { text: i18n.t("about.docs"), icon: $globals.icons.folderOutline, href: "https://docs.mealie.io/" },
]);
</script>
