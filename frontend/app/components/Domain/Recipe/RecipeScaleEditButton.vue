<template>
  <div
    v-if="yieldDisplay"
    class="inline-flex items-center font-sans"
  >
    <div
      v-if="canEditScale"
      role="group"
      :aria-label="$t('recipe.servings')"
      class="inline-flex h-10 items-center rounded-control border border-input bg-card"
    >
      <button
        type="button"
        class="inline-flex h-full w-10 items-center justify-center rounded-s-control text-muted-foreground hover:bg-highlight hover:text-highlight-foreground disabled:opacity-40"
        :disabled="disableDecrement"
        :aria-label="$t('recipe.decrease-scale-label')"
        @click="recalculateScale(yieldQuantity - 1)"
      >
        <MinusIcon class="size-4" />
      </button>
      <Popover v-model:open="menu">
        <PopoverTrigger as-child>
          <button
            type="button"
            class="h-full px-2 text-sm font-semibold hover:bg-highlight/60"
            :title="$t('recipe.edit-scale')"
          >
            <SafeInlineHtml :html="yieldDisplay" />
          </button>
        </PopoverTrigger>
        <PopoverContent
          align="center"
          class="flex w-64 flex-col gap-2"
        >
          <label
            :for="inputId"
            class="text-sm font-semibold"
          >{{ $t("recipe.servings") }}</label>
          <div class="flex items-center gap-2">
            <input
              :id="inputId"
              type="number"
              min="0"
              step="any"
              inputmode="decimal"
              :value="yieldQuantity"
              class="h-10 min-w-0 flex-1 rounded-control border border-input bg-card px-3 text-base outline-none focus:border-ring focus:ring-3 focus:ring-ring/25"
              @change="recalculateScale(Number(($event.target as HTMLInputElement).value) || 0)"
            >
            <Button
              variant="outline"
              size="icon"
              :aria-label="$t('recipe.reset-servings-count')"
              :title="$t('recipe.reset-servings-count')"
              @click="scale = 1"
            >
              <RotateCcwIcon class="size-4" />
            </Button>
          </div>
        </PopoverContent>
      </Popover>
      <button
        type="button"
        class="inline-flex h-full w-10 items-center justify-center rounded-e-control text-muted-foreground hover:bg-highlight hover:text-highlight-foreground"
        :aria-label="$t('recipe.increase-scale-label')"
        @click="recalculateScale(yieldQuantity + 1)"
      >
        <PlusIcon class="size-4" />
      </button>
    </div>
    <span
      v-else
      class="inline-flex h-10 items-center rounded-control bg-subtle px-3 text-sm font-semibold text-subtle-foreground"
    >
      <SafeInlineHtml :html="yieldDisplay" />
    </span>
  </div>
</template>

<script setup lang="ts">
import { MinusIcon, PlusIcon, RotateCcwIcon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "~/components/ui/popover";
import { calculateScaleFromYield, useScaledAmount } from "~/composables/recipes/use-scaled-amount";

interface Props {
  recipeServings?: number;
  editScale?: boolean;
}
const props = withDefaults(defineProps<Props>(), {
  recipeServings: 0,
  editScale: false,
});

const scale = defineModel<number>({ required: true });

const i18n = useI18n();
const menu = ref<boolean>(false);
const inputId = `servings-${useId()}`;
const canEditScale = computed(() => props.editScale && props.recipeServings > 0);

function recalculateScale(newYield: number) {
  const newScale = calculateScaleFromYield(newYield, props.recipeServings);
  if (newScale !== null) {
    scale.value = newScale;
  }
}

const recipeYieldAmount = computed(() => {
  return useScaledAmount(props.recipeServings, scale.value);
});
const yieldQuantity = computed(() => recipeYieldAmount.value.scaledAmount);
const yieldDisplay = computed(() => {
  return yieldQuantity.value
    ? i18n.t(
      "recipe.serves-amount", { amount: recipeYieldAmount.value.scaledAmountDisplay },
    ) as string
    : "";
});

const disableDecrement = computed(() => {
  return yieldQuantity.value <= 1;
});
</script>
