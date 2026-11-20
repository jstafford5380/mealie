<template>
  <div
    data-slot="base-dialog-content"
    class="relative flex min-h-0 flex-auto flex-col font-sans text-popover-foreground"
  >
    <div
      v-if="loading"
      class="absolute inset-x-0 top-0 z-10 h-1 overflow-hidden bg-primary/15"
      role="progressbar"
      :aria-label="$t('general.loading')"
    >
      <div class="dialog-loading-bar absolute inset-y-0 w-1/3 bg-primary motion-reduce:w-full motion-reduce:animate-none" />
    </div>

    <header class="flex items-center gap-3 border-b px-5 py-4 pe-14">
      <span
        v-if="icon"
        class="flex size-9 shrink-0 items-center justify-center rounded-control"
        :class="tone.icon"
      >
        <MdiIcon
          :path="icon"
          class="size-5"
        />
      </span>
      <component
        :is="titleComponent"
        class="m-0 min-w-0 flex-1 text-lg font-semibold leading-tight tracking-tight"
      >
        {{ title }}
      </component>
    </header>

    <div class="min-h-0 flex-1 overflow-auto">
      <slot />
    </div>

    <footer
      class="flex items-center gap-2 border-t px-5 py-3"
      :class="isXs ? 'grid auto-cols-fr grid-flow-col pb-4' : ''"
    >
      <slot name="card-actions">
        <Button
          variant="ghost"
          type="button"
          @click="emit('cancel')"
        >
          {{ cancelLabel }}
        </Button>
        <span
          v-if="!isXs"
          class="flex-1"
        />
        <slot name="custom-card-action" />
        <BaseButton
          v-if="canDelete"
          delete
          @click="emit('delete')"
        />
        <BaseButton
          v-if="canConfirm"
          :color="color === 'primary' ? 'success' : color"
          type="submit"
          :disabled="submitDisabled"
          @click="emit('confirm')"
        >
          <template #icon>
            {{ $globals.icons.check }}
          </template>
          {{ $t("general.confirm") }}
        </BaseButton>
        <BaseButton
          v-if="canSubmit"
          type="submit"
          :disabled="submitDisabled || loading"
          @click="emit('submit')"
        >
          {{ submitLabel }}
          <template
            v-if="submitIcon"
            #icon
          >
            {{ submitIcon }}
          </template>
        </BaseButton>
      </slot>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { useMediaQuery } from "@vueuse/core";
import { DialogTitle } from "reka-ui";
import { Button } from "~/components/ui/button";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { useGlobalI18n } from "~/composables/use-global-i18n";

interface DialogProps {
  color?: string;
  title?: string;
  icon?: string | null;
  loading?: boolean;

  // submit
  submitIcon?: string | null;
  submitText?: string;
  submitDisabled?: boolean;

  // cancel
  cancelText?: string;

  // actions
  canDelete?: boolean;
  canConfirm?: boolean;
  canSubmit?: boolean;

  /** Set by BaseDialog so the title is announced as the dialog's name. */
  inDialog?: boolean;
}

interface DialogEmits {
  (e: "submit" | "cancel" | "confirm" | "delete"): void;
}

const props = withDefaults(defineProps<DialogProps>(), {
  color: "primary",
  title: "Modal Title",
  icon: null,
  loading: false,

  // submit
  submitIcon: null,
  submitDisabled: false,

  // actions
  canDelete: false,
  canConfirm: false,
  canSubmit: false,
  inDialog: false,
});
const emit = defineEmits<DialogEmits>();

const i18n = useGlobalI18n();
const isXs = useMediaQuery("(max-width: 599.98px)");

const titleComponent = computed(() => (props.inDialog ? DialogTitle : "h2"));
const submitLabel = computed(() => props.submitText ?? i18n.t("general.create"));
const cancelLabel = computed(() => props.cancelText ?? i18n.t("general.cancel"));

/** Legacy colour names tint the header icon; destructive dialogs read as such. */
const tone = computed(() => {
  switch (props.color) {
    case "error":
    case "red":
      return { icon: "bg-destructive/12 text-destructive" };
    case "warning":
      return { icon: "bg-brand-soft text-brand-strong" };
    default:
      return { icon: "bg-highlight text-highlight-foreground" };
  }
});
</script>

<style scoped>
.dialog-loading-bar {
  animation: dialog-loading 1.4s ease-in-out infinite;
}

@keyframes dialog-loading {
  0% {
    left: -33%;
  }
  100% {
    left: 100%;
  }
}
</style>
