<template>
  <div>
    <BaseDialog
      v-model="discardDialog"
      bottom-sheet
      :title="$t('general.discard-changes')"
      color="warning"
      :icon="$globals.icons.alertCircle"
      can-confirm
      @confirm="confirmDiscard"
      @cancel="cancelDiscard"
    >
      <v-card-text>
        {{ $t("general.discard-changes-description") }}
      </v-card-text>
    </BaseDialog>
    <RecipePageParseDialog
      :model-value="isParsing"
      :ingredients="recipe.recipeIngredient"
      :width="$vuetify.display.smAndDown ? '100%' : '80%'"
      @update:model-value="toggleIsParsing"
      @save="saveParsedIngredients"
    />
    <!-- Reader -->
    <article
      v-if="!isEditMode && !isCookMode"
      key="recipe-reader"
      class="mx-auto w-full max-w-[1180px] px-4 pb-16 pt-4 font-sans sm:px-6 lg:px-8 lg:pt-8 print:hidden"
    >
      <RecipeReaderHeader
        :recipe="recipe"
        :recipe-scale="scale"
        :landscape="landscape"
      />
      <div class="mt-10 grid gap-10 lg:mt-12 lg:grid-cols-[minmax(280px,360px)_minmax(0,1fr)] lg:gap-14">
        <aside class="flex min-w-0 flex-col gap-6">
          <RecipePageScale
            v-model="scale"
            :recipe="recipe"
          />
          <RecipePageIngredientToolsView
            :recipe="displayedRecipe"
            :scale="scale"
            :ingredient-storage-key="ingredientStorageKey"
          />
          <RecipePageOrganizers
            v-if="isDesktop"
            v-model="recipe"
            @item-selected="chipClicked"
          />
        </aside>
        <div class="flex min-w-0 flex-col gap-10">
          <RecipeMethod :recipe="displayedRecipe" />
          <RecipePageOrganizers
            v-if="!isDesktop"
            v-model="recipe"
            @item-selected="chipClicked"
          />
          <RecipeNotes
            v-model="recipe.notes"
            :edit="false"
          />
        </div>
      </div>
      <WakelockSwitch class="mt-8" />
      <RecipePageComments
        v-if="!disableComments"
        v-model="recipe"
        class="mt-12 border-t pt-10"
      />
    </article>

    <!-- Cook mode -->
    <RecipeCookMode
      v-if="isCookMode"
      v-model:scale="scale"
      :recipe="recipe"
      :displayed-recipe="displayedRecipe"
      :ingredient-storage-key="ingredientStorageKey"
      @close="toggleCookMode()"
    />

    <!-- Editor -->
    <div
      v-if="isEditMode"
      key="recipe-editor"
      class="mx-auto w-full max-w-[1180px] px-4 pb-24 font-sans sm:px-6 lg:px-8 print:hidden"
    >
      <RecipeEditorBar
        :recipe="recipe"
        @save="saveRecipe"
        @delete="deleteRecipe"
        @close="closeEditor"
      />
      <RecipeJsonEditor
        v-if="isEditJSON"
        v-model="recipe"
        class="recipe-json-editor overflow-hidden rounded-panel border"
        height="calc(100dvh - 12rem)"
        mode="text"
        :main-menu-bar="false"
      />
      <!-- One form around every section, so Save validates the whole recipe. -->
      <v-form
        v-else
        ref="instructionForm"
        class="grid gap-8 lg:grid-cols-[170px_minmax(0,1fr)]"
        @submit.prevent
      >
        <nav
          :aria-label="$t('recipe.jump-to-section')"
          class="max-lg:display-none"
        >
          <ul class="sticky top-36 m-0 flex list-none flex-col gap-0.5 p-0">
            <li
              v-for="section in editorSections"
              :key="section.id"
            >
              <a
                :href="`#${section.id}`"
                class="block rounded-item px-3 py-1.5 text-sm font-medium text-muted-foreground no-underline transition-colors hover:bg-highlight hover:text-foreground"
              >{{ section.title }}</a>
            </li>
          </ul>
        </nav>
        <div class="flex min-w-0 flex-col gap-6">
          <RecipeEditorSection
            id="editor-basics"
            :title="$t('recipe.section-basics')"
          >
            <RecipeEditorBasics v-model="recipe" />
          </RecipeEditorSection>
          <RecipeEditorSection
            id="editor-ingredients"
            :title="$t('recipe.ingredients')"
          >
            <RecipePageIngredientEditor v-model="recipe" />
          </RecipeEditorSection>
          <RecipeEditorSection
            id="editor-method"
            :title="$t('recipe.instructions')"
          >
            <RecipeMethodEditor
              v-model="recipe.recipeInstructions"
              v-model:assets="recipe.assets"
              :recipe="displayedRecipe"
              :scale="scale"
            />
          </RecipeEditorSection>
          <RecipeEditorSection
            id="editor-organize"
            :title="$t('recipe.section-organize')"
          >
            <RecipePageOrganizers v-model="recipe" />
          </RecipeEditorSection>
          <RecipeEditorSection
            id="editor-notes"
            :title="$t('recipe.note')"
          >
            <RecipeNotes
              v-model="recipe.notes"
              edit
            />
          </RecipeEditorSection>
          <RecipeEditorSection
            v-if="recipe.settings.showNutrition"
            id="editor-nutrition"
            :title="$t('recipe.nutrition')"
          >
            <RecipeNutrition
              v-model="recipe.nutrition"
              edit
            />
          </RecipeEditorSection>
          <RecipeEditorSection
            v-if="recipe.settings.showAssets"
            id="editor-assets"
            :title="$t('asset.assets')"
          >
            <RecipeAssets
              v-model="recipe.assets"
              edit
              :slug="recipe.slug"
              :recipe-id="recipe.id"
            />
          </RecipeEditorSection>
          <RecipeEditorSection
            id="editor-source"
            :title="$t('recipe.section-source')"
          >
            <RecipeEditorSource v-model="recipe" />
          </RecipeEditorSection>
          <RecipeEditorSection
            id="editor-settings"
            :title="$t('recipe.recipe-settings')"
          >
            <RecipeSettingsSwitches
              v-model="recipe.settings"
              :is-owner="recipe.userId == user.id"
            />
          </RecipeEditorSection>
        </div>
      </v-form>
    </div>
    <RecipePrintContainer
      :recipe="displayedRecipe"
      :scale="scale"
    />
  </div>
</template>

<script setup lang="ts">
import type { VForm } from "~/types/auto-forms";
import { invoke, until, useMediaQuery } from "@vueuse/core";
import type { RouteLocationNormalized } from "vue-router";
import RecipePageIngredientEditor from "./RecipePageParts/RecipePageIngredientEditor.vue";
import RecipePageIngredientToolsView from "./RecipePageParts/RecipePageIngredientToolsView.vue";
import RecipePageOrganizers from "./RecipePageParts/RecipePageOrganizers.vue";
import RecipePageParseDialog from "./RecipePageParts/RecipeParseDialog/RecipePageParseDialog.vue";
import RecipePageScale from "./RecipePageParts/RecipePageScale.vue";
import RecipePageComments from "./RecipePageParts/RecipePageComments.vue";
import RecipeCookMode from "./RecipePageParts/RecipeCookMode.vue";
import RecipeEditorBar from "./RecipePageParts/RecipeEditorBar.vue";
import RecipeEditorBasics from "./RecipePageParts/RecipeEditorBasics.vue";
import RecipeEditorSection from "./RecipePageParts/RecipeEditorSection.vue";
import RecipeEditorSource from "./RecipePageParts/RecipeEditorSource.vue";
import RecipeMethodEditor from "./RecipePageParts/RecipeMethodEditor.vue";
import RecipeAssets from "~/components/Domain/Recipe/RecipeAssets.vue";
import RecipeNutrition from "~/components/Domain/Recipe/RecipeNutrition.vue";
import RecipeSettingsSwitches from "~/components/Domain/Recipe/RecipeSettingsSwitches.vue";
import RecipeMethod from "./RecipePageParts/RecipeMethod.vue";
import RecipeReaderHeader from "./RecipePageParts/RecipeReaderHeader.vue";
import RecipePrintContainer from "~/components/Domain/Recipe/RecipePrintContainer.vue";
import {
  clearPageState,
  PageMode,
  usePageState,
  usePageUser,
} from "~/composables/recipe-page/shared-state";
import { useCookModeQuery, type BooleanString } from "~/composables/recipe-page/use-cook-mode-query";
import type { NoUndefinedField } from "~/lib/api/types/non-generated";
import type { RecipeOut, CategoryOut, RecipeIngredient, TagOut, ToolOut } from "~/lib/api/types/recipe";
import { useRouteQuery } from "~/composables/use-router";
import { useUserApi } from "~/composables/api";
import { deepCopy } from "~/composables/use-utils";
import RecipeNotes from "~/components/Domain/Recipe/RecipeNotes.vue";
import { useLoggedInState } from "~/composables/use-logged-in-state";
import { useNavigationWarning } from "~/composables/use-navigation-warning";
import { useUnitConversion, useUnitSystem } from "~/composables/recipes";
import { useHouseholdSelf } from "~/composables/use-households";

const recipe = defineModel<RecipeOut>({ required: true });

const display = useDisplay();
const isDesktop = useMediaQuery("(min-width: 1024px)");
const { user } = usePageUser();
const i18n = useI18n();

/** Editor sections, in page order, for the jump list. */
const editorSections = computed(() => [
  { id: "editor-basics", title: i18n.t("recipe.section-basics") },
  { id: "editor-ingredients", title: i18n.t("recipe.ingredients") },
  { id: "editor-method", title: i18n.t("recipe.instructions") },
  { id: "editor-organize", title: i18n.t("recipe.section-organize") },
  { id: "editor-notes", title: i18n.t("recipe.note") },
  ...(recipe.value.settings.showNutrition ? [{ id: "editor-nutrition", title: i18n.t("recipe.nutrition") }] : []),
  ...(recipe.value.settings.showAssets ? [{ id: "editor-assets", title: i18n.t("asset.assets") }] : []),
  { id: "editor-source", title: i18n.t("recipe.section-source") },
  { id: "editor-settings", title: i18n.t("recipe.recipe-settings") },
]);
const auth = useMealieAuth();
const route = useRoute();
const { isOwnGroup } = useLoggedInState();

const { household } = useHouseholdSelf();

const disableComments = computed(() =>
  household.value?.preferences?.recipeDisableComments
  || recipe.value?.settings?.disableComments
  || false,
);

const groupSlug = computed(() => (route.params.groupSlug as string) || auth.user?.value?.groupSlug || "");
const ingredientStorageKey = computed(() => `recipe-ingredients:${recipe.value.id || recipe.value.slug}:checked`);

const router = useRouter();
const api = useUserApi();
const { pageMode, setMode, isEditForm, isEditJSON, isCookMode, isEditMode, isParsing, toggleCookMode, toggleIsParsing }
  = usePageState(recipe.value.slug);
const { deactivateNavigationWarning } = useNavigationWarning();
const scale = ref(1);

const { unitSystem } = useUnitSystem();
const { convertIngredient } = useUnitConversion();

/**
 * The recipe as the reader asked to see it — the recipe itself unless they've opted into a unit
 * system. Cook mode, print and the ingredient list all read this, so they convert together.
 *
 * Returns `recipe` by identity whenever nothing is being converted, and always does so in edit
 * mode. That is load-bearing rather than cosmetic: `recipe` is a defineModel the editors below
 * mutate in place, so handing them a derived copy would silently drop edits. Conversion is
 * display-only and never reaches anything that saves.
 */
const displayedRecipe = computed<RecipeOut>(() => {
  if (isEditMode.value || !unitSystem.value) {
    return recipe.value;
  }

  return {
    ...recipe.value,
    recipeIngredient: recipe.value.recipeIngredient.map(
      ingredient => convertIngredient(ingredient, unitSystem.value!, scale.value),
    ),
  };
});

/** =============================================================
 * Recipe Snapshot on Mount
 * this is used to determine if the recipe has been changed since the last save
 * and prompts the user to save if they have unsaved changes.
 */
const originalRecipe = ref<RecipeOut | null>(null);
const discardDialog = ref(false);
const pendingRoute = ref<RouteLocationNormalized | null>(null);

invoke(async () => {
  await until(recipe.value).not.toBeNull();
  originalRecipe.value = deepCopy(recipe.value);
});

function hasUnsavedChanges(): boolean {
  if (originalRecipe.value === null) {
    return false;
  }
  return JSON.stringify(recipe.value) !== JSON.stringify(originalRecipe.value);
}

function restoreOriginalRecipe() {
  if (originalRecipe.value) {
    recipe.value = deepCopy(originalRecipe.value);
  }
}

function closeEditor() {
  if (hasUnsavedChanges()) {
    pendingRoute.value = null;
    discardDialog.value = true;
  }
  else {
    setMode(PageMode.VIEW);
  }
}

function confirmDiscard() {
  restoreOriginalRecipe();
  discardDialog.value = false;

  if (pendingRoute.value) {
    const destination = pendingRoute.value;
    pendingRoute.value = null;
    router.push(destination);
  }
  else {
    setMode(PageMode.VIEW);
  }
}

function cancelDiscard() {
  discardDialog.value = false;
  pendingRoute.value = null;
}

onBeforeRouteLeave((to) => {
  if (isEditMode.value && hasUnsavedChanges()) {
    pendingRoute.value = to;
    discardDialog.value = true;
    return false;
  }
});

onUnmounted(() => {
  deactivateNavigationWarning();
  clearPageState(recipe.value.slug);
});
/** =============================================================
 * Set State onMounted
 */

const paramsEdit = useRouteQuery<BooleanString>("edit", "");
const paramsParse = useRouteQuery<BooleanString>("parse", "");
const paramsCook = useRouteQuery<BooleanString>("cook", "");
const paramsScale = useRouteQuery<string>("scale", "");
const { hydrateCookMode } = useCookModeQuery({
  cookQuery: paramsCook,
  isEditMode,
  pageMode,
  setMode,
});

onMounted(() => {
  if (paramsEdit.value === "true" && isOwnGroup.value) {
    setMode(PageMode.EDIT);
  }

  if (paramsParse.value === "true" && isOwnGroup.value) {
    toggleIsParsing(true);
  }

  // e.g. set when opened from a meal plan entry, so the recipe starts at the entry's scale
  const initialScale = parseFloat(paramsScale.value);
  if (initialScale > 0 && isFinite(initialScale)) {
    scale.value = initialScale;
  }

  hydrateCookMode();
});

// When set, the isEditMode watcher skips its URL cleanup because saveRecipe
// is navigating to a new slug that naturally omits ?edit=true.
const isNavigatingAfterRename = ref(false);

watch(isEditMode, (newVal) => {
  if (!newVal) {
    if (isNavigatingAfterRename.value) {
      isNavigatingAfterRename.value = false;
      return;
    }
    paramsEdit.value = undefined;
  }
});

watch(isParsing, () => {
  if (!isParsing.value && paramsParse.value) {
    paramsParse.value = undefined;
  }
});

/** =============================================================
 * Recipe Save Delete
 */

const instructionForm = ref<VForm | null>(null);

async function saveRecipe() {
  if (isEditForm.value) {
    const { valid } = (await instructionForm.value?.validate()) ?? { valid: false };
    if (!valid) return;
  }
  const { data, error } = await api.recipes.updateOne(route.params.slug as string, recipe.value);
  if (!error) {
    if (data?.slug && data.slug !== route.params.slug) {
      isNavigatingAfterRename.value = true;
    }
    setMode(PageMode.VIEW);
  }
  if (data) {
    recipe.value = data;
    originalRecipe.value = deepCopy(recipe.value);
    if (data.slug !== route.params.slug) {
      router.replace(`/g/${groupSlug.value}/r/` + data.slug);
    }
  }
}

async function saveParsedIngredients(ingredients: NoUndefinedField<RecipeIngredient[]>) {
  const returnToEdit = isEditMode.value;
  recipe.value.recipeIngredient = ingredients;
  await saveRecipe();
  toggleIsParsing(false);
  if (returnToEdit) {
    setMode(PageMode.EDIT);
  }
}

async function deleteRecipe() {
  const { data } = await api.recipes.deleteOne(recipe.value.slug);
  if (data?.slug) {
    router.push(`/g/${groupSlug.value}`);
  }
}

/** =============================================================
 * View Preferences
 */
const landscape = computed(() => {
  const preferLandscape = recipe.value.settings?.landscapeView;
  const smallScreen = !display.smAndUp.value;

  if (preferLandscape) {
    return true;
  }
  else if (smallScreen) {
    return true;
  }

  return false;
});

/** =============================================================
 * RecipeChip Clicked
 */

function chipClicked(item: TagOut | CategoryOut | ToolOut, itemType: string) {
  if (!item.id) {
    return;
  }
  router.push(`/g/${groupSlug.value}?${itemType}=${item.id}`);
}

// expose to template
// (all variables used in template are top-level in <script setup>)
</script>

<style lang="css">
.flip-list-move {
  transition: transform 0.5s;
}

.no-move {
  transition: transform 0s;
}

.ghost {
  opacity: 0.5;
}

.list-group {
  min-height: 38px;
}

.list-group-item i {
  cursor: pointer;
}
</style>
