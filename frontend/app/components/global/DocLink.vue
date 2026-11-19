<template>
  <Button
    as="a"
    size="xs"
    variant="outline"
    :href="href"
    target="_blank"
    rel="noopener noreferrer"
    class="h-7 gap-1.5 px-2.5 text-xs"
  >
    <MdiIcon
      :path="$globals.icons.folderOutline"
      class="size-3.5"
    />
    {{ $t("about.docs") }}
    <span class="sr-only">({{ $t("general.opens-in-new-tab") }})</span>
  </Button>
</template>

<script setup lang="ts">
import { Button } from "~/components/ui/button";
import { MdiIcon } from "~/components/ui/mdi-icon";

const props = defineProps({
  link: {
    type: String,
    required: true,
  },
});

const href = computed(() => {
  // TODO: dynamically set docs link based off env
  return `https://docs.mealie.io${props.link}`;
});
</script>
