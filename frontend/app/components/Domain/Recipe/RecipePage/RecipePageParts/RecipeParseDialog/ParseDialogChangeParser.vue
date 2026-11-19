<template>
  <div class="flex flex-wrap items-center gap-2 rounded-card border border-primary/30 bg-highlight/40 px-4 py-2.5 font-sans">
    <button
      type="button"
      class="min-w-0 flex-1 text-left text-sm font-medium text-primary hover:underline"
      @click="$emit('parse')"
    >
      {{ $t('recipe.parser.try-again-with-parser', { parser: currentParserText }) }}
    </button>
    <Button
      variant="ghost"
      size="sm"
      @click="open = true"
    >
      <MdiIcon
        :path="$globals.icons.edit"
        class="size-4"
      />
      {{ $t('recipe.parser.select-parser') }}
    </Button>
  </div>
  <p
    v-if="showNlpLanguageHint"
    class="m-0 mt-3 rounded-control bg-muted px-3 py-2 text-sm text-muted-foreground"
  >
    {{ $t("recipe.parser.natural-language-processor-english-only") }}
  </p>
  <BaseDialog
    v-model="open"
    :title="$t('recipe.parser.select-parser')"
    :icon="$globals.icons.fileSign"
  >
    <div class="flex flex-col gap-1 px-6 pb-4 font-sans">
      <button
        v-for="(parser) in availableParsers.filter(({ hide }) => !hide)"
        :key="parser.value"
        type="button"
        class="flex items-center justify-between rounded-control px-3 py-2.5 text-left text-[15px] hover:bg-highlight"
        :class="parser.value === currentParser && 'bg-highlight/60 font-semibold'"
        @click="currentParser = parser.value as Parser; open = false; $emit('parse')"
      >
        {{ parser.text }}
        <ChevronRightIcon class="size-4 text-muted-foreground" />
      </button>
    </div>
  </BaseDialog>
</template>

<script setup lang="ts">
import { ChevronRightIcon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import { MdiIcon } from "~/components/ui/mdi-icon";
import type { MenuItem } from "~/components/global/BaseOverflowButton.vue";
import type { Parser } from "~/lib/api/user/recipes/recipe";

defineProps<{ availableParsers: MenuItem[]; showNlpLanguageHint: boolean }>();
const emit = defineEmits<{ parse: [] }>();
const currentParser = defineModel<Parser>({ default: "nlp" });

const { t } = useI18n();

const currentParserText = computed(() => {
  switch (currentParser.value) {
    case "brute": return t("recipe.parser.brute-parser");
    case "openai": return t("recipe.parser.ai-parser");
  }
  return t("recipe.parser.natural-language-processor");
});
const open = ref(false);
watch(currentParser, () => emit("parse"));
</script>
