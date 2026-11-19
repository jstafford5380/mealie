<template>
  <div>
    <slot
      name="activator"
      :open="open"
    >
      <Button
        variant="ghost"
        @click="dialog = true"
      >
        <MdiIcon
          :path="$globals.icons.create"
          class="size-4"
        />
        {{ $t("new-recipe.bulk-add") }}
      </Button>
    </slot>
    <BaseDialog
      v-model="dialog"
      width="800"
      :title="$t('new-recipe.bulk-add')"
      :icon="$globals.icons.createAlt"
      :submit-text="$t('general.add')"
      :submit-disabled="!canSave"
      :disable-submit-on-enter="true"
      can-submit
      @submit="save"
    >
      <div class="flex flex-col gap-4 px-6 pb-2 font-sans">
        <textarea
          v-model="inputText"
          rows="12"
          autofocus
          :aria-label="$t('new-recipe.bulk-add')"
          :placeholder="$t('new-recipe.paste-in-your-recipe-data-each-line-will-be-treated-as-an-item-in-a-list')"
          class="min-h-64 w-full resize-y rounded-control border border-input bg-card px-3 py-2 text-[15px] leading-relaxed outline-none placeholder:text-muted-foreground/80 focus:border-ring focus:ring-3 focus:ring-ring/25"
        />
        <div class="flex flex-col gap-1">
          <span class="text-xs font-semibold text-muted-foreground">{{ $t("new-recipe.clean-up") }}</span>
          <div class="flex flex-wrap gap-2">
            <Button
              v-for="util in utilities"
              :key="util.id"
              variant="outline"
              size="sm"
              :title="util.description"
              @click="util.action"
            >
              {{ util.label }}
            </Button>
          </div>
        </div>
        <p class="m-0 text-sm text-muted-foreground">
          {{ $t("new-recipe.line-count", { count: splitText().length }, splitText().length) }}
        </p>
      </div>
    </BaseDialog>
  </div>
</template>

<script setup lang="ts">
import { Button } from "~/components/ui/button";
import { MdiIcon } from "~/components/ui/mdi-icon";

interface Props {
  inputTextProp?: string;
}
const props = withDefaults(defineProps<Props>(), {
  inputTextProp: "",
});

const emit = defineEmits<{
  "bulk-data": [data: string[]];
}>();

const dialog = ref(false);
const inputText = ref(props.inputTextProp);

function splitText() {
  return inputText.value.split("\n").filter(line => line.trim().length > 0);
}

const canSave = computed(() => splitText().length > 0);

function removeFirstCharacter() {
  inputText.value = splitText()
    .map(line => line.substring(1))
    .join("\n");
}

const numberedLineRegex = /\d+[.):] /gm;

function splitByNumberedLine() {
  // Split inputText by numberedLineRegex
  const matches = inputText.value.match(numberedLineRegex);

  matches?.forEach((match, idx) => {
    const replaceText = idx === 0 ? "" : "\n";
    inputText.value = inputText.value.replace(match, replaceText);
  });
}

function trimAllLines() {
  const splitLines = splitText();

  splitLines.forEach((element: string, index: number) => {
    splitLines[index] = element.trim();
  });

  inputText.value = splitLines.join("\n");
}

function save() {
  if (!canSave.value) {
    return;
  }

  emit("bulk-data", splitText());
  dialog.value = false;
}

function open() {
  dialog.value = true;
}
function close() {
  dialog.value = false;
}

const i18n = useI18n();

const utilities = computed(() => [
  {
    id: "trim-whitespace",
    label: i18n.t("new-recipe.trim-whitespace"),
    description: i18n.t("new-recipe.trim-whitespace-description"),
    action: trimAllLines,
  },
  {
    id: "trim-prefix",
    label: i18n.t("new-recipe.trim-prefix"),
    description: i18n.t("new-recipe.trim-prefix-description"),
    action: removeFirstCharacter,
  },
  {
    id: "split-by-numbered-line",
    label: i18n.t("new-recipe.split-by-numbered-line"),
    description: i18n.t("new-recipe.split-by-numbered-line-description"),
    action: splitByNumberedLine,
  },
]);

// Expose functions to parent components
defineExpose({
  open,
  close,
});
</script>
