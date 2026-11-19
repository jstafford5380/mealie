<template>
  <div class="mx-auto flex w-full max-w-[860px] flex-col gap-6 px-4 pb-16 pt-3 font-sans sm:px-6 lg:pt-8">
    <NuxtLink
      to="/group/migrations"
      class="-mb-2 inline-flex w-fit items-center gap-1 text-sm font-semibold text-muted-foreground no-underline hover:text-foreground"
    >
      <ChevronLeftIcon class="size-4 rtl:rotate-180" />
      {{ $t('migration.recipe-data-migrations') }}
    </NuxtLink>
    <header>
      <h1 class="m-0 text-[26px] font-bold tracking-tight sm:text-[32px]">
        {{ report?.name || $t('group.report') }}
      </h1>
      <p class="m-0 mt-1 text-sm text-muted-foreground">
        {{ $t('group.report-with-id', { id: id }) }}
      </p>
    </header>

    <template v-if="report">
      <p class="m-0 flex flex-wrap gap-x-4 text-sm">
        <span><b class="tabular-nums">{{ succeeded }}</b> {{ $t('group.report-succeeded') }}</span>
        <span :class="failed && 'text-destructive'"><b class="tabular-nums">{{ failed }}</b> {{ $t('group.report-failed') }}</span>
      </p>
      <ul class="m-0 flex list-none flex-col divide-y rounded-card border bg-card p-0">
        <li
          v-for="(entry, index) in report.entries"
          :key="index"
          class="px-4 py-2.5"
        >
          <div class="flex items-start gap-3">
            <MdiIcon
              :path="entry.success ? $globals.icons.checkboxMarkedCircle : $globals.icons.close"
              class="mt-0.5 size-5 shrink-0"
              :class="entry.success ? 'text-primary' : 'text-destructive'"
              :aria-label="entry.success ? $t('general.success') : $t('general.failed')"
            />
            <span class="min-w-0 flex-1 text-[15px]">{{ entry.message }}</span>
            <span class="shrink-0 text-xs whitespace-nowrap text-muted-foreground">{{ $d(Date.parse(entry.timestamp!), "short") }}</span>
          </div>
          <details
            v-if="entry.exception"
            class="ms-8 mt-1"
          >
            <summary class="cursor-pointer text-sm font-semibold text-muted-foreground">
              {{ $t('group.report-show-error') }}
            </summary>
            <pre class="m-0 mt-2 overflow-x-auto rounded-control bg-muted p-3 text-xs whitespace-pre-wrap">{{ entry.exception }}</pre>
          </details>
        </li>
      </ul>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ChevronLeftIcon } from "@lucide/vue";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { useUserApi } from "~/composables/api";
import type { ReportOut } from "~/lib/api/types/reports";

definePageMeta({
  middleware: ["auth"],
});

const route = useRoute();
const id = route.params.id as string;

const api = useUserApi();

const report = ref<ReportOut | null>(null);

async function getReport() {
  const { data } = await api.groupReports.getOne(id);
  report.value = data ?? null;
}

onMounted(async () => {
  await getReport();
});

const succeeded = computed(() => report.value?.entries.filter(entry => entry.success).length ?? 0);
const failed = computed(() => (report.value?.entries.length ?? 0) - succeeded.value);
</script>
