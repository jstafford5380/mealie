<template>
  <div class="flex flex-col font-sans">
    <label
      v-for="(_, key) in model"
      :key="key"
      class="flex cursor-pointer items-center gap-4 py-2.5 has-[button:disabled]:cursor-not-allowed has-[button:disabled]:opacity-60"
    >
      <span class="min-w-0 flex-1">
        <span class="block text-[15px] font-medium">{{ labels[key] }}</span>
        <span
          v-if="descriptions[key]"
          class="block text-sm text-muted-foreground"
        >{{ descriptions[key] }}</span>
      </span>
      <Switch
        v-model="model[key]"
        :disabled="key == 'locked' && !isOwner"
      />
    </label>
  </div>
</template>

<script setup lang="ts">
import type { RecipeSettings } from "~/lib/api/types/recipe";
import { Switch } from "~/components/ui/switch";

defineProps<{ isOwner?: boolean }>();

const model = defineModel<RecipeSettings>({ required: true });

const i18n = useI18n();
const labels: Record<keyof RecipeSettings, string> = {
  public: i18n.t("recipe.public-recipe"),
  showNutrition: i18n.t("recipe.show-nutrition-values"),
  showAssets: i18n.t("asset.show-assets"),
  landscapeView: i18n.t("recipe.landscape-view-coming-soon"),
  disableComments: i18n.t("recipe.disable-comments"),
  locked: i18n.t("recipe.locked"),
};
const descriptions: Partial<Record<keyof RecipeSettings, string>> = {
  public: i18n.t("recipe.public-recipe-visibility-note"),
};
</script>
