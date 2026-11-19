<template>
  <div class="mx-auto flex w-full max-w-[900px] flex-col px-4 pb-16 pt-3 font-sans sm:px-6 lg:pt-8">
    <BaseDialog
      v-model="createDialog"
      :title="$t('household.create-household')"
      :icon="$globals.icons.household"
      can-submit
      :submit-text="$t('general.create')"
      @submit="handleCreateSubmit"
    >
      <FieldScope ref="refNewHouseholdForm">
        <div class="px-6 pb-2">
          <SelectField
            v-if="groups"
            v-model="createHouseholdForm.data.groupId"
            :items="groups"
            item-title="name"
            item-value="id"
            :label="$t('household.household-group')"
            :rules="[validators.required]"
          />
          <AutoForm
            v-model="createHouseholdForm.data"
            class="px-0!"
            :update-mode="updateMode"
            :items="createHouseholdForm.items"
          />
        </div>
      </FieldScope>
    </BaseDialog>

    <BaseDialog
      v-model="confirmDialog"
      :title="$t('general.confirm')"
      :icon="$globals.icons.alertCircle"
      color="error"
      can-confirm
      @confirm="deleteHousehold(deleteTarget)"
    >
      <p class="m-0 px-6 pb-2 text-[15px]">
        {{ $t("general.confirm-delete-generic") }}
      </p>
    </BaseDialog>
    <header class="mb-5 flex flex-wrap items-center gap-3">
      <h1 class="m-0 flex-1 text-[26px] font-bold tracking-tight sm:text-[32px]">
        {{ $t('household.household-management') }}
      </h1>
      <Button @click="openDialog">
        <PlusIcon class="size-4" />
        {{ $t('household.create-household') }}
      </Button>
    </header>

    <ul class="m-0 flex list-none flex-col divide-y rounded-card border bg-card p-0">
      <li
        v-for="item in households || []"
        :key="item.id"
        class="flex items-center gap-2 pe-1.5"
      >
        <NuxtLink
          :to="`/admin/manage/households/${item.id}`"
          class="flex min-w-0 flex-1 items-center gap-3 py-3 ps-4 text-foreground no-underline hover:text-primary"
        >
          <span class="inline-flex size-9 shrink-0 items-center justify-center rounded-full bg-subtle text-subtle-foreground">
            <MdiIcon
              :path="$globals.icons.household"
              class="size-[18px]"
            />
          </span>
          <span class="min-w-0 flex-1">
            <span class="block truncate font-semibold">{{ item.name }}</span>
            <span class="block text-sm text-muted-foreground">{{ item.group }} · {{ $t('user.user-count', item.users?.length ?? 0) }}<template v-if="item.webhooks?.length"> · {{ $t('user.webhooks-enabled') }}</template></span>
          </span>
          <ChevronRightIcon class="size-4 shrink-0 text-muted-foreground rtl:rotate-180" />
        </NuxtLink>
        <button
          type="button"
          class="inline-flex size-9 shrink-0 items-center justify-center rounded-full text-muted-foreground hover:bg-destructive/10 hover:text-destructive disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-transparent disabled:hover:text-muted-foreground"
          :disabled="!(!item.users?.length)"
          :aria-label="$t('data-pages.delete-item', { name: item.name })"
          :title="(!item.users?.length) ? $t('general.delete') : $t('admin.household-delete-note')"
          @click="confirmDialog = true; deleteTarget = item.id"
        >
          <Trash2Icon class="size-4" />
        </button>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { ChevronRightIcon, PlusIcon, Trash2Icon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import { MdiIcon } from "~/components/ui/mdi-icon";
import FieldScope from "~/components/ui/field/FieldScope.vue";
import SelectField from "~/components/ui/field/SelectField.vue";
import { fieldTypes } from "~/composables/forms";
import { useGroups } from "~/composables/use-groups";
import { useAdminHouseholds } from "~/composables/use-households";
import { validators } from "~/composables/use-validators";

definePageMeta({
  layout: "admin",
});

const i18n = useI18n();

useSeoMeta({
  title: i18n.t("household.manage-households"),
});

const { groups } = useGroups();
const { households, deleteHousehold, createHousehold } = useAdminHouseholds();

const refNewHouseholdForm = ref<{ validate: () => Promise<{ valid: boolean }> } | null>(null);

const createDialog = ref(false);
const confirmDialog = ref(false);
const deleteTarget = ref<string>("");
const updateMode = ref(false);

const createHouseholdForm = reactive({
  items: [
    {
      label: i18n.t("household.household-name"),
      varName: "name",
      type: fieldTypes.TEXT,
      rules: [validators.required],
    },
  ],
  data: {
    groupId: "",
    name: "",
  },
});

function openDialog() {
  createDialog.value = true;
  createHouseholdForm.data.name = "";
  createHouseholdForm.data.groupId = "";
}

async function handleCreateSubmit() {
  const { valid } = (await refNewHouseholdForm.value?.validate()) ?? { valid: false };
  if (!valid) {
    return;
  }
  createDialog.value = false;
  await createHousehold(createHouseholdForm.data);
}
</script>
