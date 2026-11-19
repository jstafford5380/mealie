<template>
  <div>
    <!-- Merge Dialog -->
    <BaseDialog
      v-model="mergeDialog"
      bottom-sheet
      :icon="$globals.icons.categories"
      :title="$t('data-pages.categories.combine-category')"
      can-confirm
      @confirm="mergeCategories"
      @close="resetMergeDialog"
    >
      <div class="flex flex-col gap-3 px-6 pb-2 text-[15px]">
        <div>
          {{ $t("data-pages.categories.merge-dialog-text") }}
        </div>
        <FilterSelect
          v-model="fromCategory"
          :items="categoryStore.store.value"
          :label="$t('data-pages.categories.source-category')"
        />
        <FilterSelect
          v-model="toCategory"
          :items="categoryStore.store.value"
          :label="$t('data-pages.categories.target-category')"
        />

        <template v-if="canMerge && fromCategory && toCategory">
          <div class="rounded-control bg-muted px-3 py-2 text-center text-sm">
            {{ $t("data-pages.categories.merge-category-example", { category1: fromCategory.name, category2: toCategory.name }) }}
          </div>
        </template>
      </div>
    </BaseDialog>

    <!-- Delete Unused Dialog -->
    <BaseDialog
      v-model="deleteUnusedDialog"
      bottom-sheet
      :title="$t('general.confirm')"
      :icon="$globals.icons.alertCircle"
      color="error"
      can-confirm
      @confirm="confirmDeleteUnused"
    >
      <div class="flex flex-col gap-3 px-6 pb-2 text-[15px]">
        {{ $t('data-pages.categories.delete-unused-confirm', { count: unusedCategoryIds.length }, unusedCategoryIds.length) }}
        <ul class="m-0 ps-5 text-sm leading-7 text-muted-foreground">
          <li v-for="name in unusedCategoryNamesPreview" :key="name">
            {{ name }}
          </li>
        </ul>
        <div v-if="unusedCategoryNamesRemaining > 0" class="text-sm text-muted-foreground">
          {{ $t('data-pages.delete-unused-more', { count: unusedCategoryNamesRemaining }) }}
        </div>
      </div>
    </BaseDialog>

    <GroupDataPage
      :icon="$globals.icons.categories"
      :title="$t('data-pages.categories.category-data')"
      :create-title="$t('data-pages.categories.new-category')"
      :edit-title="$t('data-pages.categories.edit-category')"
      :table-headers="tableHeaders"
      :table-config="tableConfig"
      :data="categoryStore.store.value || []"
      :bulk-actions="[{ icon: $globals.icons.delete, text: $t('general.delete'), event: 'delete-selected' }]"
      :create-form="createForm"
      :edit-form="editForm"
      @create-one="handleCreate"
      @edit-one="handleEdit"
      @delete-one="categoryStore.actions.deleteOne"
      @bulk-action="handleBulkAction"
    >
      <template #[`item.recipeCount`]="{ item }">
        <NuxtLink v-if="groupSlug && item.recipeCount > 0" :to="`/g/${groupSlug}?categories=${item.id}`">{{ item.recipeCount }}</NuxtLink>
        <span v-else>{{ item.recipeCount || 0 }}</span>
      </template>

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
    </GroupDataPage>
  </div>
</template>

<script setup lang="ts">
import FilterSelect from "~/components/ui/field/FilterSelect.vue";
import { Button } from "~/components/ui/button";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { useCategoryStore } from "~/composables/store";
import { useUserApi } from "~/composables/api";
import { validators } from "~/composables/use-validators";
import { fieldTypes } from "~/composables/forms";
import { alert } from "~/composables/use-toast";
import type { AutoFormItems } from "~/types/auto-forms";
import type { CategoryOut } from "~/lib/api/types/recipe";
import type { TableHeaders, TableConfig } from "~/components/global/CrudTable.vue";

const i18n = useI18n();
const auth = useMealieAuth();
const groupSlug = computed(() => auth.user.value?.groupSlug || "");
const userApi = useUserApi();

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
    text: i18n.t("data-pages.recipe-count"),
    value: "recipeCount",
    show: true,
    sortable: true,
  },
];
const categoryStore = useCategoryStore();

onMounted(() => {
  categoryStore.actions.refresh();
});

// ============================================================
// Form items (shared)
const formItems = [
  {
    label: i18n.t("general.name"),
    varName: "name",
    type: fieldTypes.TEXT,
    rules: [validators.required],
  },
] as AutoFormItems;

// ============================================================
// Create
const createForm = reactive({
  items: formItems,
  data: { name: "" } as CategoryOut,
});

async function handleCreate(createFormData: CategoryOut) {
  await categoryStore.actions.createOne(createFormData);
  createForm.data.name = "";
}

// ============================================================
// Edit
const editForm = reactive({
  items: formItems,
  data: {} as CategoryOut,
});

async function handleEdit(editFormData: CategoryOut) {
  await categoryStore.actions.updateOne(editFormData);
  editForm.data = {} as CategoryOut;
}

// ============================================================
// Bulk Actions
async function handleBulkAction(event: string, items: CategoryOut[]) {
  if (event === "delete-selected") {
    const ids = items.map(item => item.id);
    await categoryStore.actions.deleteMany(ids);
  }
}

// ============================================================
// Merge Categories
const mergeDialog = ref(false);
const fromCategory = ref<CategoryOut | null>(null);
const toCategory = ref<CategoryOut | null>(null);

const canMerge = computed(() => {
  return fromCategory.value && toCategory.value && fromCategory.value.id !== toCategory.value.id;
});

function resetMergeDialog() {
  fromCategory.value = null;
  toCategory.value = null;
}

async function mergeCategories() {
  if (!canMerge.value || !fromCategory.value?.id || !toCategory.value?.id) {
    return;
  }

  const { data } = await userApi.categories.merge(fromCategory.value.id, toCategory.value.id);

  if (data) {
    fromCategory.value = null;
    toCategory.value = null;
    categoryStore.actions.refresh();
  }
}

// ============================================================
// Delete Unused
const DELETE_UNUSED_PREVIEW_LIMIT = 10;

const deleteUnusedDialog = ref(false);
const unusedCategories = ref<CategoryOut[]>([]);
const unusedCategoryIds = computed(() => unusedCategories.value.filter(c => c.id != null).map(c => c.id!));
const unusedCategoryNamesPreview = computed(() =>
  unusedCategories.value.slice(0, DELETE_UNUSED_PREVIEW_LIMIT).map(c => c.name),
);
const unusedCategoryNamesRemaining = computed(() =>
  Math.max(unusedCategories.value.length - DELETE_UNUSED_PREVIEW_LIMIT, 0),
);
const loadingEmpty = ref(false);

async function openDeleteUnusedDialog() {
  loadingEmpty.value = true;
  const { data } = await userApi.categories.getEmpty();
  loadingEmpty.value = false;
  unusedCategories.value = data ?? [];

  if (unusedCategories.value.length === 0) {
    alert.info(i18n.t("data-pages.categories.no-unused-categories"));
    return;
  }

  deleteUnusedDialog.value = true;
}

async function confirmDeleteUnused() {
  await categoryStore.actions.deleteMany(unusedCategoryIds.value);
  unusedCategories.value = [];
}
</script>
