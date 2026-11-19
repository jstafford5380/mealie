<template>
  <div>
    <!-- Merge Dialog -->
    <BaseDialog
      v-model="mergeDialog"
      bottom-sheet
      :icon="$globals.icons.foods"
      :title="$t('data-pages.foods.combine-food')"
      can-confirm
      @confirm="mergeFoods"
      @close="resetMergeDialog"
    >
      <div class="flex flex-col gap-3 px-6 pb-2 text-[15px]">
        <div>
          {{ $t("data-pages.foods.merge-dialog-text") }}
        </div>
        <FilterSelect
          v-model="fromFood"
          :items="foods"
          :label="$t('data-pages.foods.source-food')"
        />
        <FilterSelect
          v-model="toFood"
          :items="foods"
          :label="$t('data-pages.foods.target-food')"
        />

        <template v-if="canMerge && fromFood && toFood">
          <div class="rounded-control bg-muted px-3 py-2 text-center text-sm">
            {{ $t("data-pages.foods.merge-food-example", { food1: fromFood.name, food2: toFood.name }) }}
          </div>
        </template>
      </div>
    </BaseDialog>

    <!-- Delete Unused Dialog -->
    <BaseDialog
      v-model="deleteUnusedDialog"
      :title="$t('general.confirm')"
      :icon="$globals.icons.alertCircle"
      color="error"
      can-confirm
      @confirm="confirmDeleteUnused"
    >
      <div class="flex flex-col gap-3 px-6 pb-2 text-[15px]">
        {{ $t('data-pages.foods.delete-unused-confirm', { count: unusedFoodIds.length }, unusedFoodIds.length) }}
        <ul class="m-0 ps-5 text-sm leading-7 text-muted-foreground">
          <li v-for="name in unusedFoodNamesPreview" :key="name">
            {{ name }}
          </li>
        </ul>
        <div v-if="unusedFoodNamesRemaining > 0" class="text-sm text-muted-foreground">
          {{ $t('data-pages.delete-unused-more', { count: unusedFoodNamesRemaining }) }}
        </div>
      </div>
    </BaseDialog>

    <!-- Seed Dialog -->
    <BaseDialog
      v-model="seedDialog"
      bottom-sheet
      :icon="$globals.icons.foods"
      :title="$t('data-pages.seed-data')"
      can-confirm
      @confirm="seedDatabase"
    >
      <div class="flex flex-col gap-3 px-6 pb-2 text-[15px]">
        <div class="pb-2">
          {{ $t("data-pages.foods.seed-dialog-text") }}
        </div>
        <FilterSelect
          v-model="locale"
          :items="locales"
          item-value="value"
          item-key="value"
          :clearable="false"
          :label="$t('data-pages.select-language')"
        >
          <template #item="{ item }">
            <span class="flex items-baseline justify-between gap-3">
              <span class="truncate">{{ item.name }}</span>
              <span class="shrink-0 text-xs text-muted-foreground">{{ item.progress }}% {{ $t("language-dialog.translated") }}</span>
            </span>
          </template>
        </FilterSelect>

        <p
          v-if="foods && foods.length > 0"
          class="m-0 rounded-control border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
        >
          {{ $t("data-pages.foods.seed-dialog-warning") }}
        </p>
      </div>
    </BaseDialog>

    <!-- Alias Sub-Dialog -->
    <RecipeDataAliasManagerDialog
      v-if="editForm.data"
      v-model="aliasManagerDialog"
      :data="editForm.data"
      @submit="updateFoodAlias"
      @cancel="aliasManagerDialog = false"
    />

    <!-- Substitution Sub-Dialog -->
    <RecipeDataSubstitutionManagerDialog
      v-if="editForm.data"
      v-model="substitutionManagerDialog"
      :data="editForm.data"
      @submit="updateFoodSubstitutions"
      @cancel="substitutionManagerDialog = false"
    />

    <!-- Bulk Assign Labels Dialog -->
    <BaseDialog
      v-model="bulkAssignLabelDialog"
      bottom-sheet
      :title="$t('data-pages.labels.assign-label')"
      :icon="$globals.icons.tags"
      can-confirm
      @confirm="assignSelected"
    >
      <div class="flex flex-col gap-3 px-6 pb-2 text-[15px]">
        <p class="m-0 rounded-control border border-brand/50 bg-brand/10 px-3 py-2 text-sm">
          <strong>{{ $t("general.caution") }}:</strong> {{ $t("data-pages.foods.label-overwrite-warning") }}
        </p>

        <FilterSelect
          v-model="bulkAssignLabelId"
          clearable
          :items="allLabels"
          item-value="id"
          :label="$t('data-pages.foods.food-label')"
        />
        <p class="m-0 text-sm font-semibold">
          {{ $t('data-pages.selected-count', bulkAssignTarget.length) }}
        </p>
        <ul class="m-0 max-h-[40vh] list-none overflow-y-auto rounded-control border p-0">
          <li
            v-for="item in bulkAssignTarget"
            :key="item.id"
            class="border-b px-3 py-2 last:border-b-0"
          >
            {{ item.name }}
          </li>
        </ul>
      </div>
    </BaseDialog>

    <GroupDataPage
      :icon="$globals.icons.foods"
      :title="$t('data-pages.foods.food-data')"
      :create-title="$t('data-pages.foods.create-food')"
      :edit-title="$t('data-pages.foods.edit-food')"
      :table-headers="tableHeaders"
      :table-config="tableConfig"
      :data="foods || []"
      :bulk-actions="[
        { icon: $globals.icons.delete, text: $t('general.delete'), event: 'delete-selected' },
        { icon: $globals.icons.tags, text: $t('data-pages.labels.assign-label'), event: 'assign-selected' },
      ]"
      :create-form="createForm"
      :edit-form="editForm"
      :on-delete-dialog-open="onDeleteDialogOpen"
      @create-one="handleCreate"
      @edit-one="handleEdit"
      @delete-one="foodStore.actions.deleteOne"
      @bulk-action="handleBulkAction"
    >
      <template #table-button-row>
        <Button
          variant="outline"
          @click="mergeDialog = true"
        >
          <MdiIcon
            :path="$globals.icons.externalLink"
            class="size-4"
          />
          {{ $t("data-pages.combine") }}
        </Button>

        <Button
          variant="outline"
          :disabled="loadingEmpty"
          @click="openDeleteUnusedDialog"
        >
          <MdiIcon
            :path="$globals.icons.broom"
            class="size-4"
          />
          {{ $t("data-pages.delete-unused") }}
        </Button>
      </template>

      <template #[`item.recipeCount`]="{ item }">
        <NuxtLink v-if="userGroup && item.recipeCount > 0" :to="`/g/${userGroup}?foods=${item.id}`">{{ item.recipeCount }}</NuxtLink>
        <span v-else>{{ item.recipeCount || 0 }}</span>
      </template>

      <template #[`item.label`]="{ item }">
        <MultiPurposeLabel v-if="item.label" :label="item.label">
          {{ item.label.name }}
        </MultiPurposeLabel>
      </template>

      <template #[`item.onHand`]="{ item }">
        <MdiIcon
          v-if="item.onHand"
          :path="$globals.icons.check"
          class="size-5 text-primary"
          :aria-label="$t('general.yes')"
        />
        <span
          v-else
          class="text-muted-foreground"
          :aria-label="$t('general.no')"
        >–</span>
      </template>

      <template #[`item.substitutions`]="{ item }">
        {{ item.substitutions ? item.substitutions.length : 0 }}
      </template>

      <template #[`item.createdAt`]="{ item }">
        {{ item.createdAt ? $d(new Date(item.createdAt)) : "" }}
      </template>

      <template #table-button-bottom>
        <Button
          variant="ghost"
          @click="seedDialog = true"
        >
          <MdiIcon
            :path="$globals.icons.database"
            class="size-4"
          />
          {{ $t("data-pages.seed") }}
        </Button>
      </template>

      <template #edit-dialog-custom-action>
        <BaseButton edit @click="aliasManagerDialog = true">
          {{ $t("data-pages.manage-aliases") }}
        </BaseButton>
        <BaseButton edit @click="substitutionManagerDialog = true">
          {{ $t("data-pages.foods.manage-substitutions") }}
        </BaseButton>
      </template>

      <template #delete-dialog-bottom>
        <div v-if="affectedRecipes.length > 0" class="rounded-control border border-brand/50 bg-brand/10 px-3 py-2 text-sm">
          {{ $t("data-pages.foods.delete-affects-recipes", { count: affectedRecipesTotal }) }}
          <ul class="m-0 mt-1 ps-5">
            <li v-for="recipe in affectedRecipes.slice(0, 5)" :key="recipe.slug">
              <NuxtLink :to="recipe.url" class="text-primary">{{ recipe.name }}</NuxtLink>
            </li>
          </ul>
          <NuxtLink
            v-if="affectedRecipesTotal > 5"
            :to="affectedRecipesMoreLink"
            class="mt-1 inline-block font-semibold text-primary"
          >
            {{ $t("data-pages.foods.delete-affects-recipes-more", { count: affectedRecipesTotal }) }}
          </NuxtLink>
        </div>
      </template>
    </GroupDataPage>
  </div>
</template>

<script setup lang="ts">
import FilterSelect from "~/components/ui/field/FilterSelect.vue";
import { Button } from "~/components/ui/button";
import { MdiIcon } from "~/components/ui/mdi-icon";
import type { LocaleObject } from "@nuxtjs/i18n";
import RecipeDataAliasManagerDialog from "~/components/Domain/Recipe/RecipeDataAliasManagerDialog.vue";
import RecipeDataSubstitutionManagerDialog from "~/components/Domain/Recipe/RecipeDataSubstitutionManagerDialog.vue";
import type { ReverseSubstitutionChanges } from "~/components/Domain/Recipe/RecipeDataSubstitutionManagerDialog.vue";
import { validators } from "~/composables/use-validators";
import { useUserApi } from "~/composables/api";
import type {
  IngredientFoodCreate,
  IngredientFoodOut,
  IngredientFoodAlias,
  IngredientFoodSubstitution,
} from "~/lib/api/types/recipe";
import MultiPurposeLabel from "~/components/Domain/ShoppingList/MultiPurposeLabel.vue";
import { useLocales } from "~/composables/use-locales";
import { alert } from "~/composables/use-toast";
import { useFoodStore, useLabelStore } from "~/composables/store";
import type { MultiPurposeLabelOut } from "~/lib/api/types/labels";
import type { AutoFormItems } from "~/types/auto-forms";
import type { TableHeaders, TableConfig } from "~/components/global/CrudTable.vue";
import { fieldTypes } from "~/composables/forms";

interface CreateIngredientFoodWithOnHand extends IngredientFoodCreate {
  onHand: boolean;
  householdsWithIngredientFood: string[];
}

interface IngredientFoodWithOnHand extends IngredientFoodOut {
  onHand: boolean;
}

const userApi = useUserApi();
const i18n = useI18n();
const auth = useMealieAuth();
const tableConfig: TableConfig = {
  hideColumns: true,
  canExport: true,
};
const tableHeaders: TableHeaders[] = [
  {
    text: i18n.t("general.id"),
    value: "id",
    show: false,
  },
  {
    text: i18n.t("general.name"),
    value: "name",
    show: true,
    sortable: true,
  },
  {
    text: i18n.t("general.plural-name"),
    value: "pluralName",
    show: true,
    sortable: true,
  },
  {
    text: i18n.t("recipe.description"),
    value: "description",
    show: true,
  },
  {
    text: i18n.t("data-pages.recipe-count"),
    value: "recipeCount",
    show: true,
    sortable: true,
  },
  {
    text: i18n.t("shopping-list.label"),
    value: "label",
    show: true,
    sortable: true,
    sort: (label1: MultiPurposeLabelOut | null, label2: MultiPurposeLabelOut | null) => {
      const label1Name = label1?.name || "";
      const label2Name = label2?.name || "";
      return label1Name.localeCompare(label2Name);
    },
  },
  {
    text: i18n.t("tool.on-hand"),
    value: "onHand",
    show: true,
    sortable: true,
  },
  {
    text: i18n.t("data-pages.foods.substitutions"),
    value: "substitutions",
    show: true,
    sortable: true,
    sort: (subs1: IngredientFoodSubstitution[] | null, subs2: IngredientFoodSubstitution[] | null) => {
      return (subs1?.length || 0) - (subs2?.length || 0);
    },
  },
  {
    text: i18n.t("general.date-added"),
    value: "createdAt",
    show: false,
    sortable: true,
  },
];

const userHousehold = computed(() => auth.user.value?.householdSlug || "");
const userGroup = computed(() => auth.user.value?.groupSlug || "");
const foodStore = useFoodStore();
const foods = computed(() =>
  foodStore.store.value.map((food) => {
    const onHand = food.householdsWithIngredientFood?.includes(userHousehold.value) || false;
    return { ...food, onHand } as IngredientFoodWithOnHand;
  }),
);

onMounted(() => {
  foodStore.actions.refresh();
});

// ============================================================
// Labels
const labelStore = useLabelStore();
const { store: allLabels } = labelStore;
const labelOptions = computed(() => allLabels.value.map(label => ({ text: label.name, value: label.id })) || []);

// ============================================================
// Form items (shared)
const formItems = computed<AutoFormItems>(() => [
  {
    label: i18n.t("general.name"),
    varName: "name",
    type: fieldTypes.TEXT,
    rules: [validators.required],
  },
  {
    label: i18n.t("general.plural-name"),
    varName: "pluralName",
    type: fieldTypes.TEXT,
  },
  {
    label: i18n.t("recipe.description"),
    varName: "description",
    type: fieldTypes.TEXT,
  },
  {
    label: i18n.t("data-pages.foods.food-label"),
    varName: "labelId",
    type: fieldTypes.SELECT,
    options: labelOptions.value,
    selectReturnValue: "value",
  },
  {
    label: i18n.t("tool.on-hand"),
    varName: "onHand",
    type: fieldTypes.BOOLEAN,
    hint: i18n.t("data-pages.foods.on-hand-checkbox-label"),
  },
]);

// ===============================================================
// Create

const createForm = reactive({
  get items() {
    return formItems.value;
  },
  data: { name: "", onHand: false, householdsWithIngredientFood: [] } as CreateIngredientFoodWithOnHand,
});

async function handleCreate() {
  if (!createForm.data || !createForm.data.name) {
    return;
  }

  if (createForm.data.onHand) {
    createForm.data.householdsWithIngredientFood = [userHousehold.value];
  }

  // @ts-expect-error the createOne function erroneously expects an id because it uses the IngredientFood type
  await foodStore.actions.createOne(createForm.data);
  createForm.data = {
    name: "",
    onHand: false,
    householdsWithIngredientFood: [],
  };
}

// ===============================================================
// Edit

const editForm = reactive({
  get items() {
    return formItems.value;
  },
  data: {} as IngredientFoodWithOnHand,
});

async function handleEdit() {
  if (!editForm.data) {
    return;
  }
  if (!editForm.data.householdsWithIngredientFood) {
    editForm.data.householdsWithIngredientFood = [];
  }

  const foodId = editForm.data.id;

  if (editForm.data.onHand && !editForm.data.householdsWithIngredientFood.includes(userHousehold.value)) {
    editForm.data.householdsWithIngredientFood.push(userHousehold.value);
  }
  else if (!editForm.data.onHand && editForm.data.householdsWithIngredientFood.includes(userHousehold.value)) {
    const idx = editForm.data.householdsWithIngredientFood.indexOf(userHousehold.value);
    if (idx !== -1) editForm.data.householdsWithIngredientFood.splice(idx, 1);
  }

  await foodStore.actions.updateOne(editForm.data);
  editForm.data = {} as IngredientFoodWithOnHand;
  await applyReverseSubstitutions(foodId);
}

// ============================================================
// Bulk Actions
async function handleBulkAction(event: string, items: IngredientFoodWithOnHand[]) {
  if (event === "delete-selected") {
    const ids = items.map(item => item.id);
    await foodStore.actions.deleteMany(ids);
    affectedRecipes.value = [];
    affectedRecipesTotal.value = 0;
    affectedRecipesMoreLink.value = "";
  }
  else if (event === "assign-selected") {
    bulkAssignEventHandler(items);
  }
}

// ============================================================
// Alias Manager

const aliasManagerDialog = ref(false);
function updateFoodAlias(newAliases: IngredientFoodAlias[]) {
  if (!editForm.data) {
    return;
  }
  editForm.data.aliases = newAliases;
  aliasManagerDialog.value = false;
}

// ============================================================
// Substitution Manager

const substitutionManagerDialog = ref(false);

// reverse substitutions live on other foods, so they can't ride along with the food being edited.
// they're held until the edit is confirmed, and tagged with the food they were built for so
// a cancelled edit can't leak them onto the next food the user opens
const pendingReverseSubstitutions = ref<({ foodId: string } & ReverseSubstitutionChanges) | null>(null);

function updateFoodSubstitutions(
  newSubstitutions: IngredientFoodSubstitution[],
  reverseChanges: ReverseSubstitutionChanges,
) {
  if (!editForm.data) {
    return;
  }
  editForm.data.substitutions = newSubstitutions;
  pendingReverseSubstitutions.value = reverseChanges.add.length || reverseChanges.remove.length
    ? { foodId: editForm.data.id, ...reverseChanges }
    : null;
  substitutionManagerDialog.value = false;
}

async function applyReverseSubstitutions(foodId: string) {
  const pending = pendingReverseSubstitutions.value;
  pendingReverseSubstitutions.value = null;
  if (!pending || !foodId || pending.foodId !== foodId) {
    return;
  }

  let updated = false;
  for (const reverseFoodId of [...pending.add, ...pending.remove]) {
    const reverseFood = foodStore.store.value.find(food => food.id === reverseFoodId);
    if (!reverseFood) {
      continue;
    }

    // rebuilt from what's on the other food right now, so a stale dialog can't resurrect
    // a row someone else removed in the meantime
    const others = (reverseFood.substitutions || []).filter(sub => sub.substituteFoodId !== foodId);
    const substitutions = pending.add.includes(reverseFoodId)
      ? [...others, { substituteFoodId: foodId }]
      : others;

    if (substitutions.length === (reverseFood.substitutions || []).length) {
      continue;
    }

    const payload = { ...reverseFood, substitutions };
    await userApi.foods.updateOne(reverseFoodId, payload);
    updated = true;
  }

  if (updated) {
    await foodStore.actions.refresh();
  }
}

// ============================================================
// Delete Foods

// fetch affected recipes before confirming deletion
const affectedRecipes = ref<{ name: string; slug: string; url: string }[]>([]);
const affectedRecipesTotal = ref(0);
const affectedRecipesMoreLink = ref("");

async function onDeleteDialogOpen(items: IngredientFoodWithOnHand[]) {
  const ids = items.map(item => item.id);
  const { data } = await userApi.recipes.search({ foods: ids, perPage: 5 });
  affectedRecipes.value = (data?.items ?? []).map(r => ({
    name: r.name,
    slug: r.slug,
    url: `/g/${userGroup.value}/r/${r.slug}`,
  }));
  affectedRecipesTotal.value = data?.total ?? 0;
  affectedRecipesMoreLink.value = `/g/${userGroup.value}?${ids.map(id => `foods=${id}`).join("&")}`;
}

// ============================================================
// Merge Foods

const mergeDialog = ref(false);
const fromFood = ref<IngredientFoodWithOnHand | null>(null);
const toFood = ref<IngredientFoodWithOnHand | null>(null);

const canMerge = computed(() => {
  return fromFood.value && toFood.value && fromFood.value.id !== toFood.value.id;
});

function resetMergeDialog() {
  fromFood.value = null;
  toFood.value = null;
}

async function mergeFoods() {
  if (!canMerge.value || !fromFood.value || !toFood.value) {
    return;
  }

  const { data } = await userApi.foods.merge(fromFood.value.id, toFood.value.id);

  if (data) {
    foodStore.actions.refresh();
  }
}

// ============================================================
// Delete Unused
const DELETE_UNUSED_PREVIEW_LIMIT = 10;

const deleteUnusedDialog = ref(false);
const unusedFoods = ref<IngredientFoodWithOnHand[]>([]);
const unusedFoodIds = computed(() => unusedFoods.value.filter(f => f.id != null).map(f => f.id!));
const unusedFoodNamesPreview = computed(() => unusedFoods.value.slice(0, DELETE_UNUSED_PREVIEW_LIMIT).map(f => f.name));
const unusedFoodNamesRemaining = computed(() => Math.max(unusedFoods.value.length - DELETE_UNUSED_PREVIEW_LIMIT, 0));
const loadingEmpty = ref(false);

async function openDeleteUnusedDialog() {
  loadingEmpty.value = true;
  const { data } = await userApi.foods.getEmpty();
  loadingEmpty.value = false;
  unusedFoods.value = (data ?? []) as IngredientFoodWithOnHand[];

  if (unusedFoods.value.length === 0) {
    alert.info(i18n.t("data-pages.foods.no-unused-foods"));
    return;
  }

  deleteUnusedDialog.value = true;
}

async function confirmDeleteUnused() {
  await foodStore.actions.deleteMany(unusedFoodIds.value);
  unusedFoods.value = [];
}

// ============================================================
// Seed

const seedDialog = ref(false);
const locale = ref("");

const { locales: LOCALES, locale: currentLocale } = useLocales();

onMounted(() => {
  locale.value = currentLocale.value;
  foodStore.actions.refresh();
});

const locales = LOCALES.filter(locale =>
  (i18n.locales.value as LocaleObject[]).map(i18nLocale => i18nLocale.code).includes(locale.value as any),
);

async function seedDatabase() {
  const { data } = await userApi.seeders.foods({ locale: locale.value });

  if (data) {
    // seeding foods also creates the labels that group them
    foodStore.actions.refresh();
    labelStore.actions.refresh();
  }
}

// ============================================================
// Bulk Assign Labels
const bulkAssignLabelDialog = ref(false);
const bulkAssignTarget = ref<IngredientFoodWithOnHand[]>([]);
const bulkAssignLabelId = ref<string | undefined>();

function bulkAssignEventHandler(selection: IngredientFoodWithOnHand[]) {
  bulkAssignTarget.value = selection;
  bulkAssignLabelDialog.value = true;
}

async function assignSelected() {
  if (!bulkAssignLabelId.value) {
    return;
  }
  for (const item of bulkAssignTarget.value) {
    item.labelId = bulkAssignLabelId.value;
    await foodStore.actions.updateOne(item);
  }
  bulkAssignTarget.value = [];
  bulkAssignLabelId.value = undefined;
  foodStore.actions.refresh();
}
</script>
