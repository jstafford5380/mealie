<template>
  <Transition
    enter-active-class="transition-opacity duration-150 motion-reduce:transition-none"
    enter-from-class="opacity-0"
    leave-active-class="transition-opacity duration-150 motion-reduce:transition-none"
    leave-to-class="opacity-0"
  >
    <button
      v-if="showButton"
      type="button"
      class="fixed bottom-6 end-5 z-[900] inline-flex size-11 items-center justify-center rounded-full border bg-card text-foreground shadow-lg transition-colors hover:bg-highlight max-md:bottom-[calc(84px+env(safe-area-inset-bottom))] print:hidden"
      :aria-label="$t('general.scroll-to-top')"
      @click="scrollToTop"
    >
      <ArrowUpIcon class="size-5" />
    </button>
  </Transition>
</template>

<script setup lang="ts">
import { ArrowUpIcon } from "@lucide/vue";

const showButton = ref(false);
const threshold = 400;

function onScroll() {
  showButton.value = document.documentElement.scrollTop > threshold;
}

function scrollToTop() {
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  window.scrollTo({ top: 0, behavior: reduce ? "auto" : "smooth" });
}

onMounted(() => {
  window.addEventListener("scroll", onScroll, { passive: true });
});

onUnmounted(() => {
  window.removeEventListener("scroll", onScroll);
});
</script>
