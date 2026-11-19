<template>
  <BaseDialog
    v-model="dialog"
    :icon="$globals.icons.printerSettings"
    :title="$t('general.print-preferences')"
    width="70%"
    max-width="816px"
  >
    <div class="flex flex-col gap-5 px-6 pb-4 font-sans">
      <div class="flex flex-wrap items-start gap-x-10 gap-y-4">
        <div class="flex flex-col gap-1.5">
          <span class="text-sm font-semibold">{{ $t('recipe.recipe-image') }}</span>
          <div
            role="radiogroup"
            :aria-label="$t('recipe.recipe-image')"
            class="inline-flex rounded-control bg-muted p-1"
          >
            <button
              v-for="option in imageOptions"
              :key="option.value"
              type="button"
              role="radio"
              :aria-checked="preferences.imagePosition === option.value"
              :aria-label="option.label"
              :title="option.label"
              class="inline-flex size-9 items-center justify-center rounded-item transition-colors"
              :class="preferences.imagePosition === option.value ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'"
              @click="preferences.imagePosition = option.value"
            >
              <MdiIcon
                :path="option.icon"
                class="size-5"
              />
            </button>
          </div>
        </div>
        <div class="grid min-w-0 flex-1 grid-cols-1 gap-x-8 sm:grid-cols-2">
          <label
            v-for="toggle in toggles"
            :key="toggle.key"
            class="flex cursor-pointer items-center justify-between gap-3 py-2 text-[15px]"
          >
            {{ toggle.label }}
            <Switch v-model="preferences[toggle.key]" />
          </label>
        </div>
      </div>
      <div class="max-h-[40vh] overflow-y-auto rounded-card border bg-white text-black">
        <RecipePrintView :recipe="recipe" />
      </div>
    </div>
  </BaseDialog>
</template>

<script setup lang="ts">
import type { RecipeOut } from "~/lib/api/types/recipe";
import { ImagePosition, useUserPrintPreferences } from "~/composables/use-users/preferences";
import RecipePrintView from "~/components/Domain/Recipe/RecipePrintView.vue";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { Switch } from "~/components/ui/switch";

interface Props {
  recipe?: RecipeOut;
}
withDefaults(defineProps<Props>(), {
  recipe: undefined,
});

const dialog = defineModel<boolean>({ default: false });
const preferences = useUserPrintPreferences();
const i18n = useI18n();
const { $globals } = useNuxtApp();

const imageOptions = computed(() => [
  { value: ImagePosition.left, icon: $globals.icons.dockLeft, label: i18n.t("recipe.image-left") },
  { value: ImagePosition.right, icon: $globals.icons.dockRight, label: i18n.t("recipe.image-right") },
  { value: ImagePosition.hidden, icon: $globals.icons.windowClose, label: i18n.t("recipe.image-hidden") },
]);
const toggles = computed(() => [
  { key: "showDescription" as const, label: i18n.t("recipe.description") },
  { key: "showNotes" as const, label: i18n.t("recipe.notes") },
  { key: "showNutrition" as const, label: i18n.t("recipe.nutrition") },
  { key: "expandChildRecipes" as const, label: i18n.t("recipe.include-linked-recipe-ingredients") },
  { key: "showLinkedIngredients" as const, label: i18n.t("recipe.linked-ingredients") },
  { key: "showSubstitutions" as const, label: i18n.t("recipe.substitutions") },
]);
</script>
