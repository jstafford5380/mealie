<template>
  <div>
    <!-- Merge Dialog -->
    <BaseDialog
      v-model="mergeDialog"
      :icon="$globals.icons.tools"
      :title="$t('data-pages.tools.combine-tool')"
      can-confirm
      @confirm="mergeTools"
      @close="resetMergeDialog"
    >
      <div class="flex flex-col gap-3 px-6 pb-2 text-[15px]">
        <div>
          {{ $t("data-pages.tools.merge-dialog-text") }}
        </div>
        <FilterSelect
          v-model="fromTool"
          :items="tools"
          :label="$t('data-pages.tools.source-tool')"
        />
        <FilterSelect
          v-model="toTool"
          :items="tools"
          :label="$t('data-pages.tools.target-tool')"
        />

        <template v-if="canMerge && fromTool && toTool">
          <div class="rounded-control bg-muted px-3 py-2 text-center text-sm">
            {{ $t("data-pages.tools.merge-tool-example", { tool1: fromTool.name, tool2: toTool.name }) }}
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
        {{ $t('data-pages.tools.delete-unused-confirm', { count: unusedToolIds.length }, unusedToolIds.length) }}
        <ul class="m-0 ps-5 text-sm leading-7 text-muted-foreground">
          <li v-for="name in unusedToolNamesPreview" :key="name">
            {{ name }}
          </li>
        </ul>
        <div v-if="unusedToolNamesRemaining > 0" class="text-sm text-muted-foreground">
          {{ $t('data-pages.delete-unused-more', { count: unusedToolNamesRemaining }) }}
        </div>
      </div>
    </BaseDialog>

    <GroupDataPage
      :icon="$globals.icons.tools"
      :title="$t('data-pages.tools.tool-data')"
      :create-title="$t('data-pages.tools.new-tool')"
      :edit-title="$t('data-pages.tools.edit-tool')"
      :table-headers="tableHeaders"
      :table-config="tableConfig"
      :data="tools || []"
      :bulk-actions="[{ icon: $globals.icons.delete, text: $t('general.delete'), event: 'delete-selected' }]"
      :create-form="createForm"
      :edit-form="editForm"
      @create-one="handleCreate"
      @edit-one="handleEdit"
      @delete-one="toolStore.actions.deleteOne"
      @bulk-action="handleBulkAction"
    >
      <template #[`item.recipeCount`]="{ item }">
        <NuxtLink v-if="groupSlug && item.recipeCount > 0" :to="`/g/${groupSlug}?tools=${item.id}`">{{ item.recipeCount }}</NuxtLink>
        <span v-else>{{ item.recipeCount || 0 }}</span>
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
import type { RecipeToolWithOnHand } from "~/composables/store/use-tool-store";
import { validators } from "~/composables/use-validators";
import { fieldTypes } from "~/composables/forms";
import { alert } from "~/composables/use-toast";
import type { AutoFormItems } from "~/types/auto-forms";
import { useToolStore } from "~/composables/store";
import { useUserApi } from "~/composables/api";
import type { ToolOut, ToolCreate } from "~/lib/api/types/recipe";
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
  {
    text: i18n.t("tool.on-hand"),
    value: "onHand",
    show: true,
    sortable: true,
  },
];

const userHousehold = computed(() => auth.user.value?.householdSlug || "");
const toolStore = useToolStore();
const tools = computed(() => toolStore.store.value.map((tool) => {
  const onHand = tool.householdsWithTool?.includes(userHousehold.value) || false;
  return { ...tool, onHand } as RecipeToolWithOnHand;
}));

onMounted(() => {
  toolStore.actions.refresh();
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
  {
    label: i18n.t("tool.on-hand"),
    varName: "onHand",
    type: fieldTypes.BOOLEAN,
  },
] as AutoFormItems;

// ============================================================
// Create
const createForm = reactive({
  items: formItems,
  data: { name: "", onHand: false } as ToolCreate,
});

async function handleCreate(createFormData: ToolCreate) {
  // @ts-expect-error createOne eroniusly expects id and slug which are not preset at time of creation
  await toolStore.actions.createOne({ name: createFormData.name, householdsWithTool: createFormData.onHand ? [userHousehold.value] : [] } as ToolCreate);
  createForm.data = { name: "", onHand: false } as ToolCreate;
}

// ============================================================
// Edit
const editForm = reactive({
  items: formItems,
  data: {} as RecipeToolWithOnHand,
});

async function handleEdit(editFormData: RecipeToolWithOnHand) {
  // if list of households is undefined default to empty array
  if (!editFormData.householdsWithTool) {
    editFormData.householdsWithTool = [];
  }

  if (editFormData.onHand && !editFormData.householdsWithTool.includes(userHousehold.value)) {
    editFormData.householdsWithTool.push(userHousehold.value);
  }
  else if (!editFormData.onHand && editFormData.householdsWithTool.includes(userHousehold.value)) {
    const idx = editFormData.householdsWithTool.indexOf(userHousehold.value);
    if (idx !== -1) editFormData.householdsWithTool.splice(idx, 1);
  }

  await toolStore.actions.updateOne({ ...editFormData, id: editFormData.id } as ToolOut);
  editForm.data = {} as RecipeToolWithOnHand;
}

// ============================================================
// Bulk Actions
async function handleBulkAction(event: string, items: RecipeToolWithOnHand[]) {
  if (event === "delete-selected") {
    const ids = items.map(item => item.id);
    await toolStore.actions.deleteMany(ids);
  }
}

// ============================================================
// Merge Tools
const mergeDialog = ref(false);
const fromTool = ref<RecipeToolWithOnHand | null>(null);
const toTool = ref<RecipeToolWithOnHand | null>(null);

const canMerge = computed(() => {
  return fromTool.value && toTool.value && fromTool.value.id !== toTool.value.id;
});

function resetMergeDialog() {
  fromTool.value = null;
  toTool.value = null;
}

async function mergeTools() {
  if (!canMerge.value || !fromTool.value?.id || !toTool.value?.id) {
    return;
  }

  const { data } = await userApi.tools.merge(fromTool.value.id, toTool.value.id);

  if (data) {
    fromTool.value = null;
    toTool.value = null;
    toolStore.actions.refresh();
  }
}

// ============================================================
// Delete Unused
const DELETE_UNUSED_PREVIEW_LIMIT = 10;

const deleteUnusedDialog = ref(false);
const unusedTools = ref<ToolOut[]>([]);
const unusedToolIds = computed(() => unusedTools.value.filter(t => t.id != null).map(t => t.id!));
const unusedToolNamesPreview = computed(() => unusedTools.value.slice(0, DELETE_UNUSED_PREVIEW_LIMIT).map(t => t.name));
const unusedToolNamesRemaining = computed(() => Math.max(unusedTools.value.length - DELETE_UNUSED_PREVIEW_LIMIT, 0));
const loadingEmpty = ref(false);

async function openDeleteUnusedDialog() {
  loadingEmpty.value = true;
  const { data } = await userApi.tools.getEmpty();
  loadingEmpty.value = false;
  unusedTools.value = data ?? [];

  if (unusedTools.value.length === 0) {
    alert.info(i18n.t("data-pages.tools.no-unused-tools"));
    return;
  }

  deleteUnusedDialog.value = true;
}

async function confirmDeleteUnused() {
  await toolStore.actions.deleteMany(unusedToolIds.value);
  unusedTools.value = [];
}
</script>
