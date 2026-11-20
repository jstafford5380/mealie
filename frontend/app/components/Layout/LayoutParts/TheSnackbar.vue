<template>
  <Toaster
    position="top-center"
    :close-button="true"
    :close-button-aria-label="$t('general.close')"
    close-button-position="top-right"
    :visible-toasts="3"
    :toast-options="toastOptions"
  />
  <Transition
    enter-active-class="transition duration-200 ease-out motion-reduce:transition-none"
    enter-from-class="translate-y-4 opacity-0"
    leave-active-class="transition duration-150 ease-in motion-reduce:transition-none"
    leave-to-class="translate-y-4 opacity-0"
  >
    <div
      v-if="toastLoading.open"
      data-slot="loading-notice"
      role="status"
      aria-live="polite"
      class="fixed inset-x-0 bottom-4 z-[2500] mx-auto flex w-[min(28rem,calc(100%-2rem))] items-center gap-3 rounded-card border bg-popover px-4 py-3 font-sans text-popover-foreground shadow-lg"
    >
      <div class="flex min-w-0 flex-1 flex-col gap-2">
        <span class="text-sm font-medium">
          <template v-if="toastLoading.title">{{ toastLoading.title }} </template>{{ toastLoading.text }}
        </span>
        <div
          class="relative h-1.5 w-full overflow-hidden rounded-full bg-primary/20"
          aria-hidden="true"
        >
          <div class="loading-notice-bar absolute inset-y-0 w-1/3 rounded-full bg-primary motion-reduce:w-full motion-reduce:animate-none" />
        </div>
      </div>
      <button
        type="button"
        class="inline-flex size-9 shrink-0 items-center justify-center rounded-item text-muted-foreground hover:bg-highlight hover:text-highlight-foreground focus-visible:outline-2"
        :aria-label="$t('general.close')"
        @click="toastLoading.open = false"
      >
        <XIcon class="size-4" />
      </button>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { XIcon } from "@lucide/vue";
import { toast } from "vue-sonner";
import { Toaster } from "~/components/ui/sonner";
import { toastAlert, toastLoading } from "~/composables/use-toast";

const i18n = useI18n();
const DEFAULT_TIMEOUT = 2000;

const toastOptions = {
  classes: {
    toast: "font-sans !rounded-card !gap-3 !text-[15px] !pe-12",
    closeButton: "!inset-s-auto !inset-e-2 !top-1/2 !size-8 !-translate-y-1/2 !transform-none !rounded-item !border-0 !bg-transparent !text-popover-foreground hover:!bg-highlight focus-visible:!outline-2",
    description: "!text-muted-foreground",
    actionButton: "!bg-primary !text-primary-foreground !font-semibold !rounded-item",
    error: "[&_[data-icon]]:text-destructive",
    success: "[&_[data-icon]]:text-primary",
    warning: "[&_[data-icon]]:text-brand-strong",
    info: "[&_[data-icon]]:text-muted-foreground",
  },
};
let activeId: string | number | undefined;

function show() {
  if (activeId !== undefined) {
    toast.dismiss(activeId);
  }
  const message = toastAlert.title || toastAlert.text;
  const description = toastAlert.title ? toastAlert.text : undefined;
  const action = toastAlert.action;
  const options = {
    description,
    duration: toastAlert.timeout ?? DEFAULT_TIMEOUT,
    action: action
      ? {
          label: action.message ?? i18n.t("general.close"),
          onClick: () => {
            action.onClick();
            toastAlert.open = false;
          },
        }
      : undefined,
    onDismiss: () => {
      toastAlert.open = false;
    },
    onAutoClose: () => {
      toastAlert.open = false;
    },
  };
  switch (toastAlert.color) {
    case "error":
      activeId = toast.error(message, options);
      break;
    case "success":
      activeId = toast.success(message, options);
      break;
    case "warning":
      activeId = toast.warning(message, options);
      break;
    default:
      activeId = toast.info(message, options);
  }
}

watch(
  () => [toastAlert.open, toastAlert.seq] as const,
  ([open]) => {
    if (open) {
      show();
    }
    else if (activeId !== undefined) {
      toast.dismiss(activeId);
      activeId = undefined;
    }
  },
);
</script>

<style scoped>
.loading-notice-bar {
  animation: loading-notice 1.4s ease-in-out infinite;
}

@keyframes loading-notice {
  0% {
    left: -33%;
  }
  100% {
    left: 100%;
  }
}
</style>
