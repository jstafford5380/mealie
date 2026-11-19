<template>
  <div class="flex flex-col gap-2 font-sans">
    <div
      v-for="(value, key) in (modelValue ?? {})"
      :key="key"
      class="flex items-center gap-2"
    >
      <input
        :value="key"
        readonly
        :aria-label="resolvedKeyLabel"
        class="h-10 min-w-0 flex-1 rounded-control border border-input bg-card px-3 text-[15px] outline-none focus:border-ring focus:ring-3 focus:ring-ring/25 bg-muted"
      >
      <input
        :value="value"
        :aria-label="resolvedValueLabel"
        class="h-10 min-w-0 flex-1 rounded-control border border-input bg-card px-3 text-[15px] outline-none focus:border-ring focus:ring-3 focus:ring-ring/25"
        @input="updateValue(key, ($event.target as HTMLInputElement).value)"
      >
      <button
        type="button"
        class="inline-flex size-9 shrink-0 items-center justify-center rounded-full text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
        :aria-label="$t('general.delete')"
        @click="removeEntry(key)"
      >
        <Trash2Icon class="size-4" />
      </button>
    </div>

    <div
      class="flex items-center gap-2"
      @focusout="onNewEntryFocusOut"
    >
      <input
        v-model="newKey"
        :placeholder="resolvedKeyLabel"
        :aria-label="resolvedKeyLabel"
        class="h-10 min-w-0 flex-1 rounded-control border border-input bg-card px-3 text-[15px] outline-none focus:border-ring focus:ring-3 focus:ring-ring/25"
        @keydown.enter.prevent="addEntry"
      >
      <input
        v-model="newValue"
        :placeholder="resolvedValueLabel"
        :aria-label="resolvedValueLabel"
        class="h-10 min-w-0 flex-1 rounded-control border border-input bg-card px-3 text-[15px] outline-none focus:border-ring focus:ring-3 focus:ring-ring/25"
        @keydown.enter.prevent="addEntry"
      >
      <button
        type="button"
        class="inline-flex size-9 shrink-0 items-center justify-center rounded-full text-primary hover:bg-highlight disabled:opacity-40"
        :aria-label="$t('general.add')"
        :disabled="!newKey?.trim()"
        @click="addEntry"
      >
        <PlusIcon class="size-4" />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { PlusIcon, Trash2Icon } from "@lucide/vue";
import { useGlobalI18n } from "~/composables/use-global-i18n";

const i18n = useGlobalI18n();

const props = defineProps<{
  modelValue?: Record<string, string> | null;
  keyLabel?: string;
  valueLabel?: string;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", value: Record<string, string>): void;
}>();

const resolvedKeyLabel = computed(() => props.keyLabel ?? i18n.t("general.key"));
const resolvedValueLabel = computed(() => props.valueLabel ?? i18n.t("general.value"));

const newKey = ref("");
const newValue = ref("");

function current(): Record<string, string> {
  return { ...(props.modelValue ?? {}) };
}

function addEntry() {
  const key = newKey.value?.trim();
  if (!key) return;
  const updated = current();
  updated[key] = newValue.value;
  emit("update:modelValue", updated);
  newKey.value = "";
  newValue.value = "";
}

function onNewEntryFocusOut(e: FocusEvent) {
  const relatedTarget = e.relatedTarget as HTMLElement | null;
  const currentTarget = e.currentTarget as HTMLElement;
  if (!relatedTarget || !currentTarget.contains(relatedTarget)) {
    addEntry();
  }
}

function updateValue(key: string, value: string) {
  const updated = current();
  updated[key] = value;
  emit("update:modelValue", updated);
}

function removeEntry(key: string) {
  const updated = current();
  // eslint-disable-next-line @typescript-eslint/no-dynamic-delete
  delete updated[key];
  emit("update:modelValue", updated);
}
</script>
