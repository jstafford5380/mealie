<template>
  <div class="w-full">
    <TextField
      v-model="modelValue"
      :label="$t('general.color')"
      autocomplete="off"
      spellcheck="false"
      class="font-mono"
    >
      <template #append-inner>
        <Popover v-model:open="menu">
          <PopoverTrigger as-child>
            <button
              type="button"
              class="inline-flex size-8 items-center justify-center rounded-item text-muted-foreground hover:bg-highlight hover:text-highlight-foreground"
              :aria-label="$t('general.color')"
            >
              <MdiIcon
                :path="$globals.icons.formatColorFill"
                class="size-[18px]"
              />
            </button>
          </PopoverTrigger>
          <PopoverContent
            align="end"
            class="w-64 p-3"
          >
            <div class="flex flex-col gap-3">
              <label class="flex items-center gap-3 text-sm font-medium">
                <input
                  type="color"
                  class="h-10 w-14 cursor-pointer rounded-item border border-input bg-card p-1"
                  :value="hexValue"
                  @input="modelValue = ($event.target as HTMLInputElement).value"
                >
                {{ $t('general.color') }}
              </label>
              <div
                class="grid grid-cols-8 gap-1.5"
                role="listbox"
                :aria-label="$t('general.color')"
              >
                <button
                  v-for="swatch in SWATCHES"
                  :key="swatch"
                  type="button"
                  role="option"
                  :aria-selected="swatch.toLowerCase() === (modelValue || '').toLowerCase()"
                  :aria-label="swatch"
                  class="size-6 rounded-full border border-black/10 outline-offset-2 aria-selected:outline-2 aria-selected:outline-foreground"
                  :style="{ backgroundColor: swatch }"
                  @click="modelValue = swatch"
                />
              </div>
            </div>
          </PopoverContent>
        </Popover>
      </template>
    </TextField>
    <div class="-mt-1 mb-1 flex items-center gap-2">
      <button
        type="button"
        class="inline-flex h-8 items-center gap-2 rounded-item border border-input bg-card pe-2.5 ps-1 text-sm font-medium hover:bg-highlight"
        @click="setRandomHex"
      >
        <span
          class="size-6 rounded-[5px] border border-black/10"
          :style="{ backgroundColor: modelValue || 'transparent' }"
          aria-hidden="true"
        />
        <MdiIcon
          :path="$globals.icons.refreshCircle"
          class="size-4 text-muted-foreground"
        />
        {{ $t('general.random') }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import TextField from "~/components/ui/field/TextField.vue";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { Popover, PopoverContent, PopoverTrigger } from "~/components/ui/popover";

const modelValue = defineModel({
  type: String,
  required: true,
});

const menu = ref(false);

const SWATCHES = [
  "#B4412F", "#E07A66", "#E9A23B", "#C9821F", "#D9C39A", "#2E6A4F", "#5FAE87", "#4E9C76",
  "#2F69AD", "#8DB7E8", "#6B4FA0", "#B48ACB", "#A63D6B", "#E58325", "#5F6862", "#1E2420",
];

/** The native colour input only accepts #rrggbb. */
const hexValue = computed(() => (/^#[0-9a-f]{6}$/i.test(modelValue.value || "") ? modelValue.value : "#000000"));

function getRandomHex() {
  return "#000000".replace(/0/g, function () {
    return (~~(Math.random() * 16)).toString(16);
  });
}

function setRandomHex() {
  modelValue.value = getRandomHex();
}
</script>
