<template>
  <div
    v-if="wakeIsSupported"
    class="flex justify-center px-2 py-2 font-sans md:justify-end print:hidden"
  >
    <label class="inline-flex cursor-pointer items-center gap-3 text-[15px] font-medium">
      <Switch v-model="wakeLock" />
      {{ $t('recipe.screen-awake') }}
    </label>
  </div>
</template>

<script setup lang="ts">
import { useWakeLock } from "@vueuse/core";
import { Switch } from "~/components/ui/switch";
import { useUserExperiencePreferences } from "~/composables/use-users/preferences";

const { isSupported: wakeIsSupported, isActive, request, release } = useWakeLock();
const userExperiencePreferences = useUserExperiencePreferences();

function handleLock() {
  if (userExperiencePreferences.value.lockScreen) {
    lockScreen();
  }
  else {
    unlockScreen();
  }
}

const wakeLock = computed({
  get: () => userExperiencePreferences.value.lockScreen,
  set: () => {
    userExperiencePreferences.value.lockScreen = !userExperiencePreferences.value.lockScreen;
    handleLock();
  },
});

// Browsers may refuse a wake lock (no user gesture yet, battery saver, embedded views).
// The preference is kept, and the lock is requested again on the next toggle or visit.
async function lockScreen() {
  if (wakeIsSupported) {
    console.debug("Wake Lock Requested");
    try {
      await request("screen");
    }
    catch (error) {
      console.debug("Wake Lock refused", error);
    }
  }
}
async function unlockScreen() {
  if (wakeIsSupported || isActive.value) {
    console.debug("Wake Lock Released");
    try {
      await release();
    }
    catch (error) {
      console.debug("Wake Lock release failed", error);
    }
  }
}
onMounted(() => handleLock());
onUnmounted(() => unlockScreen());
</script>
