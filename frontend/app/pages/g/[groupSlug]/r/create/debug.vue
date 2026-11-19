<template>
  <div class="flex flex-col gap-6 font-sans">
    <form
      class="rounded-panel border bg-card p-5 sm:p-6"
      @submit.prevent="debugUrl(recipeUrl)"
    >
      <h2 class="m-0 text-xl font-bold tracking-tight">
        {{ $t('recipe.recipe-debugger') }}
      </h2>
      <p class="m-0 mt-1 text-[15px] text-muted-foreground">
        {{ $t('recipe.recipe-debugger-description') }}
      </p>
      <div class="mt-4">
        <TextField
          v-model="recipeUrl"
          type="url"
          autofocus
          validate-on="blur"
          clearable
          :label="$t('new-recipe.recipe-url')"
          :prepend-icon="$globals.icons.link"
          :rules="[validators.url]"
          :hint="$t('new-recipe.url-form-hint')"
        />
      </div>
      <div
        v-if="group?.aiProviderSettings?.aiEnabled"
        class="mt-2"
      >
        <CheckboxField
          v-model="state.useOpenAI"
          :label="$t('recipe.use-ai')"
          :hint="$t('recipe.recipe-debugger-use-ai-description')"
        />
      </div>
      <div class="mt-5 flex flex-wrap items-center justify-end gap-3 border-t pt-4">
        <Button
          type="submit"
          :disabled="recipeUrl === null || state.loading"
        >
          <LoaderCircleIcon
            v-if="state.loading"
            class="size-4 animate-spin"
          />
          {{ $t('recipe.debug') }}
        </Button>
      </div>
    </form>
    <section
      v-if="debugData"
      class="flex flex-col gap-2"
    >
      <label class="flex w-fit cursor-pointer items-center gap-2 text-sm">
        <Switch v-model="debugTreeView" />
        {{ $t('recipe.tree-view') }}
      </label>
      <RecipeJsonEditor
        v-model="debugData"
        height="700px"
        :mode="debugTreeView ? 'tree' : 'text'"
        :main-menu-bar="false"
        :read-only="true"
      />
    </section>
  </div>
</template>

<script setup lang="ts">
import { LoaderCircleIcon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import CheckboxField from "~/components/ui/field/CheckboxField.vue";
import TextField from "~/components/ui/field/TextField.vue";
import { Switch } from "~/components/ui/switch";
import { useUserApi } from "~/composables/api";
import { useGroupSelf } from "~/composables/use-groups";
import { validators } from "~/composables/use-validators";
import type { RecipeDraft } from "~/lib/api/types/recipe";

const state = reactive({
  loading: false,
  useOpenAI: false,
});

const api = useUserApi();
const route = useRoute();
const router = useRouter();
const { group } = useGroupSelf();

const recipeUrl = computed({
  set(recipe_import_url: string | null) {
    if (recipe_import_url !== null) {
      recipe_import_url = recipe_import_url.trim();
      router.replace({ query: { ...route.query, recipe_import_url } });
    }
  },
  get() {
    return route.query.recipe_import_url as string | null;
  },
});

const debugTreeView = ref(false);

const debugData = ref<RecipeDraft | null>(null);

async function debugUrl(url: string | null) {
  if (url === null) {
    return;
  }

  state.loading = true;

  const { data } = await api.recipes.testCreateOneUrl(url, state.useOpenAI);

  state.loading = false;
  debugData.value = data;
}
</script>
