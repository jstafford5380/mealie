<template>
  <BaseDialog
    v-if="currentAnnouncement"
    v-model="dialog"
    :title="$t('announcements.announcements')"
    :icon="$globals.icons.bullhornVariant"
    :cancel-text="$t('general.done')"
    width="100%"
    max-width="1200"
  >
    <div class="flex min-h-[60vh] font-sans md:h-[60vh]">
      <!-- every announcement, newest first -->
      <nav
        v-show="!useMobile || navOpen"
        class="w-full shrink-0 overflow-y-auto border-e px-2 md:w-56"
        :aria-label="$t('announcements.all-announcements')"
      >
        <ul class="m-0 flex list-none flex-col gap-0.5 p-0">
          <li
            v-for="announcement in allAnnouncements.toReversed()"
            :key="announcement.key"
          >
            <button
              type="button"
              class="flex w-full items-start gap-2 rounded-item px-3 py-2 text-start transition-colors"
              :class="currentAnnouncement.key === announcement.key ? 'bg-highlight text-highlight-foreground' : 'hover:bg-highlight/60'"
              :aria-current="currentAnnouncement.key === announcement.key ? 'true' : undefined"
              @click="setCurrentAnnouncement(announcement); navOpen = false"
            >
              <span class="min-w-0 flex-1">
                <span class="block text-sm font-semibold">{{ announcement.meta?.title }}</span>
                <span
                  v-if="announcement.date"
                  class="block text-xs text-muted-foreground"
                >{{ $d(announcement.date) }}</span>
              </span>
              <span
                v-if="newAnnouncements.some(a => a.key === announcement.key)"
                class="mt-1.5 size-2 shrink-0 rounded-full bg-brand"
                :aria-label="$t('announcements.new')"
              />
            </button>
          </li>
        </ul>
      </nav>

      <div
        v-show="!useMobile || !navOpen"
        class="min-w-0 flex-1 overflow-y-auto px-6"
      >
        <button
          v-if="useMobile"
          type="button"
          class="mb-2 inline-flex items-center gap-1 text-sm font-semibold text-muted-foreground"
          @click="navOpen = !navOpen"
        >
          <ChevronLeftIcon class="size-4 rtl:rotate-180" />
          {{ $t("announcements.all-announcements") }}
        </button>
        <p
          v-if="currentAnnouncement.date"
          class="m-0 text-sm text-muted-foreground"
        >
          {{ $d(currentAnnouncement.date) }}
        </p>
        <h3 class="m-0 mb-4 text-xl font-bold tracking-tight">
          {{ currentAnnouncement.meta?.title }}
        </h3>
        <div class="text-[15px] leading-relaxed [&_a:not([class])]:text-primary [&_a:not([class])]:underline [&_hr]:my-4 [&_li]:mb-1 [&_p]:mb-3 [&_ul]:mb-3 [&_ul]:list-disc [&_ul]:ps-5">
          <component :is="currentAnnouncement.component" />
        </div>
      </div>
    </div>
    <template #custom-card-action>
      <Button
        v-if="newAnnouncements.length"
        variant="ghost"
        @click="markAllAsRead"
      >
        {{ $t('announcements.mark-all-as-read') }}
      </Button>
      <Button
        variant="outline"
        :disabled="isLastAnnouncement(currentAnnouncement.key)"
        @click="nextAnnouncement"
      >
        {{ $t('general.next') }}
        <ChevronRightIcon class="size-4 rtl:rotate-180" />
      </Button>
    </template>
  </BaseDialog>
</template>

<script setup lang="ts">
import { useMediaQuery } from "@vueuse/core";
import { ChevronLeftIcon, ChevronRightIcon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import { useAnnouncements } from "~/composables/use-announcements";
import type { Announcement } from "~/composables/use-announcements";

const dialog = defineModel<boolean>({ default: false });

const useMobile = useMediaQuery("(max-width: 959.98px)");
const navOpen = ref(false);

const route = useRoute();
watch(() => route.fullPath, () => { dialog.value = false; });

const { newAnnouncements, allAnnouncements, setLastRead, markAllAsRead } = useAnnouncements();

const currentAnnouncement = shallowRef<Announcement | undefined>();

watch(dialog, () => {
  if (!dialog.value || currentAnnouncement.value) {
    return;
  }

  // Show first unread on open, or fall back to the newest
  const next = newAnnouncements.value.at(0) || allAnnouncements.at(-1)!;
  setCurrentAnnouncement(next);
});

function setCurrentAnnouncement(announcement: Announcement) {
  currentAnnouncement.value = announcement;
  setLastRead(announcement.key);
}

function nextAnnouncement() {
  // Find the first unread announcement after the current one (current is already removed from newAnnouncements)
  const next = newAnnouncements.value.find(a => a.key > currentAnnouncement.value!.key);
  if (next) {
    setCurrentAnnouncement(next);
  }
}

function isLastAnnouncement(key: string) {
  if (!newAnnouncements.value.length) {
    return true;
  }
  else {
    return key >= newAnnouncements.value.at(-1)!.key;
  }
}
</script>
