<template>
  <div
    data-slot="app-toolbar"
    class="flex min-h-14 flex-wrap items-center gap-2 py-2"
  >
    <BaseButton
      color="null"
      secondary
      @click="$router.go(-1)"
    >
      <template #icon>
        {{ $globals.icons.arrowLeftBold }}
      </template>
      {{ $t('general.back') }}
    </BaseButton>
    <slot />
  </div>
</template>

<script setup lang="ts">
defineProps({
  back: {
    type: Boolean,
    default: false,
  },
});
</script>
