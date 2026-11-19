<template>
  <TooltipProvider>
    <!-- Controlled: shows the copy result after a click, not on hover. -->
    <Tooltip :open="show">
      <TooltipTrigger as-child>
        <Button
          :variant="buttonVariant"
          :size="icon ? 'icon' : 'default'"
          :class="btnClass"
          :disabled="copyText === ''"
          :aria-label="icon ? $t('general.copy') : undefined"
          @click="textToClipboard()"
        >
          <MdiIcon
            :path="$globals.icons.contentCopy"
            class="size-[18px]"
          />
          {{ icon ? "" : $t("general.copy") }}
        </Button>
      </TooltipTrigger>
      <TooltipContent
        side="top"
        class="flex items-center gap-1.5"
      >
        <MdiIcon
          :path="$globals.icons.clipboardCheck"
          class="size-4"
        />
        <span role="status">
          <slot v-if="!isSupported"> {{ $t("general.your-browser-does-not-support-clipboard") }} </slot>
          <slot v-else> {{ copiedSuccess ? $t("general.copied_message") : $t("general.clipboard-copy-failure") }} </slot>
        </span>
      </TooltipContent>
    </Tooltip>
  </TooltipProvider>
</template>

<script setup lang="ts">
import { useClipboard } from "@vueuse/core";
import { Button } from "~/components/ui/button";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "~/components/ui/tooltip";

const props = defineProps({
  copyText: {
    type: String,
    required: true,
  },
  color: {
    type: String,
    default: "",
  },
  icon: {
    type: Boolean,
    default: true,
  },
  btnClass: {
    type: String,
    default: "",
  },
});

const buttonVariant = computed(() => (props.color === "primary" || props.color === "success" ? "default" : props.icon ? "ghost" : "outline"));

const { copy, copied, isSupported } = useClipboard({ legacy: true });
const show = ref(false);
const copiedSuccess = ref<boolean | null>(null);

async function textToClipboard() {
  if (isSupported.value) {
    await copy(props.copyText);
    if (copied.value) {
      copiedSuccess.value = true;
      console.info(`Copied\n${props.copyText}`);
    }
    else {
      copiedSuccess.value = false;
      console.error("Copy failed: ", copied.value);
    }
  }
  else {
    console.warn("Clipboard is currently not supported by your browser. Ensure you're on a secure (https) site.");
  }

  show.value = true;
  setTimeout(() => {
    show.value = false;
  }, 3000);
}
</script>
