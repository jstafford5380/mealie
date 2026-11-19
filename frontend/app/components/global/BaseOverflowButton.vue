<template>
  <DropdownMenu :modal="false">
    <DropdownMenuTrigger as-child>
      <Button
        v-bind="buttonAttrs"
        :variant="variant"
        :class="btnClass"
        :disabled="disabled"
      >
        <MdiIcon
          v-if="activeObj.icon"
          :path="activeObj.icon"
          class="size-[18px]"
        />
        {{ mode === MODES.model ? activeObj.text : btnText }}
        <ChevronDownIcon class="size-4 opacity-80" />
      </Button>
    </DropdownMenuTrigger>
    <DropdownMenuContent
      align="start"
      class="max-h-[80vh] min-w-48 overflow-y-auto"
    >
      <template
        v-for="(item, index) in visibleItems"
        :key="index"
      >
        <!-- Model -->
        <DropdownMenuItem
          v-if="mode === MODES.model"
          :class="item.value === modelValue && 'bg-highlight/60 font-semibold text-highlight-foreground'"
          :aria-current="item.value === modelValue ? 'true' : undefined"
          @select="setValue(item)"
        >
          <MdiIcon
            v-if="item.icon"
            :path="item.icon"
            class="size-[18px]"
          />
          {{ item.text }}
        </DropdownMenuItem>
        <!-- Links -->
        <DropdownMenuItem
          v-else-if="mode === MODES.link"
          as-child
        >
          <NuxtLink
            :to="item.to"
            active-class="bg-highlight/60 font-semibold text-highlight-foreground"
          >
            <MdiIcon
              v-if="item.icon"
              :path="item.icon"
              class="size-[18px]"
            />
            {{ item.text }}
          </NuxtLink>
        </DropdownMenuItem>
        <!-- Event -->
        <DropdownMenuItem
          v-else-if="mode === MODES.event"
          @select="$emit(item.event!)"
        >
          <MdiIcon
            v-if="item.icon"
            :path="item.icon"
            class="size-[18px]"
          />
          {{ item.text }}
        </DropdownMenuItem>
        <DropdownMenuSeparator v-if="item.divider" />
      </template>
    </DropdownMenuContent>
  </DropdownMenu>
</template>

<script setup lang="ts">
import { ChevronDownIcon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "~/components/ui/dropdown-menu";
import { MdiIcon } from "~/components/ui/mdi-icon";

defineOptions({ inheritAttrs: false });

const MODES = {
  model: "model",
  link: "link",
  event: "event",
};

type modes = "model" | "link" | "event";

export interface MenuItem {
  text: string;
  icon?: string;
  to?: string;
  value?: string;
  event?: string;
  divider?: boolean;
  hide?: boolean;
}

const props = defineProps({
  mode: {
    type: String as () => modes,
    default: "model",
  },
  items: {
    type: Array as () => MenuItem[],
    required: true,
  },
  disabled: {
    type: Boolean,
    required: false,
    default: false,
  },
  btnClass: {
    type: String,
    required: false,
    default: "",
  },
  btnText: {
    type: String,
    required: false,
    default: function () {
      return useI18n().t("general.actions");
    },
  },
});

const modelValue = defineModel({
  type: String,
  required: false,
  default: "",
});

const attrs = useAttrs();
// `color` is the legacy Vuetify colour; it picks the button style and is not passed on.
const buttonAttrs = computed(() => Object.fromEntries(Object.entries(attrs).filter(([key]) => key !== "color")));
const variant = computed(() => {
  const color = String(attrs.color ?? "primary");
  if (color === "error" || color === "red") {
    return "destructive";
  }
  return color === "primary" || color === "success" ? "default" : "outline";
});

const visibleItems = computed(() => props.items.filter(item => !item.hide));

const activeObj = computed<MenuItem>(() =>
  props.items.find(item => item.value === modelValue.value) ?? {
    text: "DEFAULT",
    value: "",
  },
);

function setValue(v: MenuItem) {
  modelValue.value = v.value || "";
}
</script>
