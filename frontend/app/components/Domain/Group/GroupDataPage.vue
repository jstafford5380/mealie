<template>
  <!-- Create Dialog -->
  <BaseDialog
    v-model="createDialog"
    :title="createTitle || $t('general.create')"
    :icon="icon"
    color="primary"
    max-width="600px"
    width="100%"
    :submit-disabled="!createFormValid"
    can-confirm
    @confirm="emit('create-one', createForm.data)"
  >
    <div class="px-4">
      <slot name="create-dialog-top" />
      <AutoForm
        v-model="createForm.data"
        v-model:is-valid="createFormValid"
        :items="createForm.items"
        class="py-2"
      />
    </div>
  </BaseDialog>

  <!-- Edit Dialog -->
  <BaseDialog
    v-model="editDialogModel"
    :title="editTitle || $t('general.edit')"
    :icon="icon"
    color="primary"
    max-width="600px"
    width="100%"
    :submit-disabled="!editFormValid"
    :loading="editSaving"
    :keep-open="keepEditOpen"
    :can-confirm="!keepEditOpen"
    :can-submit="keepEditOpen"
    :submit-text="$t('general.save')"
    @confirm="emit('edit-one', editForm.data)"
    @submit="emit('edit-one', editForm.data)"
  >
    <div
      class="px-4"
      :inert="editSaving"
    >
      <slot name="edit-dialog-top" />
      <AutoForm
        v-model="editForm.data"
        v-model:is-valid="editFormValid"
        :items="editForm.items"
        class="py-2"
      />
    </div>
    <template #custom-card-action>
      <slot
        v-if="!editSaving"
        name="edit-dialog-custom-action"
      />
    </template>
  </BaseDialog>

  <!-- Delete Dialog -->
  <BaseDialog
    v-model="deleteDialog"
    :title="$t('general.confirm')"
    :icon="$globals.icons.alertCircle"
    color="error"
    can-confirm
    @confirm="$emit('deleteOne', deleteTarget.id)"
  >
    <div class="flex flex-col gap-3 px-6 pb-2 text-[15px]">
      <p class="m-0">
        {{ $t("general.confirm-delete-generic") }}
      </p>
      <p
        v-if="deleteTarget"
        class="m-0 rounded-control bg-muted px-3 py-2 font-semibold"
      >
        {{ deleteTarget.name || deleteTarget.title || deleteTarget.id }}
      </p>
      <slot name="delete-dialog-bottom" />
    </div>
  </BaseDialog>

  <!-- Bulk Delete Dialog -->
  <BaseDialog
    v-model="bulkDeleteDialog"
    width="650px"
    :title="$t('general.confirm')"
    :icon="$globals.icons.alertCircle"
    color="error"
    can-confirm
    @confirm="$emit('bulk-action', 'delete-selected', bulkDeleteTarget)"
  >
    <div class="flex flex-col gap-3 px-6 pb-2 text-[15px]">
      <p class="m-0">
        {{ $t('general.confirm-delete-generic-items') }}
      </p>
      <ul class="m-0 max-h-[40vh] list-none overflow-y-auto rounded-control border p-0">
        <li
          v-for="item in bulkDeleteTarget"
          :key="item.id || item.name"
          class="border-b px-3 py-2 last:border-b-0"
        >
          {{ item.name || item.title || item.id }}
        </li>
      </ul>
      <slot name="delete-dialog-bottom" />
    </div>
  </BaseDialog>

  <section class="flex flex-col gap-4">
    <header class="flex items-baseline gap-3">
      <h2 class="m-0 text-xl font-bold tracking-tight">
        {{ title }}
      </h2>
      <span class="text-sm text-muted-foreground tabular-nums">{{ (data || []).length }}</span>
    </header>

    <CrudTable
      :headers="tableHeaders"
      :table-config="tableConfig"
      :data="data || []"
      :bulk-actions="bulkActions"
      :initial-sort="initialSort"
      @edit-one="editEventHandler"
      @delete-one="deleteEventHandler"
      @bulk-action="handleBulkAction"
    >
      <template
        v-for="slotName in itemSlotNames"
        #[slotName]="slotProps"
      >
        <slot
          :name="slotName"
          v-bind="slotProps"
        />
      </template>
      <template #button-row>
        <slot name="table-button-row" />
        <Button @click="createDialog = true">
          <PlusIcon class="size-4" />
          {{ createTitle || $t("general.create") }}
        </Button>
      </template>
      <template #button-bottom>
        <slot name="table-button-bottom" />
      </template>
    </CrudTable>
  </section>
</template>

<script setup lang="ts">
import { PlusIcon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import type { TableHeaders, TableConfig, BulkAction } from "~/components/global/CrudTable.vue";
import type { AutoFormItems } from "~/types/auto-forms";

const slots = useSlots();

const emit = defineEmits<{
  (e: "deleteOne", id: string): void;
  (e: "deleteMany", ids: string[]): void;
  (e: "create-one" | "edit-one", data: any): void;
  (e: "bulk-action", event: string, items: any[]): void;
}>();

const tableHeaders = defineModel<TableHeaders[]>("tableHeaders", { required: true });
const createForm = defineModel<{ items: AutoFormItems; data: Record<string, any> }>("createForm", { required: true });
const createDialog = defineModel("createDialog", { type: Boolean, default: false });

const editForm = defineModel<{ items: AutoFormItems; data: Record<string, any> }>("editForm", { required: true });
const editDialog = defineModel("editDialog", { type: Boolean, default: false });

const props = defineProps({
  icon: {
    type: String,
    required: true,
  },
  title: {
    type: String,
    required: true,
  },
  createTitle: {
    type: String,
  },
  editTitle: {
    type: String,
  },
  keepEditOpen: Boolean,
  editSaving: Boolean,
  tableConfig: {
    type: Object as PropType<TableConfig>,
    default: () => ({
      hideColumns: false,
      canExport: true,
    }),
  },
  data: {
    type: Array as PropType<Array<any>>,
    required: true,
  },
  bulkActions: {
    type: Array as PropType<BulkAction[]>,
    required: true,
  },
  initialSort: {
    type: String,
    default: "name",
  },
  onDeleteDialogOpen: {
    type: Function as PropType<(items: any[]) => Promise<void>>,
    default: null,
  },
});

const editDialogModel = computed({
  get: () => editDialog.value,
  set: (open) => {
    if (!props.editSaving) {
      editDialog.value = open;
    }
  },
});

// ============================================================
// Bulk Action Handler
function handleBulkAction(event: string, items: any[]) {
  if (event === "delete-selected") {
    bulkDeleteEventHandler(items);
    return;
  }
  emit("bulk-action", event, items);
}

// ============================================================
// Create & Edit
const createFormValid = ref(false);
const editFormValid = ref(false);
const itemSlotNames = computed(() => Object.keys(slots).filter(slotName => slotName.startsWith("item.")));
const editEventHandler = (item: any) => {
  editForm.value.data = { ...item };
  editDialog.value = true;
};

// ============================================================
// Delete Logic
const deleteTarget = ref<any>(null);
const deleteDialog = ref(false);

async function deleteEventHandler(item: any) {
  deleteTarget.value = item;
  if (props.onDeleteDialogOpen) {
    await props.onDeleteDialogOpen([item]);
  }
  deleteDialog.value = true;
}

// ============================================================
// Bulk Delete Logic
const bulkDeleteTarget = ref<Array<any>>([]);
const bulkDeleteDialog = ref(false);

async function bulkDeleteEventHandler(items: Array<any>) {
  bulkDeleteTarget.value = items;
  if (props.onDeleteDialogOpen) {
    await props.onDeleteDialogOpen(items);
  }
  bulkDeleteDialog.value = true;
}
</script>
