<script setup lang="ts">
import type { RecipeOut } from "~/lib/api/types/recipe";
import { PlusIcon, Trash2Icon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import TextField from "~/components/ui/field/TextField.vue";

/** Editor section: where the recipe came from, plus API extras for advanced users. */
const recipe = defineModel<RecipeOut>({ required: true });
const newKey = ref("");

function addExtra() {
  const key = newKey.value.trim();
  if (!key) {
    return;
  }
  const extras = { ...(recipe.value.extras ?? {}) };
  if (key in extras) {
    return;
  }
  extras[key] = "";
  recipe.value.extras = extras;
  newKey.value = "";
}

function removeExtra(key: string | number) {
  recipe.value.extras = Object.fromEntries(Object.entries(recipe.value.extras ?? {}).filter(([k]) => k !== String(key)));
}
</script>

<template>
  <div class="flex flex-col gap-6 font-sans">
    <TextField
      v-model="recipe.orgURL"
      type="url"
      :label="$t('recipe.original-url')"
      placeholder="https://"
    />
    <AdvancedOnly>
      <div class="flex flex-col gap-3 border-t pt-5">
        <div>
          <div class="text-sm font-semibold">
            {{ $t("recipe.api-extras") }}
          </div>
          <p class="m-0 mt-1 max-w-[70ch] text-sm text-muted-foreground">
            {{ $t("recipe.api-extras-description") }}
          </p>
        </div>
        <div
          v-for="(_, key) in recipe.extras"
          :key="key"
          class="flex items-end gap-2"
        >
          <div class="max-w-md min-w-0 flex-1">
            <TextField
              v-model="recipe.extras![key]"
              :label="String(key)"
            />
          </div>
          <Button
            variant="ghost"
            size="icon"
            class="text-destructive hover:text-destructive"
            :aria-label="`${$t('general.remove')}: ${key}`"
            @click="removeExtra(key)"
          >
            <Trash2Icon class="size-4" />
          </Button>
        </div>
        <form
          class="flex items-end gap-2"
          @submit.prevent="addExtra"
        >
          <div class="max-w-xs min-w-0 flex-1">
            <TextField
              v-model="newKey"
              :label="$t('recipe.message-key')"
            />
          </div>
          <Button
            type="submit"
            variant="outline"
            :disabled="!newKey.trim()"
          >
            <PlusIcon class="size-4" />
            {{ $t("recipe.add-extra") }}
          </Button>
        </form>
      </div>
    </AdvancedOnly>
  </div>
</template>
