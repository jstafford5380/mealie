<template>
  <div>
    <Button
      :as="NuxtLink"
      :to="to"
      variant="outline"
      class="m-1 rounded-full"
    >
      <MdiIcon
        v-if="icon != ''"
        :path="icon"
        class="size-[18px]"
      />
      {{ text }}
    </Button>
  </div>
</template>

<script setup lang="ts">
import { Button } from "~/components/ui/button";
import { MdiIcon } from "~/components/ui/mdi-icon";

const NuxtLink = resolveComponent("NuxtLink");

defineProps({
  to: {
    type: String,
    required: true,
  },
  text: {
    type: String,
    required: true,
  },
  icon: {
    type: String,
    default: "",
  },
});
</script>
