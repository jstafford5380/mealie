<template>
  <CrudTable
    v-model:selected="selected"
    :headers="headers"
    :table-config="{ hideColumns: true, canExport: false }"
    :data="recipes"
    :bulk-actions="bulkActions"
    :loading="loading"
    :row-actions="false"
    keep-selection
    initial-sort="dateAdded"
    initial-sort-desc
    @bulk-action="(event, items) => $emit('bulk-action', event, items)"
  >
    <template #button-row>
      <slot name="button-row" />
    </template>
    <template #button-bottom>
      <slot name="button-bottom" />
    </template>
    <template #[`item.name`]="{ item }">
      <NuxtLink
        :to="`/g/${groupSlug}/r/${item.slug}`"
        class="font-medium text-foreground no-underline hover:text-primary hover:underline"
        @click="$emit('click')"
      >
        {{ item.name }}
      </NuxtLink>
    </template>
    <template #[`item.tags`]="{ item }">
      <RecipeChip
        small
        :items="item.tags"
        :is-category="false"
        url-prefix="tags"
        @item-selected="filterItems"
      />
    </template>
    <template #[`item.recipeCategory`]="{ item }">
      <RecipeChip
        small
        :items="item.recipeCategory"
        @item-selected="filterItems"
      />
    </template>
    <template #[`item.tools`]="{ item }">
      <RecipeChip
        small
        :items="item.tools"
        url-prefix="tools"
        @item-selected="filterItems"
      />
    </template>
    <template #[`item.userId`]="{ item }">
      <span class="inline-flex items-center gap-2 whitespace-nowrap">
        <UserAvatar
          :user-id="item.userId"
          :tooltip="false"
          size="28"
        />
        {{ getMember(item.userId) }}
      </span>
    </template>
    <template #[`item.dateAdded`]="{ item }">
      <span class="whitespace-nowrap">{{ item.dateAdded ? $d(new Date(item.dateAdded)) : '' }}</span>
    </template>
  </CrudTable>
</template>

<script setup lang="ts">
import UserAvatar from "../User/UserAvatar.vue";
import RecipeChip from "./RecipeChips.vue";
import CrudTable from "~/components/global/CrudTable.vue";
import type { BulkAction, TableHeaders } from "~/components/global/CrudTable.vue";
import type { CategoryOut, RecipeSummary, ToolOut } from "~/lib/api/types/recipe";
import { useUserApi } from "~/composables/api";
import type { UserSummary } from "~/lib/api/types/user";
import type { TagOut } from "~/lib/api/types/household";

interface ShowHeaders {
  id: boolean;
  owner: boolean;
  tags: boolean;
  categories: boolean;
  tools: boolean;
  recipeServings: boolean;
  recipeYieldQuantity: boolean;
  recipeYield: boolean;
  dateAdded: boolean;
}

interface Props {
  loading?: boolean;
  recipes?: RecipeSummary[];
  /** Which columns start visible; the table's own menu changes them after that. */
  showHeaders?: ShowHeaders;
  bulkActions?: BulkAction[];
}
const props = withDefaults(defineProps<Props>(), {
  loading: false,
  recipes: () => [],
  bulkActions: () => [],
  showHeaders: () => ({
    id: true,
    owner: false,
    tags: true,
    categories: true,
    tools: true,
    recipeServings: true,
    recipeYieldQuantity: true,
    recipeYield: true,
    dateAdded: true,
  }),
});

defineEmits<{
  "click": [];
  "bulk-action": [event: string, items: RecipeSummary[]];
}>();

const selected = defineModel<RecipeSummary[]>({ default: () => [] });

const i18n = useI18n();
const auth = useMealieAuth();
const groupSlug = auth.user.value?.groupSlug;
const router = useRouter();

const headers = computed<TableHeaders[]>(() => [
  { text: i18n.t("general.id"), value: "id", show: props.showHeaders.id },
  { text: i18n.t("general.owner"), value: "userId", show: props.showHeaders.owner, sortable: true },
  { text: i18n.t("general.name"), value: "name", show: true, sortable: true },
  { text: i18n.t("recipe.categories"), value: "recipeCategory", show: props.showHeaders.categories, sortable: true },
  { text: i18n.t("tag.tags"), value: "tags", show: props.showHeaders.tags, sortable: true },
  { text: i18n.t("tool.tools"), value: "tools", show: props.showHeaders.tools, sortable: true },
  { text: i18n.t("recipe.servings"), value: "recipeServings", show: props.showHeaders.recipeServings, sortable: true },
  { text: i18n.t("recipe.yield"), value: "recipeYieldQuantity", show: props.showHeaders.recipeYieldQuantity, sortable: true },
  { text: i18n.t("recipe.yield-text"), value: "recipeYield", show: props.showHeaders.recipeYield, sortable: true },
  { text: i18n.t("general.date-added"), value: "dateAdded", show: props.showHeaders.dateAdded, sortable: true },
]);

// ============
// Group Members
const api = useUserApi();
const members = ref<UserSummary[]>([]);

async function refreshMembers() {
  const { data } = await api.groups.fetchMembers();
  if (data) {
    members.value = data.items;
  }
}

function filterItems(item: TagOut | CategoryOut | ToolOut, itemType: string) {
  if (!groupSlug || !item.id) {
    return;
  }
  router.push(`/g/${groupSlug}?${itemType}=${item.id}`);
}

onMounted(() => {
  refreshMembers();
});

function getMember(id: string) {
  if (members.value[0]) {
    return members.value.find(m => m.id === id)?.fullName;
  }

  return i18n.t("general.none");
}
</script>
