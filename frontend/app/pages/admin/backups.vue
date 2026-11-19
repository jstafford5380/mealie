<template>
  <div class="mx-auto flex w-full max-w-[900px] flex-col px-4 pb-16 pt-3 font-sans sm:px-6 lg:pt-8">
    <!-- Delete Dialog -->
    <BaseDialog
      v-model="state.deleteDialog"
      :title="$t('settings.backup.delete-backup')"
      color="error"
      :icon="$globals.icons.alertCircle"
      can-confirm
      @confirm="deleteBackup()"
    >
      <div class="flex flex-col gap-3 px-6 pb-2 text-[15px]">
        <p class="m-0">
          {{ $t("general.confirm-delete-generic") }}
        </p>
        <p class="m-0 rounded-control bg-muted px-3 py-2 font-mono text-sm">
          {{ deleteTarget }}
        </p>
      </div>
    </BaseDialog>

    <!-- Restore Dialog -->
    <BaseDialog
      v-model="state.importDialog"
      color="error"
      :title="$t('settings.backup.backup-restore')"
      :icon="$globals.icons.database"
    >
      <div class="flex flex-col gap-3 px-6 pb-2 text-[15px]">
        <p class="m-0 rounded-control bg-muted px-3 py-2 font-mono text-sm">
          {{ selected }}
        </p>
        <p class="m-0">
          <i18n-t keypath="settings.backup.back-restore-description">
            <template #cannot-be-undone>
              <b>{{ $t('settings.backup.cannot-be-undone') }}</b>
            </template>
          </i18n-t>
        </p>
        <p class="m-0 text-sm text-muted-foreground">
          <i18n-t keypath="settings.backup.postgresql-note">
            <template #backup-restore-process>
              <a
                class="font-semibold text-primary"
                href="https://nightly.mealie.io/documentation/getting-started/usage/backups-and-restoring/"
                target="_blank"
                rel="noopener"
              >{{ $t('settings.backup.backup-restore-process-in-the-documentation') }}</a>
            </template>
          </i18n-t>
        </p>
        <label class="flex cursor-pointer items-start gap-2 rounded-control border border-destructive/40 bg-destructive/5 p-3 text-sm">
          <Checkbox
            v-model="state.confirmImport"
            class="mt-0.5"
          />
          {{ $t('settings.backup.irreversible-acknowledgment') }}
        </label>
        <div
          v-if="state.runningRestore"
          class="flex items-center gap-2 text-sm text-muted-foreground"
          role="status"
        >
          <LoaderCircleIcon class="size-4 animate-spin" />
          {{ $t('settings.backup.restoring') }}
        </div>
      </div>
      <template #custom-card-action>
        <Button
          variant="destructive"
          :disabled="!state.confirmImport || state.runningRestore"
          @click="restoreBackup(selected)"
        >
          <MdiIcon
            :path="$globals.icons.database"
            class="size-4"
          />
          {{ $t('settings.backup.restore-backup') }}
        </Button>
      </template>
    </BaseDialog>

    <header class="mb-5 flex flex-wrap items-end gap-3">
      <div class="min-w-0 flex-1">
        <h1 class="m-0 text-[26px] font-bold tracking-tight sm:text-[32px]">
          {{ $t('settings.backup-and-exports') }}
        </h1>
        <p class="m-0 mt-1 max-w-[65ch] text-[15px] text-muted-foreground">
          <i18n-t keypath="settings.backup.experimental-description" />
        </p>
      </div>
      <div class="flex flex-wrap gap-2">
        <AppButtonUpload
          :text-btn="false"
          url="/api/admin/backups/upload"
          accept=".zip"
          @uploaded="refreshBackups()"
        />
        <Button
          :disabled="state.runningBackup"
          @click="createBackup"
        >
          <LoaderCircleIcon
            v-if="state.runningBackup"
            class="size-4 animate-spin"
          />
          <PlusIcon
            v-else
            class="size-4"
          />
          {{ $t("settings.backup.create-heading") }}
        </Button>
      </div>
    </header>

    <ul
      v-if="backups.imports && backups.imports.length"
      class="m-0 flex list-none flex-col divide-y rounded-card border bg-card p-0"
    >
      <li
        v-for="item in backups.imports"
        :key="item.name"
        class="flex flex-wrap items-center gap-x-3 gap-y-2 py-2.5 ps-4 pe-2"
      >
        <MdiIcon
          :path="$globals.icons.database"
          class="size-5 shrink-0 text-muted-foreground"
        />
        <span class="min-w-0 flex-1">
          <span class="block truncate font-mono text-sm font-semibold">{{ item.name }}</span>
          <span class="block text-sm text-muted-foreground">{{ $d(Date.parse(item.date)) }} · {{ item.size }}</span>
        </span>
        <span class="flex items-center gap-1">
          <button
            type="button"
            class="inline-flex size-9 items-center justify-center rounded-full text-muted-foreground hover:bg-highlight hover:text-foreground"
            :aria-label="$t('general.download')"
            :title="$t('general.download')"
            @click="api.utils.download(backupsFileNameDownload(item.name))"
          >
            <DownloadIcon class="size-4" />
          </button>
          <button
            type="button"
            class="inline-flex size-9 items-center justify-center rounded-full text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
            :aria-label="$t('settings.backup.delete-backup')"
            :title="$t('settings.backup.delete-backup')"
            @click="state.deleteDialog = true; deleteTarget = item.name"
          >
            <Trash2Icon class="size-4" />
          </button>
          <Button
            size="sm"
            variant="outline"
            @click="setSelected(item); state.confirmImport = false; state.importDialog = true"
          >
            <MdiIcon
              :path="$globals.icons.backupRestore"
              class="size-4"
            />
            {{ $t("settings.backup.restore-backup") }}
          </Button>
        </span>
      </li>
    </ul>
    <p
      v-else
      class="m-0 rounded-card border border-dashed px-4 py-8 text-center text-sm text-muted-foreground"
    >
      {{ $t('settings.backup.no-backups-yet') }}
    </p>

    <p class="m-0 mt-6 text-center text-sm">
      <NuxtLink
        class="font-semibold text-primary no-underline hover:underline"
        to="/group/migrations"
      >
        {{ $t('recipe.looking-for-migrations') }}
      </NuxtLink>
    </p>
  </div>
</template>

<script setup lang="ts">
import { DownloadIcon, LoaderCircleIcon, PlusIcon, Trash2Icon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import { Checkbox } from "~/components/ui/checkbox";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { useAdminApi, useUserApi } from "~/composables/api";
import type { AllBackups } from "~/lib/api/types/admin";
import { alert } from "~/composables/use-toast";

definePageMeta({
  layout: "admin",
});

const i18n = useI18n();

const adminApi = useAdminApi();
const selected = ref("");

const backups = ref<AllBackups>({
  imports: [],
  templates: [],
});

async function refreshBackups() {
  const { data } = await adminApi.backups.getAll();
  if (data) {
    backups.value = data;
  }
}

async function createBackup() {
  state.runningBackup = true;
  const { data } = await adminApi.backups.create();

  if (data?.error === false) {
    refreshBackups();
    alert.success(i18n.t("settings.backup.backup-created"));
  }
  else {
    alert.error(i18n.t("settings.backup.error-creating-backup-see-log-file"));
  }
  state.runningBackup = false;
}

async function restoreBackup(fileName: string) {
  state.runningRestore = true;
  const { error } = await adminApi.backups.restore(fileName);

  if (error) {
    console.log(error);
    state.importDialog = false;
    state.runningRestore = false;
    alert.error(i18n.t("settings.backup.restore-fail"));
  }
  else {
    alert.success(i18n.t("settings.backup.restore-success"));
    setTimeout(() => {
      window.location.reload();
    }, 500);
  }
}

const deleteTarget = ref("");

async function deleteBackup() {
  const { data } = await adminApi.backups.delete(deleteTarget.value);

  if (!data?.error) {
    alert.success(i18n.t("settings.backup.backup-deleted"));
    refreshBackups();
  }
}

const state = reactive({
  confirmImport: false,
  deleteDialog: false,
  createDialog: false,
  importDialog: false,
  runningBackup: false,
  runningRestore: false,
});

function setSelected(data: { name: string; date: string }) {
  if (!data.name) {
    return;
  }
  selected.value = data.name;
}

const backupsFileNameDownload = (fileName: string) => `api/admin/backups/${fileName}`;
const api = useUserApi();

useSeoMeta({
  title: i18n.t("sidebar.backups"),
});

onMounted(refreshBackups);

useHead({
  title: i18n.t("sidebar.backups"),
});
</script>

<style>
.v-input--selection-controls__input {
  margin-bottom: auto;
}
</style>
