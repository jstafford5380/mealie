<template>
  <ul
    v-if="items.length"
    class="m-0 flex list-none flex-col divide-y rounded-card border bg-card p-0 font-sans"
  >
    <li
      v-for="item in items"
      :key="item.id"
      class="flex items-center gap-3 py-2 ps-4 pe-1.5"
    >
      <component
        :is="item.status === 'in-progress' ? 'div' : NuxtLink"
        :to="item.status === 'in-progress' ? undefined : `/group/reports/${item.id}`"
        class="flex min-w-0 flex-1 items-center gap-3 text-foreground no-underline"
      >
        <span class="min-w-0 flex-1">
          <span class="block truncate font-semibold">{{ item.name }}</span>
          <span class="block text-sm text-muted-foreground">
            {{ capitalize(item.category) }} · {{ $d(Date.parse(item.timestamp!), "long") }}
          </span>
        </span>
        <span
          class="shrink-0 rounded-full px-2 py-0.5 text-xs font-semibold"
          :class="STATUS_CLASSES[item.status!] || 'bg-muted text-muted-foreground'"
        >{{ capitalize(item.status!) }}</span>
      </component>
      <button
        type="button"
        class="inline-flex size-9 shrink-0 items-center justify-center rounded-full text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
        :aria-label="$t('data-pages.delete-item', { name: item.name })"
        :title="$t('general.delete')"
        @click="deleteReport(item.id)"
      >
        <Trash2Icon class="size-4" />
      </button>
    </li>
  </ul>
  <p
    v-else
    class="m-0 rounded-card border border-dashed px-4 py-6 text-center text-sm text-muted-foreground"
  >
    {{ $t('group.no-reports-yet') }}
  </p>
</template>

<script setup lang="ts">
import { Trash2Icon } from "@lucide/vue";
import type { ReportSummary } from "~/lib/api/types/reports";

defineProps({
  items: {
    type: Array as () => Array<ReportSummary>,
    required: true,
  },
});

const emit = defineEmits<{
  (e: "delete", id: string): void;
}>();

const NuxtLink = resolveComponent("NuxtLink");

const STATUS_CLASSES: Record<string, string> = {
  "success": "bg-primary/15 text-primary",
  "failure": "bg-destructive/15 text-destructive",
  "partial": "bg-brand/20 text-brand-strong",
  "in-progress": "bg-muted text-muted-foreground",
};

function capitalize(str: string) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

function deleteReport(id: string) {
  emit("delete", id);
}
</script>

<style lang="scss" scoped></style>
