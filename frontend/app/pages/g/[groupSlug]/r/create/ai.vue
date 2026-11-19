<template>
  <div class="flex flex-col gap-6 font-sans">
    <p
      v-if="!aiEnabled"
      class="m-0 rounded-card border border-primary/30 bg-primary/8 p-4 text-[15px]"
    >
      {{ $t('recipe.import-with-ai-provider-required') }}
    </p>
    <FieldScope
      v-else
      ref="domUrlForm"
    >
      <form
        class="rounded-panel border bg-card p-5 sm:p-6"
        @submit.prevent="createRecipe"
      >
        <h2 class="m-0 text-xl font-bold tracking-tight">
          {{ $t('recipe.import-with-ai') }}
        </h2>
        <p class="m-0 mt-1 text-[15px] text-muted-foreground">
          {{ $t('recipe.import-with-ai-description') }}
          <template v-if="videosEnabled">
            {{ $t('recipe.import-with-ai-video-description') }}
          </template>
        </p>

        <div class="mt-4">
          <TextField
            v-model="recipeUrl"
            type="url"
            validate-on="blur"
            clearable
            :label="$t('new-recipe.recipe-url')"
            :prepend-icon="$globals.icons.link"
            :rules="[validators.urlOptional]"
            :hint="$t('recipe.import-with-ai-url-hint')"
            :disabled="state.loading"
          />
        </div>

        <div class="mt-3 flex items-center justify-between gap-3">
          <span class="text-sm font-semibold">{{ $t('recipe.import-with-ai-content') }}</span>
          <label class="flex cursor-pointer items-center gap-2 text-sm">
            <Switch
              v-model="state.isEditJSON"
              :disabled="state.loading"
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
            rows="6"
            :disabled="state.loading"
            :aria-label="$t('recipe.import-with-ai-content')"
            class="w-full resize-y rounded-control border border-input bg-card px-3 py-2 font-mono text-[13.5px] outline-none focus:border-ring focus:ring-3 focus:ring-ring/25 disabled:opacity-60 font-sans text-[15px]"
          />
          <p class="m-0 mt-1 text-sm text-muted-foreground">
            {{ $t('recipe.import-with-ai-content-hint') }}
          </p>
        </div>

        <div class="mt-4">
          <RecipeImportImages
            v-if="imagesEnabled"
            v-model="uploadedImages"
            :disabled="state.loading"
          />
          <p
            v-else
            class="m-0 rounded-control border border-primary/30 bg-primary/8 px-3 py-2 text-sm"
          >
            {{ $t('recipe.import-with-ai-image-provider-required') }}
          </p>
        </div>

        <div class="mt-3 grid gap-x-6 gap-y-1 sm:grid-cols-2">
          <CheckboxField
            v-model="translateRecipe"
            :label="$t('recipe.should-translate-description')"
            :disabled="state.loading"
          />
          <CheckboxField
            v-model="createNewOrganizers"
            :label="$t('recipe.create-new-organizers')"
            :hint="$t('recipe.create-new-organizers-hint')"
            :disabled="state.loading"
          />
          <CheckboxField
            v-model="stayInEditMode"
            :label="$t('recipe.stay-in-edit-mode')"
            :disabled="state.loading"
          />
          <CheckboxField
            v-model="parseRecipe"
            :label="$t('recipe.parse-recipe-ingredients-after-import')"
            :disabled="state.loading"
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
            :disabled="!hasSource || state.loading"
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
        {{ state.errorMessage || $t("recipe.import-with-ai-error-details") }}
      </p>
    </section>

    <ul class="m-0 flex list-none flex-col gap-1.5 p-0 text-sm text-muted-foreground">
      <li>
        {{ $t('recipe.import-with-ai-without-ai-question') }}
        <NuxtLink
          :to="urlImporterTarget"
          class="font-semibold text-primary no-underline hover:underline"
        >{{ $t('recipe.import-with-ai-use-url-import') }}</NuxtLink>.
      </li>
      <li>
        {{ $t('recipe.scrape-recipe-have-raw-html-or-json-data') }}
        <NuxtLink
          :to="htmlOrJsonImporterTarget"
          class="font-semibold text-primary no-underline hover:underline"
        >{{ $t('recipe.scrape-recipe-you-can-import-from-raw-data-directly') }}</NuxtLink>.
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
import { Switch } from "~/components/ui/switch";
import { useUserApi } from "~/composables/api";
import { useGroupSelf } from "~/composables/use-groups";
import { useTagStore } from "~/composables/store/use-tag-store";
import { useNewRecipeOptions } from "~/composables/use-new-recipe-options";
import { validators } from "~/composables/use-validators";

definePageMeta({
  key: route => route.path,
});

const state = reactive({
  error: false,
  errorMessage: "",
  loading: false,
  isEditJSON: false,
});

const i18n = useI18n();
const api = useUserApi();
const auth = useMealieAuth();
const route = useRoute();
const tags = useTagStore();
const { group } = useGroupSelf();

const groupSlug = computed(() => route.params.groupSlug as string || auth.user.value?.groupSlug || "");
const urlImporterTarget = computed(() => `/g/${groupSlug.value}/r/create/url`);
const htmlOrJsonImporterTarget = computed(() => `/g/${groupSlug.value}/r/create/html`);
const aiEnabled = computed(() => !!group.value?.aiProviderSettings?.aiEnabled);
const imagesEnabled = computed(() => !!group.value?.aiProviderSettings?.imageProviderEnabled);
const videosEnabled = computed(() => !!group.value?.aiProviderSettings?.audioProviderEnabled);

const domUrlForm = ref<{ validate: () => Promise<{ valid: boolean }> } | null>(null);
const recipeUrl = ref<string | null>(null);
const newRecipeData = ref<string | object | null>(null);
const uploadedImages = ref<(Blob | File)[]>([]);
const createStatus = ref<string | null>(null);

const {
  stayInEditMode,
  parseRecipe,
  translateRecipe,
  createNewOrganizers,
  navigateToRecipe,
} = useNewRecipeOptions({
  enableImportKeywords: false,
  enableImportCategories: false,
  enableTranslateRecipe: true,
  enableCreateNewOrganizers: true,
});

const contentAsString = computed(() => {
  const data = newRecipeData.value;
  if (!data) {
    return null;
  }

  return typeof data === "string" ? data : JSON.stringify(data);
});

const hasSource = computed(() => !!(recipeUrl.value || contentAsString.value || uploadedImages.value.length));

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

async function createRecipe() {
  if (!hasSource.value) {
    return;
  }

  const isValid = await domUrlForm.value?.validate();
  if (!isValid?.valid) {
    return;
  }

  state.error = false;
  state.errorMessage = "";
  state.loading = true;

  const { data, error } = await api.recipes.createOneWithAI(
    {
      content: contentAsString.value,
      url: recipeUrl.value,
      images: uploadedImages.value,
      translateLanguage: translateRecipe.value ? i18n.locale.value : null,
      createNewOrganizers: createNewOrganizers.value,
    },
    (message: string) => createStatus.value = message,
  );

  createStatus.value = null;

  if (error || !data) {
    state.error = true;
    state.errorMessage = error?.message || "";
    state.loading = false;
    return;
  }

  if (createNewOrganizers.value) {
    tags.actions.refresh();
  }

  navigateToRecipe(data, groupSlug.value, `/g/${groupSlug.value}/r/create/ai`);
}
</script>
