<template>
  <div class="flex flex-col items-center gap-4 py-4 text-center">
    <span class="flex size-16 items-center justify-center rounded-full bg-highlight text-primary">
      <MdiIcon
        :path="$globals.icons.progressCheck"
        class="size-9"
      />
    </span>
    <h3 class="m-0 font-serif text-2xl font-normal">
      {{ $t("recipe.parser.ingredient-parser-headline") }}
    </h3>
    <div class="flex max-w-[60ch] flex-col gap-2 text-left text-[15px] leading-relaxed">
      <h4 class="m-0 text-base font-semibold">
        {{ $t("recipe.parser.ingredient-parser-title") }}
      </h4>
      <p class="m-0">
        {{ $t("recipe.parser.ingredient-parser-description") }}
      </p>
      <p class="m-0">
        {{ $t("recipe.parser.ingredient-parser-final-review-description") }}
      </p>
      <h4 class="m-0 mt-2 text-base font-semibold">
        {{ $t("recipe.parser.ingredient-parser-result-title") }}
      </h4>
      <div class="flex flex-wrap gap-2">
        <span
          v-if="autoParsed"
          class="inline-flex items-center gap-1.5 rounded-full bg-highlight px-3 py-1 text-sm font-semibold text-highlight-foreground"
        >
          <MdiIcon
            :path="$globals.icons.checkboxMarkedCircle"
            class="size-4"
          />
          {{ $t("recipe.parser.ingredient-parser-result-success", autoParsed) }}
        </span>
        <span class="inline-flex items-center gap-1.5 rounded-full bg-brand/20 px-3 py-1 text-sm font-semibold text-brand-strong dark:text-brand">
          <MdiIcon
            :path="$globals.icons.alert"
            class="size-4"
          />
          {{ $t("recipe.parser.ingredient-parser-result-failed", toReview) }}
        </span>
      </div>
    </div>
  </div>
  <CheckboxField
    v-model="dontShowAgain"
    :label="$t('recipe.parser.dont-show-again')"
  />
</template>

<script setup lang="ts">
import CheckboxField from "~/components/ui/field/CheckboxField.vue";
import { MdiIcon } from "~/components/ui/mdi-icon";

const dontShowAgain = defineModel<boolean>({ default: true });
defineProps<{
  autoParsed: number;
  toReview: number;
}>();
</script>
