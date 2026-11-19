<template>
  <Button
    :as="tag"
    :to="to || undefined"
    :type="tag === 'button' ? (($attrs.type as string) || 'button') : undefined"
    :variant="variant"
    :size="buttonSize"
    :disabled="tag === 'button' ? (disabled || loading) : undefined"
    :aria-disabled="tag !== 'button' && (disabled || loading) ? 'true' : undefined"
    :aria-busy="loading ? 'true' : undefined"
    :class="cn(
      block && 'w-full',
      tag !== 'button' && (disabled || loading) && 'pointer-events-none opacity-50',
      colorClass,
    )"
    v-bind="passthroughAttrs"
    @click="download ? downloadFile() : undefined"
  >
    <Spinner
      v-if="loading"
      class="size-4"
      :label="$t('general.loading')"
    />
    <MdiIcon
      v-else-if="!iconRight && iconPath"
      :path="iconPath"
      class="size-[18px]"
    />
    <slot name="default">
      {{ text || btnAttrs.text }}
    </slot>
    <MdiIcon
      v-if="iconRight && iconPath && !loading"
      :path="iconPath"
      class="size-[18px]"
    />
  </Button>
</template>

<script setup lang="ts">
import type { ButtonVariants } from "~/components/ui/button";
import { Button } from "~/components/ui/button";
import { MdiIcon, slotText } from "~/components/ui/mdi-icon";
import { Spinner } from "~/components/ui/spinner";
import { useUserApi } from "~/composables/api";
import { cn } from "~/lib/utils";

defineOptions({ inheritAttrs: false });

const props = defineProps({
  cancel: {
    type: Boolean,
    default: false,
  },
  create: {
    type: Boolean,
    default: false,
  },
  update: {
    type: Boolean,
    default: false,
  },
  edit: {
    type: Boolean,
    default: false,
  },
  save: {
    type: Boolean,
    default: false,
  },
  delete: {
    type: Boolean,
    default: false },
  download: {
    type: Boolean,
    default: false,
  },
  downloadUrl: {
    type: String,
    default: "",
  },
  loading: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  small: {
    type: Boolean,
    default: false,
  },
  xSmall: {
    type: Boolean,
    default: false,
  },
  secondary: {
    type: Boolean,
    default: false,
  },
  minor: {
    type: Boolean,
    default: false,
  },
  to: {
    type: String,
    default: null,
  },
  color: {
    type: String,
    default: null,
  },
  text: {
    type: String,
    default: null,
  },
  icon: {
    type: String,
    default: null,
  },
  iconRight: {
    type: Boolean,
    default: false,
  },
  /** Vuetify-compatible attributes still used by callers. */
  block: {
    type: Boolean,
    default: false,
  },
  size: {
    type: String,
    default: null,
  },
});

const attrs = useAttrs();
const slots = useSlots();
const i18n = useI18n();
const { $globals } = useNuxtApp();

const buttonOptions = {
  create: {
    text: i18n.t("general.create"),
    icon: $globals.icons.createAlt,
    color: "success",
  },
  update: {
    text: i18n.t("general.update"),
    icon: $globals.icons.edit,
    color: "success",
  },
  save: {
    text: i18n.t("general.save"),
    icon: $globals.icons.save,
    color: "success",
  },
  edit: {
    text: i18n.t("general.edit"),
    icon: $globals.icons.edit,
    color: "info",
  },
  delete: {
    text: i18n.t("general.delete"),
    icon: $globals.icons.delete,
    color: "error",
  },
  cancel: {
    text: i18n.t("general.cancel"),
    icon: $globals.icons.close,
    color: "grey",
  },
  download: {
    text: i18n.t("general.download"),
    icon: $globals.icons.download,
    color: "info",
  },
};

const btnAttrs = computed(() => {
  if (props.delete) {
    return buttonOptions.delete;
  }
  if (props.update) {
    return buttonOptions.update;
  }
  if (props.edit) {
    return buttonOptions.edit;
  }
  if (props.cancel) {
    return buttonOptions.cancel;
  }
  if (props.save) {
    return buttonOptions.save;
  }
  if (props.download) {
    return buttonOptions.download;
  }
  return buttonOptions.create;
});

const iconPath = computed(() => slotText(slots.icon) || props.icon || btnAttrs.value.icon);

const tag = computed(() => {
  if (props.to) {
    return resolveComponent("NuxtLink");
  }
  if (attrs.href) {
    return "a";
  }
  return "button";
});

/**
 * Maps the legacy Vuetify colour names to the new button hierarchy:
 * success/primary (and any submit button) are the main action, info is a neutral outlined action,
 * error is destructive, warning is outlined with warning text, grey is quiet.
 */
type Variant = NonNullable<ButtonVariants["variant"]>;
const colorName = computed(() => (props.color || btnAttrs.value.color || "success").toLowerCase());

const variant = computed<Variant>(() => {
  if (props.minor || props.cancel) {
    return "ghost";
  }
  const name = colorName.value;
  const destructive = name === "error" || name === "red";
  if (props.secondary) {
    return "outline";
  }
  if (destructive) {
    return "destructive";
  }
  if (name === "success" || name === "primary" || attrs.type === "submit") {
    return "default";
  }
  return "outline";
});

const colorClass = computed(() => {
  const name = colorName.value;
  if (variant.value === "outline" && (name === "error" || name === "red")) {
    return "text-destructive";
  }
  if (variant.value === "outline" && name === "warning") {
    return "text-brand-strong";
  }
  if (variant.value === "ghost" && (name === "error" || name === "red")) {
    return "text-destructive";
  }
  return undefined;
});

const buttonSize = computed<ButtonVariants["size"]>(() => {
  if (props.xSmall || props.size === "x-small") {
    return "xs";
  }
  if (props.small || props.size === "small") {
    return "sm";
  }
  if (props.size === "large" || props.size === "x-large") {
    return "lg";
  }
  return "default";
});

// Vuetify-only attributes have no meaning here; everything else (listeners, class, style, aria) passes through.
const VUETIFY_ONLY = new Set(["rounded", "flat", "variant", "elevation", "density", "type"]);
const passthroughAttrs = computed(() => Object.fromEntries(
  Object.entries(attrs).filter(([key]) => !VUETIFY_ONLY.has(key)),
));

const api = useUserApi();
function downloadFile() {
  api.utils.download(props.downloadUrl);
}
</script>
