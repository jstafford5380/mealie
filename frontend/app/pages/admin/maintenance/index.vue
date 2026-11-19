<template>
  <div class="mx-auto flex w-full max-w-[860px] flex-col px-4 pb-16 pt-3 font-sans sm:px-6 lg:pt-8">
    <BaseDialog
      v-model="state.storageDetails"
      :title="$t('admin.maintenance.storage-details')"
      :icon="$globals.icons.folderOutline"
    >
      <dl class="m-0 mx-6 mb-2 divide-y rounded-card border">
        <div
          v-for="(value, key) in storageDetails"
          :key="key"
          class="flex flex-wrap items-baseline justify-between gap-x-4 px-4 py-2.5"
        >
          <dt class="text-sm text-muted-foreground">
            {{ storageDetailsText(key) }}
          </dt>
          <dd class="m-0 font-mono text-sm font-semibold">
            {{ value }}
          </dd>
        </div>
      </dl>
    </BaseDialog>

    <h1 class="m-0 mb-8 text-[26px] font-bold tracking-tight sm:text-[32px]">
      {{ $t("admin.maintenance.page-title") }}
    </h1>

    <section class="mb-8">
      <div class="mb-3 flex flex-wrap items-center gap-2">
        <h2 class="m-0 flex-1 text-base font-semibold">
          {{ $t('admin.maintenance.summary-title') }}
        </h2>
        <Button
          variant="outline"
          :disabled="state.fetchingInfo"
          @click="getSummary"
        >
          <LoaderCircleIcon
            v-if="state.fetchingInfo"
            class="size-4 animate-spin"
          />
          <RefreshCwIcon
            v-else
            class="size-4"
          />
          {{ $t("admin.maintenance.button-label-get-summary") }}
        </Button>
        <Button
          variant="ghost"
          @click="openDetails"
        >
          <MdiIcon
            :path="$globals.icons.folderOutline"
            class="size-4"
          />
          {{ $t("admin.maintenance.button-label-open-details") }}
        </Button>
      </div>
      <dl class="m-0 divide-y rounded-card border bg-card">
        <div
          v-for="(value, idx) in info"
          :key="idx"
          class="flex flex-wrap items-baseline justify-between gap-x-4 px-4 py-3"
        >
          <dt class="text-[15px]">
            {{ value.name }}
          </dt>
          <dd class="m-0 font-semibold tabular-nums">
            {{ value.value }}
          </dd>
        </div>
      </dl>
    </section>

    <section>
      <h2 class="m-0 text-base font-semibold">
        {{ $t('admin.mainentance.actions-title') }}
      </h2>
      <p class="m-0 mt-1 mb-3 max-w-[65ch] text-sm text-muted-foreground">
        <i18n-t keypath="admin.maintenance.actions-description">
          <template #destructive_in_bold>
            <b class="text-foreground">{{ $t("admin.maintenance.actions-description-destructive") }}</b>
          </template>
          <template #irreversible_in_bold>
            <b class="text-foreground">{{ $t("admin.maintenance.actions-description-irreversible") }}</b>
          </template>
        </i18n-t>
      </p>
      <ul class="m-0 flex list-none flex-col divide-y rounded-card border bg-card p-0">
        <li
          v-for="(action, idx) in actions"
          :key="idx"
          class="flex flex-wrap items-center gap-3 px-4 py-3"
        >
          <span class="min-w-0 flex-1 basis-60">
            <span class="block font-semibold">{{ action.name }}</span>
            <span class="block text-sm break-words text-muted-foreground">{{ action.subtitle }}</span>
          </span>
          <Button
            variant="outline"
            :disabled="state.actionLoading"
            @click="action.handler"
          >
            {{ $t("general.run") }}
          </Button>
        </li>
      </ul>
    </section>
  </div>
</template>

<script setup lang="ts">
import { LoaderCircleIcon, RefreshCwIcon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { useAdminApi } from "~/composables/api";
import type { MaintenanceStorageDetails, MaintenanceSummary } from "~/lib/api/types/admin";

definePageMeta({
  layout: "admin",
});

const state = reactive({
  storageDetails: false,
  storageDetailsLoading: false,
  fetchingInfo: false,
  actionLoading: false,
});

const adminApi = useAdminApi();
const i18n = useI18n();

// Set page title
useSeoMeta({
  title: i18n.t("admin.maintenance.page-title"),
});

// ==========================================================================
// General Info

const infoResults = ref<MaintenanceSummary>({
  dataDirSize: i18n.t("about.unknown-version"),
  cleanableDirs: 0,
  cleanableImages: 0,
});

async function getSummary() {
  state.fetchingInfo = true;
  const { data } = await adminApi.maintenance.getInfo();

  infoResults.value = data ?? {
    dataDirSize: i18n.t("about.unknown-version"),
    cleanableDirs: 0,
    cleanableImages: 0,
  };

  state.fetchingInfo = false;
}

const info = computed(() => {
  return [
    {
      name: i18n.t("admin.maintenance.info-description-data-dir-size"),
      value: infoResults.value.dataDirSize,
    },
    {
      name: i18n.t("admin.maintenance.info-description-cleanable-directories"),
      value: infoResults.value.cleanableDirs,
    },
    {
      name: i18n.t("admin.maintenance.info-description-cleanable-images"),
      value: infoResults.value.cleanableImages,
    },
  ];
});

// ==========================================================================
// Storage Details

const storageTitles: { [key: string]: string } = {
  tempDirSize: i18n.t("admin.maintenance.storage.title-temporary-directory") as string,
  backupsDirSize: i18n.t("admin.maintenance.storage.title-backups-directory") as string,
  groupsDirSize: i18n.t("admin.maintenance.storage.title-groups-directory") as string,
  recipesDirSize: i18n.t("admin.maintenance.storage.title-recipes-directory") as string,
  userDirSize: i18n.t("admin.maintenance.storage.title-user-directory") as string,
};

function storageDetailsText(key: string) {
  return storageTitles[key] ?? i18n.t("about.unknown-version");
}

const storageDetails = ref<MaintenanceStorageDetails | null>(null);

async function openDetails() {
  state.storageDetailsLoading = true;
  state.storageDetails = true;

  const { data } = await adminApi.maintenance.getStorageDetails();

  if (data) {
    storageDetails.value = data;
  }

  state.storageDetailsLoading = true;
}

// ==========================================================================
// Actions

async function handleCleanDirectories() {
  state.actionLoading = true;
  await adminApi.maintenance.cleanRecipeFolders();
  state.actionLoading = false;
}

async function handleCleanImages() {
  state.actionLoading = true;
  await adminApi.maintenance.cleanImages();
  state.actionLoading = false;
}

async function handleCleanTemp() {
  state.actionLoading = true;
  await adminApi.maintenance.cleanTemp();
  state.actionLoading = false;
}

const actions = [
  {
    name: i18n.t("admin.maintenance.action-clean-directories-name"),
    handler: handleCleanDirectories,
    subtitle: i18n.t("admin.maintenance.action-clean-directories-description"),
  },
  {
    name: i18n.t("admin.maintenance.action-clean-temporary-files-name"),
    handler: handleCleanTemp,
    subtitle: i18n.t("admin.maintenance.action-clean-temporary-files-description"),
  },
  {
    name: i18n.t("admin.maintenance.action-clean-images-name"),
    handler: handleCleanImages,
    subtitle: i18n.t("admin.maintenance.action-clean-images-description"),
  },
];
</script>

<style scoped>
.wrap-word {
  white-space: normal;
  word-wrap: break-word;
}
</style>
