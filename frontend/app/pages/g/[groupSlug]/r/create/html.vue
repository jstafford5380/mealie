<template>
  <div class="flex flex-col gap-6 font-sans">
    <FieldScope ref="domUrlForm">
      <form
        class="rounded-panel border bg-card p-5 sm:p-6"
        @submit.prevent="createFromHtmlOrJson(newRecipeData, importKeywordsAsTags, importCategories, newRecipeUrl)"
      >
        <h2 class="m-0 text-xl font-bold tracking-tight">
          {{ $t('recipe.import-from-html-or-json') }}
        </h2>
        <p class="m-0 mt-1 text-[15px] text-muted-foreground">
          {{ $t("recipe.import-from-html-or-json-description") }}
        </p>
        <p class="m-0 mt-1 text-sm text-muted-foreground">
          {{ $t("recipe.json-import-format-description-colon") }}
          <a
            href="https://schema.org/Recipe"
            target="_blank"
            rel="noopener"
            class="font-semibold text-primary"
          >schema.org/Recipe</a>
        </p>

        <div class="mt-4 max-w-lg">
          <TextField
            v-model="newRecipeUrl"
            type="url"
            validate-on="blur"
            clearable
            :label="$t('new-recipe.recipe-url')"
            :prepend-icon="$globals.icons.link"
            :rules="[validators.urlOptional]"
            :hint="$t('new-recipe.copy-and-paste-the-source-url-of-your-data-optional')"
          />
        </div>

        <div class="mt-3 flex items-center justify-between gap-3">
          <span class="text-sm font-semibold">{{ $t('new-recipe.recipe-html-or-json') }}</span>
          <label class="flex cursor-pointer items-center gap-2 text-sm">
            <Switch
              v-model="state.isEditJSON"
              @update:model-value="handleIsEditJson"
            />
            {{ $t('recipe.json-editor') }}
          </label>
        </div>
        <div class="mt-1.5">
          <RecipeJsonEditor
            v-if="state.isEditJSON"
            v-model="newRecipeData"
            height="250px"
            mode="code"
            :main-menu-bar="false"
          />
          <textarea
            v-else
            v-model="newRecipeData"
            rows="8"
            autofocus
            :aria-label="$t('new-recipe.recipe-html-or-json')"
            class="w-full resize-y rounded-control border border-input bg-card px-3 py-2 font-mono text-[13.5px] outline-none focus:border-ring focus:ring-3 focus:ring-ring/25 disabled:opacity-60"
          />
        </div>

        <div class="mt-2 grid gap-x-6 gap-y-1 sm:grid-cols-2">
          <CheckboxField
            v-model="importKeywordsAsTags"
            :label="$t('recipe.import-original-keywords-as-tags')"
          />
          <CheckboxField
            v-model="importCategories"
            :label="$t('recipe.import-original-categories')"
          />
          <CheckboxField
            v-model="stayInEditMode"
            :label="$t('recipe.stay-in-edit-mode')"
          />
          <CheckboxField
            v-model="parseRecipe"
            :label="$t('recipe.parse-recipe-ingredients-after-import')"
          />
        </div>
        <div class="mt-5 flex flex-wrap items-center justify-end gap-3 border-t pt-4">
          <span
            v-if="createStatus"
            class="me-auto text-sm text-muted-foreground"
            role="status"
          >{{ createStatus }}</span>
          <Button
            type="submit"
            :disabled="!newRecipeData || state.loading"
          >
            <LoaderCircleIcon
              v-if="state.loading"
              class="size-4 animate-spin"
            />
            {{ $t('recipe.import-recipe') }}
          </Button>
        </div>
      </form>
    </FieldScope>

    <section
      v-if="state.error"
      class="rounded-panel border border-destructive/40 bg-destructive/5 p-5 text-[15px] sm:p-6"
      role="alert"
    >
      <h2 class="m-0 mb-2 flex items-center gap-2 text-lg font-bold text-destructive">
        <MdiIcon
          :path="$globals.icons.robot"
          class="size-6"
        />
        {{ $t("new-recipe.error-title") }}
      </h2>
      <p class="m-0">
        {{ errorDetails || $t("new-recipe.html-or-json-error-details") }}
      </p>
      <p class="m-0 mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm">
        <a
          v-for="link in ERROR_LINKS"
          :key="link.href"
          :href="link.href"
          target="_blank"
          rel="noreferrer nofollow"
          class="font-semibold text-primary"
        >{{ $t(link.text) }}</a>
      </p>
    </section>

    <p
      v-if="aiEnabled"
      class="m-0 text-sm text-muted-foreground"
    >
      {{ $t("recipe.import-from-html-or-json-have-ai-read-it") }}
      <NuxtLink
        :to="aiImporterTarget"
        class="font-semibold text-primary no-underline hover:underline"
      >{{ $t("recipe.import-with-ai") }}</NuxtLink>.
    </p>
  </div>
</template>

<script setup lang="ts">
import { LoaderCircleIcon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import CheckboxField from "~/components/ui/field/CheckboxField.vue";
import FieldScope from "~/components/ui/field/FieldScope.vue";
import TextField from "~/components/ui/field/TextField.vue";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { Switch } from "~/components/ui/switch";
import type { AxiosResponse } from "axios";
import { useTagStore } from "~/composables/store/use-tag-store";
import { useUserApi } from "~/composables/api";
import { useGroupSelf } from "~/composables/use-groups";
import { useNewRecipeOptions } from "~/composables/use-new-recipe-options";
import { validators } from "~/composables/use-validators";

const ERROR_LINKS = [
  { text: "new-recipe.google-ld-json-info", href: "https://developers.google.com/search/docs/data-types/recipe" },
  { text: "new-recipe.github-issues", href: "https://github.com/mealie-recipes/mealie/issues" },
  { text: "new-recipe.recipe-markup-specification", href: "https://schema.org/Recipe" },
];

const state = reactive({
  error: false,
  errorMessage: "",
  loading: false,
  isEditJSON: false,
});
// Messages the paste page cannot explain better than its generic advice: the scraper's bare
// error codes, and the stream client's own fallback when no error message arrived.
const genericErrors = ["BAD_RECIPE_DATA", "NO_RECIPE_DATA", "CONNECTION_ERROR", "Recipe creation failed"];
const errorDetails = computed(() =>
  state.errorMessage && !genericErrors.includes(state.errorMessage) ? state.errorMessage : null,
);
const auth = useMealieAuth();
const route = useRoute();
const groupSlug = computed(() => route.params.groupSlug as string || auth.user.value?.groupSlug || "");
const domUrlForm = ref<{ validate: () => Promise<{ valid: boolean }> } | null>(null);

const { group } = useGroupSelf();
const aiImporterTarget = computed(() => `/g/${groupSlug.value}/r/create/ai`);
const aiEnabled = computed(() => !!group.value?.aiProviderSettings?.aiEnabled);

const api = useUserApi();
const tags = useTagStore();

const {
  importKeywordsAsTags,
  importCategories,
  stayInEditMode,
  parseRecipe,
  navigateToRecipe,
} = useNewRecipeOptions();

function handleResponse(response: AxiosResponse<string> | null, refreshTags = false) {
  if (response?.status !== 201) {
    state.error = true;
    state.loading = false;
    return;
  }
  if (refreshTags) {
    tags.actions.refresh();
  }

  navigateToRecipe(response.data, groupSlug.value, `/g/${groupSlug.value}/r/create/html`);
}

const newRecipeData = ref<string | object | null>(null);
const newRecipeUrl = ref<string | null>(null);

function handleIsEditJson() {
  if (state.isEditJSON) {
    if (newRecipeData.value) {
      try {
        newRecipeData.value = JSON.parse(newRecipeData.value as string);
      }
      catch {
        newRecipeData.value = { data: newRecipeData.value };
      }
    }
    else {
      newRecipeData.value = {};
    }
  }
  else if (newRecipeData.value && Object.keys(newRecipeData.value).length > 0) {
    newRecipeData.value = JSON.stringify(newRecipeData.value);
  }
  else {
    newRecipeData.value = null;
  }
}
handleIsEditJson();

const createStatus = ref<string | null>(null);
async function createFromHtmlOrJson(htmlOrJsonData: string | object | null, importKeywordsAsTags: boolean, importCategories: boolean, url: string | null = null) {
  if (!htmlOrJsonData) {
    return;
  }

  const isValid = await domUrlForm.value?.validate();
  if (!isValid?.valid) {
    return;
  }

  let dataString;
  if (typeof htmlOrJsonData === "string") {
    dataString = htmlOrJsonData;
  }
  else {
    dataString = JSON.stringify(htmlOrJsonData);
  }

  state.error = false;
  state.errorMessage = "";
  state.loading = true;
  const { response, error } = await api.recipes.createOneByHtmlOrJson(
    dataString,
    importKeywordsAsTags,
    importCategories,
    url,
    (message: string) => createStatus.value = message,
  );
  createStatus.value = null;
  state.errorMessage = error?.message || "";
  handleResponse(response, importKeywordsAsTags);
}
</script>
