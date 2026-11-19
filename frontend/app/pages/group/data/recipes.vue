<template>
  <div>
    <!-- Export Purge Confirmation Dialog -->
    <BaseDialog
      v-model="purgeExportsDialog"
      :title="$t('data-pages.recipes.purge-exports')"
      color="error"
      :icon="$globals.icons.alertCircle"
      can-confirm
      @confirm="purgeExports()"
    >
      <p class="m-0 px-6 pb-2 text-[15px]">
        {{ $t('data-pages.recipes.are-you-sure-you-want-to-delete-all-export-data') }}
      </p>
    </BaseDialog>

    <!-- One dialog for every bulk action -->
    <BaseDialog
      ref="domDialog"
      v-model="dialog.state"
      width="650px"
      :color="dialog.mode == MODES.delete ? 'error' : undefined"
      :icon="dialog.icon"
      :title="dialog.title"
      :submit-text="$t('general.submit')"
      :can-submit="dialog.mode != MODES.delete"
      :can-delete="dialog.mode == MODES.delete"
      @submit="dialog.callback"
      @delete="dialog.callback"
    >
      <div class="flex flex-col gap-3 px-6 pb-2 text-[15px]">
        <template v-if="dialog.mode == MODES.tag">
          <RecipeOrganizerSelector
            v-model="toSetTags"
            selector-type="tags"
          />
        </template>
        <template v-else-if="dialog.mode == MODES.category">
          <RecipeOrganizerSelector
            v-model="toSetCategories"
            selector-type="categories"
          />
        </template>
        <template v-else-if="dialog.mode == MODES.delete || dialog.mode == MODES.export">
          <p class="m-0">
            {{ dialog.mode == MODES.delete
              ? $t('data-pages.recipes.confirm-delete-recipes')
              : $t('data-pages.recipes.the-following-recipes-selected-length-will-be-exported', [selected.length]) }}
          </p>
          <ul class="m-0 max-h-[40vh] list-none overflow-y-auto rounded-control border p-0">
            <li
              v-for="item in selected"
              :key="item.id || item.slug"
              class="border-b px-3 py-2 last:border-b-0"
            >
              {{ item.name }}
            </li>
          </ul>
        </template>
        <template v-else-if="dialog.mode == MODES.updateSettings">
          <p class="m-0 text-muted-foreground">
            {{ $t('data-pages.recipes.settings-chosen-explanation') }}
          </p>
          <RecipeSettingsSwitches v-model="recipeSettings" />
          <p class="m-0 text-sm text-muted-foreground">
            {{ $t('data-pages.recipes.selected-length-recipe-s-settings-will-be-updated', selected.length) }}
          </p>
        </template>
        <template v-else-if="dialog.mode == MODES.changeOwner">
          <div class="flex items-end gap-3">
            <UserAvatar
              v-if="selectedOwner"
              class="mb-2.5"
              :user-id="selectedOwner"
              :tooltip="false"
              size="36"
            />
            <div class="min-w-0 flex-1">
              <SelectField
                v-model="selectedOwner"
                :items="allUsers"
                item-title="fullName"
                item-value="id"
                :label="$t('general.owner')"
              />
            </div>
          </div>
          <p
            v-if="selectedOwnerHousehold"
            class="m-0 flex items-center gap-2 text-sm text-muted-foreground"
          >
            <MdiIcon
              :path="$globals.icons.household"
              class="size-4"
            />
            {{ selectedOwnerHousehold.name }}
          </p>
        </template>
      </div>
    </BaseDialog>

    <section class="flex flex-col gap-4">
      <header>
        <div class="flex items-baseline gap-3">
          <h2 class="m-0 text-xl font-bold tracking-tight">
            {{ $t('data-pages.recipes.recipe-data') }}
          </h2>
          <span class="text-sm text-muted-foreground tabular-nums">{{ allRecipes.length }}</span>
        </div>
        <p class="m-0 mt-1 max-w-[65ch] text-sm text-muted-foreground">
          {{ $t('data-pages.recipes.recipe-data-description') }}
        </p>
      </header>
      <RecipeDataTable
        v-model="selected"
        :loading="loading"
        :recipes="allRecipes"
        :show-headers="headers"
        :bulk-actions="actions"
        @bulk-action="onBulkAction"
      >
        <template #button-row>
          <Button
            variant="outline"
            @click="
              selectAll();
              openDialog(MODES.export);
            "
          >
            <MdiIcon
              :path="$globals.icons.database"
              class="size-4"
            />
            {{ $t('general.export-all') }}
          </Button>
        </template>
      </RecipeDataTable>
    </section>

    <section class="mt-12 flex flex-col gap-4">
      <header class="flex flex-wrap items-end gap-3">
        <div class="min-w-0 flex-1">
          <h2 class="m-0 text-xl font-bold tracking-tight">
            {{ $t('data-pages.recipes.data-exports') }}
          </h2>
          <p class="m-0 mt-1 max-w-[65ch] text-sm text-muted-foreground">
            {{ $t('data-pages.recipes.data-exports-description') }}
          </p>
        </div>
        <Button
          variant="outline"
          class="text-destructive hover:text-destructive"
          :disabled="!groupExports.length"
          @click="purgeExportsDialog = true"
        >
          <Trash2Icon class="size-4" />
          {{ $t('data-pages.recipes.purge-exports') }}
        </Button>
      </header>
      <GroupExportData :exports="groupExports" />
    </section>
  </div>
</template>

<script setup lang="ts">
import { Trash2Icon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import SelectField from "~/components/ui/field/SelectField.vue";
import { MdiIcon } from "~/components/ui/mdi-icon";
import RecipeDataTable from "~/components/Domain/Recipe/RecipeDataTable.vue";
import RecipeOrganizerSelector from "~/components/Domain/Recipe/RecipeOrganizerSelector.vue";
import { useUserApi } from "~/composables/api";
import { useRecipes, allRecipes } from "~/composables/recipes";
import type { RecipeSettings, RecipeSummary } from "~/lib/api/types/recipe";
import GroupExportData from "~/components/Domain/Group/GroupExportData.vue";
import type { GroupDataExport } from "~/lib/api/types/group";
import type { BulkAction } from "~/components/global/CrudTable.vue";
import RecipeSettingsSwitches from "~/components/Domain/Recipe/RecipeSettingsSwitches.vue";
import { useUserStore } from "~/composables/store/use-user-store";
import UserAvatar from "~/components/Domain/User/UserAvatar.vue";
import { useHouseholdStore } from "~/composables/store/use-household-store";

enum MODES {
  tag = "tag",
  category = "category",
  export = "export",
  delete = "delete",
  updateSettings = "updateSettings",
  changeOwner = "changeOwner",
}

definePageMeta({
  scrollToTop: true,
});

const i18n = useI18n();
const auth = useMealieAuth();
const { $globals } = useNuxtApp();

useSeoMeta({
  title: i18n.t("data-pages.recipes.recipe-data"),
});

const { refreshRecipes } = useRecipes(true, true, false, `householdId=${auth.user.value?.householdId || ""}`);
const selected = ref<RecipeSummary[]>([]);

function resetAll() {
  selected.value = [];
  toSetTags.value = [];
  toSetCategories.value = [];
  loading.value = false;
}

const headers = reactive({
  id: false,
  owner: false,
  tags: true,
  tools: true,
  categories: true,
  recipeServings: false,
  recipeYieldQuantity: false,
  recipeYield: false,
  dateAdded: false,
});

const actions: BulkAction[] = [
  {
    icon: $globals.icons.database,
    text: i18n.t("export.export"),
    event: "export-selected",
  },
  {
    icon: $globals.icons.tags,
    text: i18n.t("data-pages.recipes.tag"),
    event: "tag-selected",
  },
  {
    icon: $globals.icons.categories,
    text: i18n.t("data-pages.recipes.categorize"),
    event: "categorize-selected",
  },
  {
    icon: $globals.icons.cog,
    text: i18n.t("data-pages.recipes.update-settings"),
    event: "update-settings",
  },
  {
    icon: $globals.icons.user,
    text: i18n.t("general.change-owner"),
    event: "change-owner",
  },
  {
    icon: $globals.icons.delete,
    text: i18n.t("general.delete"),
    event: "delete-selected",
  },
];

const api = useUserApi();
const loading = ref(false);

// ===============================================================
// Group Exports

const purgeExportsDialog = ref(false);

async function purgeExports() {
  await api.bulk.purgeExports();
  refreshExports();
}

const groupExports = ref<GroupDataExport[]>([]);

async function refreshExports() {
  const { data } = await api.bulk.fetchExports();

  if (data) {
    groupExports.value = data;
  }
}

onMounted(async () => {
  await refreshExports();
});
// ===============================================================
// All Recipes

const BULK_MODES: Record<string, MODES> = {
  "export-selected": MODES.export,
  "tag-selected": MODES.tag,
  "categorize-selected": MODES.category,
  "update-settings": MODES.updateSettings,
  "change-owner": MODES.changeOwner,
  "delete-selected": MODES.delete,
};

function onBulkAction(event: string) {
  const mode = BULK_MODES[event];
  if (mode) {
    openDialog(mode);
  }
}

function selectAll() {
  selected.value = allRecipes.value;
}

async function exportSelected() {
  loading.value = true;
  await api.bulk.bulkExport({
    recipes: selected.value.map(x => x.slug),
    exportType: "json",
  });

  resetAll();
  refreshExports();
}

const toSetTags = ref([]);

async function tagSelected() {
  loading.value = true;

  const recipes = selected.value.map(x => x.slug);
  await api.bulk.bulkTag({ recipes, tags: toSetTags.value });
  await refreshRecipes();
  resetAll();
}

const toSetCategories = ref([]);

async function categorizeSelected() {
  loading.value = true;

  const recipes = selected.value.map(x => x.slug);
  await api.bulk.bulkCategorize({ recipes, categories: toSetCategories.value });
  await refreshRecipes();
  resetAll();
}

async function deleteSelected() {
  loading.value = true;

  const recipes = selected.value.map(x => x.slug);

  await api.bulk.bulkDelete({ recipes });

  await refreshRecipes();
  resetAll();
}

const recipeSettings = reactive<RecipeSettings>({
  public: false,
  showNutrition: false,
  showAssets: false,
  landscapeView: false,
  disableComments: false,
  locked: false,
});

async function updateSettings() {
  loading.value = true;

  const recipes = selected.value.map(x => x.slug);

  await api.bulk.bulkSetSettings({ recipes, settings: recipeSettings });

  await refreshRecipes();
  resetAll();
}

async function changeOwner() {
  if (!selected.value.length || !selectedOwner.value) {
    return;
  }

  selected.value.forEach((r) => {
    r.userId = selectedOwner.value;
  });

  loading.value = true;
  await api.recipes.patchMany(selected.value);

  await refreshRecipes();
  resetAll();
}

// ============================================================
// Dialog Management

const dialog = reactive({
  state: false,
  title: i18n.t("data-pages.recipes.tag-recipes"),
  mode: MODES.tag,
  tag: "",
  callback: () => {
    // Stub function to be overwritten
    return Promise.resolve();
  },
  icon: $globals.icons.tags,
});

function openDialog(mode: MODES) {
  const titles: Record<MODES, string> = {
    [MODES.tag]: i18n.t("data-pages.recipes.tag-recipes"),
    [MODES.category]: i18n.t("data-pages.recipes.categorize-recipes"),
    [MODES.export]: i18n.t("data-pages.recipes.export-recipes"),
    [MODES.delete]: i18n.t("data-pages.recipes.delete-recipes"),
    [MODES.updateSettings]: i18n.t("data-pages.recipes.update-settings"),
    [MODES.changeOwner]: i18n.t("general.change-owner"),
  };

  const callbacks: Record<MODES, () => Promise<void>> = {
    [MODES.tag]: tagSelected,
    [MODES.category]: categorizeSelected,
    [MODES.export]: exportSelected,
    [MODES.delete]: deleteSelected,
    [MODES.updateSettings]: updateSettings,
    [MODES.changeOwner]: changeOwner,
  };

  const icons: Record<MODES, string> = {
    [MODES.tag]: $globals.icons.tags,
    [MODES.category]: $globals.icons.categories,
    [MODES.export]: $globals.icons.database,
    [MODES.delete]: $globals.icons.delete,
    [MODES.updateSettings]: $globals.icons.cog,
    [MODES.changeOwner]: $globals.icons.user,
  };

  dialog.mode = mode;
  dialog.title = titles[mode];
  dialog.callback = callbacks[mode];
  dialog.icon = icons[mode];
  dialog.state = true;
}

const { store: allUsers } = useUserStore();
const { store: households } = useHouseholdStore();
const selectedOwner = ref("");
const selectedOwnerHousehold = computed(() => {
  if (!selectedOwner.value) {
    return null;
  }

  const owner = allUsers.value.find(u => u.id === selectedOwner.value);
  if (!owner) {
    return null;
  };

  return households.value.find(h => h.id === owner.householdId);
});
</script>
