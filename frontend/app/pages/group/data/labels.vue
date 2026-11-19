<template>
  <div>
    <!-- Merge Dialog -->
    <BaseDialog
      v-model="mergeDialog"
      :icon="$globals.icons.tags"
      :title="$t('data-pages.labels.combine-label')"
      can-confirm
      @confirm="mergeLabels"
      @close="resetMergeDialog"
    >
      <div class="flex flex-col gap-3 px-6 pb-2 text-[15px]">
        <div>
          {{ $t("data-pages.labels.merge-dialog-text") }}
        </div>
        <FilterSelect
          v-model="fromLabel"
          :items="labelStore.store.value"
          :label="$t('data-pages.labels.source-label')"
        />
        <FilterSelect
          v-model="toLabel"
          :items="labelStore.store.value"
          :label="$t('data-pages.labels.target-label')"
        />

        <template v-if="canMerge && fromLabel && toLabel">
          <div class="rounded-control bg-muted px-3 py-2 text-center text-sm">
            {{ $t("data-pages.labels.merge-label-example", { label1: fromLabel.name, label2: toLabel.name }) }}
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
        {{ $t('data-pages.labels.delete-unused-confirm', { count: unusedLabelIds.length }, unusedLabelIds.length) }}
        <ul class="m-0 ps-5 text-sm leading-7 text-muted-foreground">
          <li v-for="name in unusedLabelNamesPreview" :key="name">
            {{ name }}
          </li>
        </ul>
        <div v-if="unusedLabelNamesRemaining > 0" class="text-sm text-muted-foreground">
          {{ $t('data-pages.delete-unused-more', { count: unusedLabelNamesRemaining }) }}
        </div>
      </div>
    </BaseDialog>

    <GroupDataPage
      :icon="$globals.icons.tags"
      :title="$t('data-pages.labels.labels')"
      :create-title="$t('data-pages.labels.new-label')"
      :edit-title="$t('data-pages.labels.edit-label')"
      :table-headers="tableHeaders"
      :table-config="tableConfig"
      :data="labelStore.store.value || []"
      :bulk-actions="[{ icon: $globals.icons.delete, text: $t('general.delete'), event: 'delete-selected' }]"
      :create-form="createForm"
      :edit-form="editForm"
      @create-one="handleCreate"
      @edit-one="handleEdit"
      @delete-one="labelStore.actions.deleteOne"
      @bulk-action="handleBulkAction"
    >
      <template #[`item.name`]="{ item }">
        <MultiPurposeLabel
          v-if="item"
          :label="item"
        >
          {{ item.name }}
        </MultiPurposeLabel>
      </template>

      <template #create-dialog-top>
        <MultiPurposeLabel v-if="createForm.data.name" :label="createForm.data" class="my-2" />
      </template>

      <template #edit-dialog-top>
        <MultiPurposeLabel v-if="editForm.data.name" :label="editForm.data" class="my-2" />
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
import { validators } from "~/composables/use-validators";
import { useUserApi } from "~/composables/api";
import MultiPurposeLabel from "~/components/Domain/ShoppingList/MultiPurposeLabel.vue";
import { fieldTypes } from "~/composables/forms";
import type { MultiPurposeLabelOut, MultiPurposeLabelSummary } from "~/lib/api/types/labels";
import type { AutoFormItems } from "~/types/auto-forms";
import { alert } from "~/composables/use-toast";
import { useLabelStore } from "~/composables/store";
import type { TableHeaders, TableConfig } from "~/components/global/CrudTable.vue";

const userApi = useUserApi();
const i18n = useI18n();

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
];

const labelStore = useLabelStore();

// ============================================================
// Form items (shared)
const formItems: AutoFormItems = [
  {
    label: i18n.t("general.name"),
    varName: "name",
    type: fieldTypes.TEXT,
    rules: [validators.required],
  },
  {
    label: i18n.t("general.color"),
    varName: "color",
    type: fieldTypes.COLOR,
  },
];

// ============================================================
// Create
const createForm = reactive({
  items: formItems,
  data: {
    name: "",
    color: "",
  } as MultiPurposeLabelSummary,
});

async function handleCreate(createFormData: MultiPurposeLabelSummary) {
  await labelStore.actions.createOne(createFormData);
  createForm.data = { name: "", color: "#7417BE" } as MultiPurposeLabelSummary;
}

// ============================================================
// Edit
const editForm = reactive({
  items: formItems,
  data: {} as MultiPurposeLabelSummary,
});

async function handleEdit(editFormData: MultiPurposeLabelSummary) {
  await labelStore.actions.updateOne(editFormData);
  editForm.data = {} as MultiPurposeLabelSummary;
}

// ============================================================
// Bulk Actions
async function handleBulkAction(event: string, items: MultiPurposeLabelSummary[]) {
  if (event === "delete-selected") {
    const ids = items.filter(item => item.id != null).map(item => item.id!);
    await labelStore.actions.deleteMany(ids);
  }
}

// ============================================================
// Merge Labels
const mergeDialog = ref(false);
const fromLabel = ref<MultiPurposeLabelOut | null>(null);
const toLabel = ref<MultiPurposeLabelOut | null>(null);

const canMerge = computed(() => {
  return fromLabel.value && toLabel.value && fromLabel.value.id !== toLabel.value.id;
});

function resetMergeDialog() {
  fromLabel.value = null;
  toLabel.value = null;
}

async function mergeLabels() {
  if (!canMerge.value || !fromLabel.value?.id || !toLabel.value?.id) {
    return;
  }

  const { data } = await userApi.multiPurposeLabels.merge(fromLabel.value.id, toLabel.value.id);

  if (data) {
    fromLabel.value = null;
    toLabel.value = null;
    labelStore.actions.refresh();
  }
}

// ============================================================
// Delete Unused
const DELETE_UNUSED_PREVIEW_LIMIT = 10;

const deleteUnusedDialog = ref(false);
const unusedLabels = ref<MultiPurposeLabelOut[]>([]);
const unusedLabelIds = computed(() => unusedLabels.value.filter(l => l.id != null).map(l => l.id!));
const unusedLabelNamesPreview = computed(() => unusedLabels.value.slice(0, DELETE_UNUSED_PREVIEW_LIMIT).map(l => l.name));
const unusedLabelNamesRemaining = computed(() => Math.max(unusedLabels.value.length - DELETE_UNUSED_PREVIEW_LIMIT, 0));
const loadingEmpty = ref(false);

async function openDeleteUnusedDialog() {
  loadingEmpty.value = true;
  const { data } = await userApi.multiPurposeLabels.getEmpty();
  loadingEmpty.value = false;
  unusedLabels.value = data ?? [];

  if (unusedLabels.value.length === 0) {
    alert.info(i18n.t("data-pages.labels.no-unused-labels"));
    return;
  }

  deleteUnusedDialog.value = true;
}

async function confirmDeleteUnused() {
  await labelStore.actions.deleteMany(unusedLabelIds.value);
  unusedLabels.value = [];
}
</script>
