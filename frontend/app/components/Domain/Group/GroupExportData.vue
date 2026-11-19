<template>
  <div class="overflow-x-auto rounded-card border bg-card font-sans">
    <table class="w-full border-collapse text-[14.5px]">
      <thead>
        <tr class="border-b bg-muted/40 text-left text-[13px] text-muted-foreground">
          <th class="h-11 px-3 font-semibold">
            {{ $t("export.export") }}
          </th>
          <th class="h-11 px-3 font-semibold">
            {{ $t("export.file-name") }}
          </th>
          <th class="h-11 px-3 font-semibold">
            {{ $t("export.size") }}
          </th>
          <th class="h-11 px-3 font-semibold">
            {{ $t("export.link-expires") }}
          </th>
          <th class="w-14">
            <span class="sr-only">{{ $t("general.download") }}</span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="item in exports"
          :key="item.id"
          class="border-b last:border-b-0"
        >
          <td class="px-3 py-2.5 font-medium">
            {{ item.name }}
          </td>
          <td class="px-3 py-2.5 text-muted-foreground">
            {{ item.filename }}
          </td>
          <td class="px-3 py-2.5 whitespace-nowrap">
            {{ item.size }}
          </td>
          <td class="px-3 py-2.5 whitespace-nowrap">
            {{ getTimeToExpire(item.expires) }}
          </td>
          <td class="pe-2 text-end">
            <button
              type="button"
              class="inline-flex size-9 items-center justify-center rounded-full text-muted-foreground hover:bg-highlight hover:text-foreground"
              :aria-label="$t('general.download')"
              :title="$t('general.download')"
              @click="api.utils.download(`/api/recipes/bulk-actions/export/${item.id}/download`)"
            >
              <DownloadIcon class="size-4" />
            </button>
          </td>
        </tr>
        <tr v-if="!exports.length">
          <td
            colspan="5"
            class="px-4 py-8 text-center text-sm text-muted-foreground"
          >
            {{ $t("data-pages.recipes.no-exports-yet") }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { DownloadIcon } from "@lucide/vue";
import { parseISO, formatDistanceToNow } from "date-fns";
import { useUserApi } from "~/composables/api";
import type { GroupDataExport } from "~/lib/api/types/group";

defineProps<{
  exports: GroupDataExport[];
}>();

const api = useUserApi();

function getTimeToExpire(timeString: string) {
  const expiresAt = parseISO(timeString);

  return formatDistanceToNow(expiresAt, {
    addSuffix: false,
  });
}
</script>
