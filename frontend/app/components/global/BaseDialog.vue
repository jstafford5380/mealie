<template>
  <div>
    <slot
      name="activator"
      v-bind="{ open }"
    />
    <DialogRoot
      v-model:open="dialog"
      :modal="true"
    >
      <DialogPortal>
        <Transition
          enter-active-class="transition-opacity duration-150 motion-reduce:transition-none"
          enter-from-class="opacity-0"
          leave-active-class="transition-opacity duration-100 motion-reduce:transition-none"
          leave-to-class="opacity-0"
        >
          <DialogOverlay
            v-if="dialog"
            force-mount
            class="fixed inset-0 z-[2050] bg-black/45"
          />
        </Transition>
        <Transition
          :enter-active-class="asSheet ? 'transition-transform duration-200 ease-out motion-reduce:transition-none' : 'transition duration-150 ease-out motion-reduce:transition-none'"
          :enter-from-class="asSheet ? 'translate-y-full' : 'opacity-0 scale-[0.98]'"
          :leave-active-class="asSheet ? 'transition-transform duration-150 ease-in motion-reduce:transition-none' : 'transition duration-100 ease-in motion-reduce:transition-none'"
          :leave-to-class="asSheet ? 'translate-y-full' : 'opacity-0 scale-[0.98]'"
        >
          <DialogContent
            v-if="dialog"
            ref="contentRef"
            force-mount
            :trap-focus="false"
            :aria-describedby="undefined"
            :class="contentClass"
            :style="contentStyle"
            @keydown.enter="onEnter"
            @escape-key-down="onEscape"
            @pointer-down-outside="onPointerDownOutside"
            @focus-outside="keepOpenForVuetifyOverlay"
            @interact-outside="keepOpenForVuetifyOverlay"
          >
            <BaseDialogContent
              v-bind="bindings"
              in-dialog
            >
              <template #default>
                <slot v-bind="{ submitEvent }" />
              </template>
              <template
                v-if="$slots['card-actions']"
                #card-actions
              >
                <slot name="card-actions" />
              </template>
              <template #custom-card-action>
                <slot name="custom-card-action" />
              </template>
            </BaseDialogContent>
            <DialogClose
              class="absolute end-3 top-3.5 inline-flex size-9 items-center justify-center rounded-item text-muted-foreground transition-colors hover:bg-highlight hover:text-highlight-foreground focus-visible:outline-2 focus-visible:outline-offset-2"
              :aria-label="$t('general.close')"
              @click="emit('cancel')"
            >
              <XIcon class="size-5" />
            </DialogClose>
          </DialogContent>
        </Transition>
      </DialogPortal>
    </DialogRoot>
  </div>
</template>

<script setup lang="ts">
import { XIcon } from "@lucide/vue";
import { useEventListener, useMediaQuery } from "@vueuse/core";
import { DialogClose, DialogContent, DialogOverlay, DialogPortal, DialogRoot } from "reka-ui";
import {
  escapeClosesVuetifyOverlayFirst,
  isInsideVuetifyOverlay,
  keepOpenForVuetifyOverlay,
} from "~/lib/vuetify-coexistence";
import { useGlobalI18n } from "~/composables/use-global-i18n";
import { cn } from "~/lib/utils";

const i18n = useGlobalI18n();

interface DialogProps {
  modelValue: boolean;
  color?: string;
  title?: string;
  icon?: string | null;
  width?: number | string;
  maxWidth?: number | string | null;
  loading?: boolean;
  top?: boolean | null;
  keepOpen?: boolean;
  bottomSheet?: boolean;

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
  disableSubmitOnEnter?: boolean;
}

interface DialogEmits {
  (e: "update:modelValue", value: boolean): void;
  (e: "submit" | "cancel" | "confirm" | "delete" | "close"): void;
}

const props = withDefaults(defineProps<DialogProps>(), {
  color: "primary",
  title: "Modal Title",
  icon: null,
  width: "500",
  maxWidth: null,
  loading: false,
  top: null,
  keepOpen: false,
  bottomSheet: false,

  // submit
  submitIcon: null,
  submitDisabled: false,

  // actions
  canDelete: false,
  canConfirm: false,
  canSubmit: false,
  disableSubmitOnEnter: false,
});
const emit = defineEmits<DialogEmits>();

const dialog = computed({
  get: () => props.modelValue,
  set: val => emit("update:modelValue", val),
});

const isXs = useMediaQuery("(max-width: 599.98px)");
/** Extra-small screens: a bottom sheet when requested, otherwise fullscreen (as before). */
const asSheet = computed(() => props.bottomSheet && isXs.value);
const fullscreen = computed(() => !props.bottomSheet && isXs.value);

function toCssSize(value: number | string | null | undefined): string | undefined {
  if (value === null || value === undefined || value === "") {
    return undefined;
  }
  return /^\d+(\.\d+)?$/.test(String(value)) ? `${value}px` : String(value);
}

const contentClass = computed(() => cn(
  "fixed z-[2051] flex flex-col overflow-hidden border bg-popover shadow-2xl outline-none",
  asSheet.value && "inset-x-0 bottom-0 max-h-[92dvh] rounded-t-[20px] border-b-0",
  fullscreen.value && "inset-0 rounded-none border-0",
  !asSheet.value && !fullscreen.value && "left-1/2 max-h-[min(90dvh,900px)] -translate-x-1/2 rounded-panel",
  !asSheet.value && !fullscreen.value && (props.top ? "top-6" : "top-1/2 -translate-y-1/2"),
));

const contentStyle = computed(() => {
  if (asSheet.value || fullscreen.value) {
    return props.maxWidth && asSheet.value ? { maxWidth: toCssSize(props.maxWidth), marginInline: "auto" } : undefined;
  }
  const width = toCssSize(props.width) ?? "500px";
  const maxWidth = toCssSize(props.maxWidth);
  return {
    width: `min(${width}, calc(100vw - 2rem))`,
    maxWidth: maxWidth ? `min(${maxWidth}, calc(100vw - 2rem))` : undefined,
  };
});

const submitted = ref(false);

const determineClose = computed(() => {
  return submitted.value && !props.loading && !props.keepOpen;
});

watch(determineClose, (shouldClose) => {
  if (shouldClose) {
    submitted.value = false;
    dialog.value = false;
  }
});

watch(dialog, (val) => {
  if (val) submitted.value = false;
  if (!val) emit("close");
});

function submitEvent() {
  emit("submit");
  submitted.value = true;
}

function submitOnEnter() {
  if (props.disableSubmitOnEnter) {
    return;
  }

  if (props.canConfirm) {
    if (!props.submitDisabled) {
      emit("confirm");
      dialog.value = false;
    }
    return;
  }

  submitEvent();
}

/**
 * Enter submits the dialog, as before, except where Enter already means something:
 * new lines in a textarea or rich-text field, activating a focused button or link, and
 * choosing an item in an open select/autocomplete (those mark the event as handled).
 */
function onEnter(event: KeyboardEvent) {
  const target = event.target as HTMLElement | null;
  if (event.defaultPrevented || event.isComposing || !target) {
    return;
  }
  if (target.closest("textarea, [contenteditable=''], [contenteditable='true'], button, a[href]")) {
    return;
  }
  submitOnEnter();
}

function onEscape(event: KeyboardEvent) {
  escapeClosesVuetifyOverlayFirst(event);
  if (!event.defaultPrevented) {
    emit("cancel");
  }
}

function onPointerDownOutside(event: Parameters<typeof keepOpenForVuetifyOverlay>[0]) {
  keepOpenForVuetifyOverlay(event);
  if (!event.defaultPrevented) {
    emit("cancel");
  }
}

function deleteEvent() {
  emit("delete");
  submitted.value = true;
}

function open() {
  dialog.value = true;
}

/**
 * Focus containment that tolerates Vuetify menus. Reka's own trap would pull focus out of
 * Vuetify's select and autocomplete lists, which render outside the dialog.
 */
const contentRef = ref<{ $el: HTMLElement } | null>(null);
useEventListener(document, "focusin", (event: FocusEvent) => {
  const content = contentRef.value?.$el;
  const target = event.target as Node | null;
  if (!dialog.value || !content || !target || content.contains(target) || isInsideVuetifyOverlay(target)) {
    return;
  }
  // Another (nested) Reka dialog or popover owns focus.
  if (target instanceof Element && target.closest("[role=dialog], [data-reka-popper-content-wrapper]")) {
    return;
  }
  const first = content.querySelector<HTMLElement>(
    "input:not([disabled]):not([type=hidden]), select:not([disabled]), textarea:not([disabled]), button:not([disabled]), [href], [tabindex]:not([tabindex='-1'])",
  );
  (first ?? content).focus();
});

const bindings = computed(() => ({
  color: props.color,
  title: props.title,
  icon: props.icon,
  loading: props.loading,
  submitIcon: props.submitIcon,
  submitText: props.submitText ?? i18n.t("general.create"),
  submitDisabled: props.submitDisabled,
  cancelText: props.cancelText ?? i18n.t("general.cancel"),
  canDelete: props.canDelete,
  canConfirm: props.canConfirm,
  canSubmit: props.canSubmit,
  onCancel: () => {
    emit("cancel");
    dialog.value = false;
  },
  onConfirm: () => {
    emit("confirm");
    dialog.value = false;
  },
  onSubmit: submitEvent,
  onDelete: deleteEvent,
}));
</script>
