<template>
  <DropdownMenu :modal="false">
    <DropdownMenuTrigger
      as-child
      :disabled="!hasConvertibleIngredients"
    >
      <Button
        variant="outline"
        class="font-sans"
        :title="$t('general.units')"
        :disabled="!hasConvertibleIngredients"
      >
        <MdiIcon
          :path="$globals.icons.units"
          class="size-[18px]"
        />
        {{ activeLabel }}
        <ChevronDownIcon class="size-4 opacity-60" />
      </Button>
    </DropdownMenuTrigger>
    <DropdownMenuContent
      align="start"
      class="min-w-56"
    >
      <DropdownMenuLabel class="text-xs text-muted-foreground">
        {{ $t("general.units") }}
      </DropdownMenuLabel>
      <DropdownMenuItem
        v-for="option in options"
        :key="option.key"
        :class="option.value === unitSystem && 'bg-highlight/60 font-semibold text-highlight-foreground'"
        :aria-current="option.value === unitSystem ? 'true' : undefined"
        @select="unitSystem = option.value"
      >
        {{ option.text }}
      </DropdownMenuItem>
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
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "~/components/ui/dropdown-menu";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { canConvertIngredient, useUnitSystem } from "~/composables/recipes";
import type { UnitSystem } from "~/composables/recipes/unit-systems";
import type { RecipeOut } from "~/lib/api/types/recipe";

const props = defineProps<{ recipe: RecipeOut }>();

const i18n = useI18n();
const { unitSystem } = useUnitSystem();

/**
 * Readers call US customary "imperial", so that's what the labels say. The stored value stays
 * `us`, which is what the units actually are, and leaves `imperial` free should a genuine
 * imperial ladder ever be added.
 */
const options = computed<{ key: string; value: UnitSystem | null; text: string }[]>(() => [
  { key: "as-written", value: null, text: i18n.t("recipe.unit-system.as-written") },
  { key: "metric", value: "metric", text: i18n.t("recipe.unit-system.metric-with-hint") },
  { key: "us", value: "us", text: i18n.t("recipe.unit-system.imperial-with-hint") },
]);

const activeLabel = computed(() => {
  switch (unitSystem.value) {
    case "metric":
      return i18n.t("recipe.unit-system.metric");
    case "us":
      return i18n.t("recipe.unit-system.imperial");
    default:
      return i18n.t("recipe.unit-system.as-written");
  }
});

// Disabled when nothing on the recipe carries the standardization data conversion needs, so the
// control stays in place — the reader can see units are a thing here — but never does nothing
// when used.
const hasConvertibleIngredients = computed(() =>
  props.recipe.recipeIngredient.some(canConvertIngredient),
);
</script>
