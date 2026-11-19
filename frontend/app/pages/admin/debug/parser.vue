<template>
  <div class="mx-auto flex w-full max-w-[860px] flex-col gap-8 px-4 pb-16 pt-3 font-sans sm:px-6 lg:pt-8">
    <header>
      <h1 class="m-0 text-[26px] font-bold tracking-tight sm:text-[32px]">
        {{ $t('admin.ingredients-natural-language-processor') }}
      </h1>
      <p class="m-0 mt-1 max-w-[65ch] text-[15px] text-muted-foreground">
        {{ $t('admin.ingredients-natural-language-processor-explanation') }}
      </p>
      <p class="m-0 mt-2 max-w-[65ch] text-[15px] text-muted-foreground">
        {{ $t('admin.ingredients-natural-language-processor-explanation-2') }}
      </p>
    </header>

    <form
      class="rounded-panel border bg-card p-5 sm:p-6"
      @submit.prevent="processIngredient"
    >
      <div class="mb-3 flex flex-wrap items-center gap-3">
        <div
          role="radiogroup"
          :aria-label="$t('admin.parser')"
          class="inline-flex rounded-control border bg-muted/50 p-0.5"
        >
          <button
            v-for="parser in PARSERS"
            :key="parser.value"
            type="button"
            role="radio"
            :aria-checked="state.parser === parser.value"
            class="h-8 rounded-item px-3 text-sm font-semibold transition-colors"
            :class="state.parser === parser.value ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'"
            @click="state.parser = parser.value; processIngredient()"
          >
            {{ $t(parser.label) }}
          </button>
        </div>
        <label class="ms-auto flex cursor-pointer items-center gap-2 text-sm">
          <Checkbox v-model="showConfidence" />
          {{ $t('admin.show-individual-confidence') }}
        </label>
      </div>
      <div class="flex flex-wrap items-end gap-3">
        <div class="min-w-0 flex-1 basis-60">
          <TextField
            v-model="state.ingredient"
            :label="$t('admin.ingredient-text')"
          />
        </div>
        <Button
          type="submit"
          class="mb-1.5"
        >
          {{ $t("admin.parse") }}
        </Button>
      </div>
    </form>

    <section v-if="state.results">
      <p
        v-if="state.parser !== 'brute' && getConfidence('average')"
        class="m-0 mb-3"
      >
        <span
          class="rounded-full px-3 py-1 text-sm font-semibold"
          :class="CONFIDENCE_CLASSES[getColor('average') || ''] || 'bg-muted'"
        >{{ $t('admin.average-confident', [getConfidence("average")]) }}</span>
      </p>
      <div class="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        <template
          v-for="(prop, index) in properties"
          :key="index"
        >
          <div
            v-if="prop.value"
            class="flex flex-col gap-1 rounded-card border bg-card px-4 py-3"
          >
            <span class="text-sm text-muted-foreground">{{ prop.subtitle }}</span>
            <span class="text-lg font-semibold break-words">{{ prop.value }}</span>
            <span
              v-if="prop.confidence && showConfidence"
              class="w-fit rounded-full px-2 py-0.5 text-xs font-semibold"
              :class="CONFIDENCE_CLASSES[prop.color || ''] || 'bg-muted'"
            >{{ $t('admin.average-confident', [prop.confidence]) }}</span>
          </div>
        </template>
      </div>
    </section>

    <section>
      <h2 class="m-0 mb-3 text-base font-semibold">
        {{ $t('admin.try-an-example') }}
      </h2>
      <div class="flex flex-col gap-2">
        <button
          v-for="(text, idx) in tryText"
          :key="idx"
          type="button"
          class="rounded-card border bg-card px-4 py-3 text-start text-[15px] transition-colors hover:border-primary/50 hover:bg-primary/5"
          @click="processTryText(text)"
        >
          {{ text }}
        </button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { Button } from "~/components/ui/button";
import { Checkbox } from "~/components/ui/checkbox";
import TextField from "~/components/ui/field/TextField.vue";
import { alert } from "~/composables/use-toast";
import { useUserApi } from "~/composables/api";
import type { IngredientConfidence } from "~/lib/api/types/recipe";
import type { Parser } from "~/lib/api/user/recipes/recipe";

const PARSERS = [
  { value: "nlp", label: "admin.nlp" },
  { value: "brute", label: "admin.brute" },
  { value: "ai-providers", label: "admin.ai-providers" },
] as const;

const CONFIDENCE_CLASSES: Record<string, string> = {
  success: "bg-primary/15 text-primary",
  warning: "bg-brand/20 text-brand-strong",
  error: "bg-destructive/15 text-destructive",
};

type ConfidenceAttribute = "average" | "comment" | "name" | "unit" | "quantity" | "food";

definePageMeta({
  layout: "admin",
});

const api = useUserApi();

const state = reactive({
  loading: false,
  ingredient: "",
  results: false,
  parser: "nlp" as Parser,
});

const i18n = useI18n();

// Set page title
useSeoMeta({
  title: i18n.t("admin.parser"),
});

const confidence = ref<IngredientConfidence>({});

function getColor(attribute: ConfidenceAttribute) {
  const percentage = getConfidence(attribute);
  if (percentage === undefined) return;

  const p_as_num = parseFloat(percentage.replace("%", ""));

  // Set color based off range
  if (p_as_num > 75) {
    return "success";
  }
  else if (p_as_num > 60) {
    return "warning";
  }
  else {
    return "error";
  }
}

function getConfidence(attribute: ConfidenceAttribute) {
  if (!confidence.value) {
    return;
  }

  const property = confidence.value[attribute];
  if (property !== undefined && property !== null) {
    return `${(+property * 100).toFixed(0)}%`;
  }
  return undefined;
}

const tryText = [
  "2 tbsp minced cilantro, leaves and stems",
  "1 large yellow onion, coarsely chopped",
  "1 1/2 tsp garam masala",
  "1 inch piece fresh ginger, (peeled and minced)",
  "2 cups mango chunks, (2 large mangoes) (fresh or frozen)",
];

function processTryText(str: string) {
  state.ingredient = str;
  processIngredient();
}

async function processIngredient() {
  if (state.ingredient === "") {
    return;
  }

  state.loading = true;

  const { data } = await api.recipes.parseIngredient(state.parser, state.ingredient);

  if (data) {
    state.results = true;

    if (data.confidence) confidence.value = data.confidence;

    // TODO: Remove ts-ignore
    // ts-ignore because data will likely change significantly once I figure out how to return results
    // for the parser. For now we'll leave it like this
    properties.comment.value = data.ingredient.note || "";
    properties.quantity.value = data.ingredient.quantity || "";
    properties.unit.value = data.ingredient?.unit?.name || "";
    properties.food.value = data.ingredient?.food?.name || "";

    (["comment", "quantity", "unit", "food"] as ConfidenceAttribute[]).forEach((property) => {
      const color = getColor(property);
      const confidence = getConfidence(property);
      if (color) {
        properties[property].color = color;
      }
      if (confidence) {
        properties[property].confidence = confidence;
      }
    });
  }
  else {
    alert.error(i18n.t("events.something-went-wrong") as string);
    state.results = false;
  }
  state.loading = false;
}

const properties = reactive({
  quantity: {
    subtitle: i18n.t("recipe.quantity"),
    value: "" as string | number,
    color: null,
    confidence: null,
  },
  unit: {
    subtitle: i18n.t("recipe.unit"),
    value: "",
    color: null,
    confidence: null,
  },
  food: {
    subtitle: i18n.t("shopping-list.food"),
    value: "",
    color: null,
    confidence: null,
  },
  comment: {
    subtitle: i18n.t("recipe.comment"),
    value: "",
    color: null,
    confidence: null,
  },
});

const showConfidence = ref(false);
</script>

<style scoped></style>
