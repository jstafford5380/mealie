<template>
  <div class="mx-auto flex w-full max-w-[900px] flex-col px-4 pb-16 pt-3 font-sans sm:px-6 lg:pt-8">
    <BaseDialog
      v-model="state.createDialog"
      :title="$t('group.create-group')"
      :icon="$globals.icons.group"
      can-submit
      :submit-text="$t('general.create')"
      @submit="createGroup(state.createGroupForm.data)"
    >
      <div class="px-6 pb-2">
        <AutoForm
          v-model="state.createGroupForm.data"
          class="px-0!"
          :update-mode="state.updateMode"
          :items="state.createGroupForm.items"
        />
      </div>
    </BaseDialog>

    <BaseDialog
      v-model="state.confirmDialog"
      :title="$t('general.confirm')"
      :icon="$globals.icons.alertCircle"
      color="error"
      can-confirm
      @confirm="deleteGroup(state.deleteTarget)"
    >
      <p class="m-0 px-6 pb-2 text-[15px]">
        {{ $t("general.confirm-delete-generic") }}
      </p>
    </BaseDialog>
    <header class="mb-5 flex flex-wrap items-center gap-3">
      <h1 class="m-0 flex-1 text-[26px] font-bold tracking-tight sm:text-[32px]">
        {{ $t('group.group-management') }}
      </h1>
      <Button @click="openDialog">
        <PlusIcon class="size-4" />
        {{ $t('group.create-group') }}
      </Button>
    </header>

    <ul class="m-0 flex list-none flex-col divide-y rounded-card border bg-card p-0">
      <li
        v-for="item in groups || []"
        :key="item.id"
        class="flex items-center gap-2 pe-1.5"
      >
        <NuxtLink
          :to="`/admin/manage/groups/${item.id}`"
          class="flex min-w-0 flex-1 items-center gap-3 py-3 ps-4 text-foreground no-underline hover:text-primary"
        >
          <span class="inline-flex size-9 shrink-0 items-center justify-center rounded-full bg-subtle text-subtle-foreground">
            <MdiIcon
              :path="$globals.icons.group"
              class="size-[18px]"
            />
          </span>
          <span class="min-w-0 flex-1">
            <span class="block truncate font-semibold">{{ item.name }}</span>
            <span class="block text-sm text-muted-foreground">{{ $t('group.household-count', item.households?.length ?? 0) }} · {{ $t('user.user-count', item.users?.length ?? 0) }}</span>
          </span>
          <ChevronRightIcon class="size-4 shrink-0 text-muted-foreground rtl:rotate-180" />
        </NuxtLink>
        <button
          type="button"
          class="inline-flex size-9 shrink-0 items-center justify-center rounded-full text-muted-foreground hover:bg-destructive/10 hover:text-destructive disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-transparent disabled:hover:text-muted-foreground"
          :disabled="!(!item.households?.length && !item.users?.length)"
          :aria-label="$t('data-pages.delete-item', { name: item.name })"
          :title="(!item.households?.length && !item.users?.length) ? $t('general.delete') : $t('admin.group-delete-note')"
          @click="state.confirmDialog = true; state.deleteTarget = item.id"
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
import { fieldTypes } from "~/composables/forms";
import { useGroups } from "~/composables/use-groups";
import { validators } from "~/composables/use-validators";

definePageMeta({
  layout: "admin",
});

const i18n = useI18n();

useHead({
  title: i18n.t("group.manage-groups"),
});

// Set page title
useSeoMeta({
  title: i18n.t("group.manage-groups"),
});

const { groups, deleteGroup, createGroup } = useGroups();

const state = reactive({
  createDialog: false,
  confirmDialog: false,
  deleteTarget: "",
  updateMode: false,
  createGroupForm: {
    items: [
      {
        label: i18n.t("group.group-name"),
        varName: "name",
        type: fieldTypes.TEXT,
        rules: [validators.required],
      },
    ],
    data: {
      name: "",
    },
  },
});

function openDialog() {
  state.createDialog = true;
  state.createGroupForm.data.name = "";
}
</script>
