<template>
  <div class="flex flex-col gap-6 font-sans">
    <FieldScope ref="domUrlForm">
      <form
        class="rounded-panel border bg-card p-5 sm:p-6"
        @submit.prevent="createByUrl(recipeUrl, importKeywordsAsTags, importCategories)"
      >
        <h2 class="m-0 text-xl font-bold tracking-tight">
          {{ $t('recipe.scrape-recipe') }}
        </h2>
        <p class="m-0 mt-1 text-[15px] text-muted-foreground">
          {{ $t('recipe.scrape-recipe-description') }}
          <template v-if="group?.aiProviderSettings?.audioProviderEnabled">
            {{ $t('recipe.scrape-recipe-description-transcription') }}
          </template>
        </p>

        <div class="mt-4">
          <TextField
            v-model="recipeUrl"
            type="url"
            autofocus
            validate-on="blur"
            :label="$t('new-recipe.recipe-url')"
            :prepend-icon="$globals.icons.link"
            :rules="[validators.url]"
            :hint="$t('new-recipe.url-form-hint')"
            clearable
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
            :disabled="recipeUrl === null || state.loading"
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
        {{ $t("recipe.scrape-recipe-website-being-blocked") }}
        <NuxtLink
          :to="htmlOrJsonImporterTarget"
          class="font-semibold text-primary"
        >{{ $t("recipe.scrape-recipe-try-importing-raw-html-instead") }}</NuxtLink>
      </p>
      <p
        v-if="aiEnabled"
        class="m-0 mt-2"
      >
        {{ $t("recipe.scrape-recipe-have-ai-read-the-page") }}
        <NuxtLink
          :to="aiImporterTarget"
          class="font-semibold text-primary"
        >{{ $t("recipe.import-with-ai") }}</NuxtLink>.
      </p>
      <p class="m-0 mt-3 text-sm text-muted-foreground">
        {{ $t("new-recipe.error-details") }}
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

    <!-- other ways in -->
    <ul class="m-0 flex list-none flex-col gap-1.5 p-0 text-sm text-muted-foreground">
      <li>
        {{ $t('recipe.scrape-recipe-have-a-lot-of-recipes') }}
        <NuxtLink
          :to="bulkImporterTarget"
          class="font-semibold text-primary no-underline hover:underline"
        >{{ $t('recipe.scrape-recipe-suggest-bulk-importer') }}</NuxtLink>.
      </li>
      <li>
        {{ $t('recipe.scrape-recipe-have-raw-html-or-json-data') }}
        <NuxtLink
          :to="htmlOrJsonImporterTarget"
          class="font-semibold text-primary no-underline hover:underline"
        >{{ $t('recipe.scrape-recipe-you-can-import-from-raw-data-directly') }}</NuxtLink>.
      </li>
      <li v-if="aiEnabled">
        {{ $t('recipe.scrape-recipe-have-ai-read-the-page') }}
        <NuxtLink
          :to="aiImporterTarget"
          class="font-semibold text-primary no-underline hover:underline"
        >{{ $t('recipe.import-with-ai') }}</NuxtLink>.
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { LoaderCircleIcon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import CheckboxField from "~/components/ui/field/CheckboxField.vue";
import FieldScope from "~/components/ui/field/FieldScope.vue";
import TextField from "~/components/ui/field/TextField.vue";
import { MdiIcon } from "~/components/ui/mdi-icon";
import type { AxiosResponse } from "axios";
import { useUserApi } from "~/composables/api";
import { useGroupSelf } from "~/composables/use-groups";
import { useTagStore } from "~/composables/store/use-tag-store";
import { useNewRecipeOptions } from "~/composables/use-new-recipe-options";
import { validators } from "~/composables/use-validators";

const ERROR_LINKS = [
  { text: "new-recipe.google-ld-json-info", href: "https://developers.google.com/search/docs/data-types/recipe" },
  { text: "new-recipe.github-issues", href: "https://github.com/mealie-recipes/mealie/issues" },
  { text: "new-recipe.recipe-markup-specification", href: "https://schema.org/Recipe" },
];

definePageMeta({
  key: route => route.path,
});
const state = reactive({
  error: false,
  loading: false,
});

const auth = useMealieAuth();
const api = useUserApi();
const route = useRoute();
const groupSlug = computed(() => route.params.groupSlug as string || auth.user.value?.groupSlug || "");
const { group } = useGroupSelf();

const router = useRouter();
const tags = useTagStore();

const {
  importKeywordsAsTags,
  importCategories,
  stayInEditMode,
  parseRecipe,
  navigateToRecipe,
} = useNewRecipeOptions();

const bulkImporterTarget = computed(() => `/g/${groupSlug.value}/r/create/bulk`);
const htmlOrJsonImporterTarget = computed(() => `/g/${groupSlug.value}/r/create/html`);
const aiImporterTarget = computed(() => `/g/${groupSlug.value}/r/create/ai`);
const aiEnabled = computed(() => !!group.value?.aiProviderSettings?.aiEnabled);

function handleResponse(response: AxiosResponse<string> | null, refreshTags = false) {
  if (response?.status !== 201) {
    state.error = true;
    state.loading = false;
    return;
  }
  if (refreshTags) {
    tags.actions.refresh();
  }

  navigateToRecipe(response.data, groupSlug.value, `/g/${groupSlug.value}/r/create/url`);
}

const recipeUrl = computed({
  set(recipe_import_url: string | null) {
    if (recipe_import_url !== null) {
      recipe_import_url = recipe_import_url.trim();
      router.replace({ query: { ...route.query, recipe_import_url } });
    }
  },
  get() {
    // Prefer the 'url' share field (recipe_import_url, populated by Chrome when
    // sharing a page URL). Fall back to the 'text' share field (recipe_import_text)
    // for apps that share URLs as plain text, but only when the text value is
    // actually a valid http/https URL — shared text can be arbitrary.
    const urlFromField = route.query.recipe_import_url as string | null;
    if (urlFromField) {
      return urlFromField;
    }
    const textFromField = route.query.recipe_import_text as string | null;
    if (textFromField) {
      try {
        const parsed = new URL(textFromField);
        if (parsed.protocol === "http:" || parsed.protocol === "https:") {
          return textFromField;
        }
      }
      catch { /* not a URL, ignore */ }
    }
    return null;
  },
});

onMounted(() => {
  if (recipeUrl.value) {
    // Apply legacy query params for older automations such as the Bookmarklet.
    // These are no longer used by the app itself but are easy to keep supporting.
    const importKeywordsAsTagsParam = route.query.use_keywords;
    if (importKeywordsAsTagsParam === "1") {
      importKeywordsAsTags.value = true;
    }
    else if (importKeywordsAsTagsParam === "0") {
      importKeywordsAsTags.value = false;
    }

    const stayInEditModeParam = route.query.edit;
    if (stayInEditModeParam === "1") {
      stayInEditMode.value = true;
    }
    else if (stayInEditModeParam === "0") {
      stayInEditMode.value = false;
    }

    // The URL is pre-filled via the recipeUrl computed property.
    // Do not auto-submit: the user should review the import options and
    // confirm by clicking the submit button.
  }
});

const domUrlForm = ref<{ validate: () => Promise<{ valid: boolean }> } | null>(null);

// Remove import URL from query params when leaving the page
const isLeaving = ref(false);
onBeforeRouteLeave((to) => {
  if (isLeaving.value) {
    return;
  }
  isLeaving.value = true;
  router.replace({ query: undefined }).then(() => router.push(to));
});

const createStatus = ref<string | null>(null);
async function createByUrl(url: string | null, importKeywordsAsTags: boolean, importCategories: boolean) {
  if (url === null) {
    return;
  }

  if (!domUrlForm.value?.validate() || url === "") {
    console.log("Invalid URL", url);
    return;
  }
  state.loading = true;
  const { response } = await api.recipes.createOneByUrl(
    url,
    importKeywordsAsTags,
    importCategories,
    (message: string) => createStatus.value = message,
  );
  createStatus.value = null;
  handleResponse(response, importKeywordsAsTags);
}
</script>
