<template>
  <div class="flex flex-col gap-8 font-sans">
    <section class="rounded-panel border bg-card p-5 sm:p-6">
      <h2 class="m-0 text-xl font-bold tracking-tight">
        {{ $t('recipe.recipe-bulk-importer') }}
      </h2>
      <p class="m-0 mt-1 text-[15px] text-muted-foreground">
        {{ $t('recipe.recipe-bulk-importer-description') }}
      </p>

      <ol class="m-0 mt-4 flex list-none flex-col gap-3 p-0">
        <li
          v-for="(_, idx) in bulkUrls"
          :key="'bulk-url' + idx"
          class="flex flex-col gap-2"
          :class="state.showCatTags && 'rounded-card border p-3'"
        >
          <div class="flex items-center gap-2">
            <span class="w-6 shrink-0 text-end text-sm text-muted-foreground tabular-nums">{{ idx + 1 }}</span>
            <input
              v-model="bulkUrls[idx]!.url"
              type="url"
              autofocus
              :placeholder="$t('new-recipe.recipe-url')"
              :aria-label="`${$t('new-recipe.recipe-url')} ${idx + 1}`"
              class="h-10 min-w-0 flex-1 rounded-control border border-input bg-card px-3 text-[15px] outline-none focus:border-ring focus:ring-3 focus:ring-ring/25"
            >
            <button
              type="button"
              class="inline-flex size-9 shrink-0 items-center justify-center rounded-full text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
              :aria-label="$t('general.delete')"
              @click="bulkUrls.splice(idx, 1)"
            >
              <Trash2Icon class="size-4" />
            </button>
          </div>
          <div
            v-if="state.showCatTags"
            class="grid gap-2 ps-8 sm:grid-cols-2"
          >
            <RecipeOrganizerSelector
              v-model="bulkUrls[idx]!.categories"
              selector-type="categories"
            />
            <RecipeOrganizerSelector
              v-model="bulkUrls[idx]!.tags"
              selector-type="tags"
            />
          </div>
        </li>
      </ol>
      <p
        v-if="!bulkUrls.length"
        class="m-0 mt-4 rounded-card border border-dashed px-4 py-6 text-center text-sm text-muted-foreground"
      >
        {{ $t('recipe.bulk-no-urls-yet') }}
      </p>

      <div class="mt-3 flex flex-wrap items-center gap-2">
        <Button
          variant="outline"
          @click="bulkUrls.push({ url: '', categories: [], tags: [] })"
        >
          <PlusIcon class="size-4" />
          {{ $t('recipe.add-url') }}
        </Button>
        <RecipeDialogBulkAdd
          v-model="state.bulkDialog"
          @bulk-data="assignUrls"
        />
        <Button
          v-if="bulkUrls.length"
          variant="ghost"
          class="ms-auto text-destructive hover:text-destructive"
          @click="bulkUrls = []; lockBulkImport = false"
        >
          {{ $t('general.clear') }}
        </Button>
      </div>

      <div class="mt-5 flex flex-wrap items-center justify-between gap-3 border-t pt-4">
        <label class="flex cursor-pointer items-center gap-2 text-sm">
          <Checkbox v-model="state.showCatTags" />
          {{ $t('recipe.set-categories-and-tags') }}
        </label>
        <Button
          :disabled="bulkUrls.length === 0 || lockBulkImport"
          @click="bulkCreate"
        >
          {{ $t('recipe.import-count', bulkUrls.length) }}
        </Button>
      </div>
    </section>

    <section>
      <h2 class="m-0 mb-3 text-base font-semibold">
        {{ $t('recipe.bulk-imports') }}
      </h2>
      <ReportTable
        :items="reports"
        @delete="deleteReport"
      />
    </section>
  </div>
</template>

<script setup lang="ts">
import { PlusIcon, Trash2Icon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import { Checkbox } from "~/components/ui/checkbox";
import { whenever } from "@vueuse/shared";
import { useUserApi } from "~/composables/api";
import { alert } from "~/composables/use-toast";
import RecipeOrganizerSelector from "~/components/Domain/Recipe/RecipeOrganizerSelector.vue";
import type { ReportSummary } from "~/lib/api/types/reports";
import RecipeDialogBulkAdd from "~/components/Domain/Recipe/RecipeDialogBulkAdd.vue";

const state = reactive({
  showCatTags: false,
  bulkDialog: false,
});

whenever(
  () => !state.showCatTags,
  () => {
    console.log("showCatTags changed");
  },
);

const api = useUserApi();
const i18n = useI18n();

const bulkUrls = ref([{ url: "", categories: [], tags: [] }]);
const lockBulkImport = ref(false);

async function bulkCreate() {
  if (bulkUrls.value.length === 0) {
    return;
  }

  const { response } = await api.recipes.createManyByUrl({ imports: bulkUrls.value });

  if (response?.status === 202) {
    alert.success(i18n.t("recipe.bulk-import-process-has-started"));
    lockBulkImport.value = true;
  }
  else {
    alert.error(i18n.t("recipe.bulk-import-process-has-failed"));
  }

  fetchReports();
}

// =========================================================
// Reports

const reports = ref<ReportSummary[]>([]);

async function fetchReports() {
  const { data } = await api.groupReports.getAll("bulk_import");
  reports.value = data ?? [];
}

async function deleteReport(id: string) {
  console.log(id);
  const { response } = await api.groupReports.deleteOne(id);

  if (response?.status === 200) {
    fetchReports();
  }
  else {
    alert.error(i18n.t("recipe.report-deletion-failed"));
  }
}

fetchReports();

function assignUrls(urls: string[]) {
  if (urls.length === 0) {
    return;
  }

  bulkUrls.value = urls.map(url => ({ url, categories: [], tags: [] }));
}
</script>
