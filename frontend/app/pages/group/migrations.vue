<template>
  <div class="mx-auto flex w-full max-w-[860px] flex-col gap-8 px-4 pb-16 pt-3 font-sans sm:px-6 lg:pt-8">
    <header>
      <h1 class="m-0 text-[26px] font-bold tracking-tight sm:text-[32px]">
        {{ $t('migration.recipe-data-migrations') }}
      </h1>
      <p class="m-0 mt-1 max-w-[65ch] text-[15px] text-muted-foreground">
        {{ $t('migration.recipe-data-migrations-explanation') }}
      </p>
    </header>

    <section class="rounded-panel border bg-card p-5 sm:p-6">
      <h2 class="m-0 mb-4 text-xl font-bold tracking-tight">
        {{ $t('migration.new-migration') }}
      </h2>
      <div class="max-w-sm">
        <SelectField
          v-model="state.migrationType"
          :items="items"
          item-title="text"
          item-value="value"
          :label="$t('migration.choose-migration-type')"
        />
      </div>
      <template v-if="content">
        <p class="m-0 mt-2 max-w-[70ch] text-[15px] whitespace-pre-line text-muted-foreground">
          {{ content.text }}
        </p>
        <div
          v-if="content.tree && Array.isArray(content.tree)"
          class="mt-4 rounded-card border bg-muted/40 p-4"
        >
          <p class="m-0 mb-2 text-sm font-semibold">
            {{ $t('migration.expected-file-layout') }}
          </p>
          <GroupMigrationFileTree
            :key="state.migrationType"
            :nodes="content.tree"
          />
        </div>
      </template>

      <div class="mt-6 flex flex-col gap-3 border-t pt-5">
        <div class="flex flex-wrap items-center gap-3">
          <AppButtonUpload
            :accept="content.acceptedFileType || '.zip'"
            :post="false"
            file-name="file"
            :text-btn="false"
            @uploaded="setFileObject"
          />
          <span
            class="text-sm"
            :class="state.fileObject.name ? 'font-semibold' : 'text-muted-foreground'"
          >{{ state.fileObject.name || $t('migration.no-file-selected') }}</span>
        </div>
        <label class="flex w-fit cursor-pointer items-center gap-2 text-[15px]">
          <Checkbox v-model="state.addMigrationTag" />
          <span>
            <i18n-t keypath="migration.tag-all-recipes">
              <template #tag-name>
                <b>{{ state.migrationType }}</b>
              </template>
            </i18n-t>
          </span>
        </label>
        <Button
          class="self-end"
          :disabled="!state.fileObject.name || state.loading"
          @click="startMigration"
        >
          <LoaderCircleIcon
            v-if="state.loading"
            class="size-4 animate-spin"
          />
          {{ $t("migration.start-migration") }}
        </Button>
      </div>
    </section>

    <section>
      <h2 class="m-0 mb-3 text-base font-semibold">
        {{ $t('migration.previous-migrations') }}
      </h2>
      <ReportTable
        :items="state.reports"
        @delete="deleteReport"
      />
    </section>
  </div>
</template>

<script setup lang="ts">
import { LoaderCircleIcon } from "@lucide/vue";
import GroupMigrationFileTree from "~/components/Domain/Group/GroupMigrationFileTree.vue";
import { Button } from "~/components/ui/button";
import { Checkbox } from "~/components/ui/checkbox";
import SelectField from "~/components/ui/field/SelectField.vue";
import type { ReportSummary } from "~/lib/api/types/reports";
import type { MenuItem } from "~/components/global/BaseOverflowButton.vue";
import { useUserApi } from "~/composables/api";
import type { SupportedMigrations } from "~/lib/api/types/group";

interface TreeNode {
  id?: number;
  icon: string;
  title: string;
  children?: TreeNode[];
}

interface MigrationContent {
  text: string;
  acceptedFileType: string;
  tree: TreeNode[] | false;
}

const MIGRATIONS = {
  mealie: "mealie_alpha",
  chowdown: "chowdown",
  copymethat: "copymethat",
  myrecipebox: "myrecipebox",
  nextcloud: "nextcloud",
  paprika: "paprika",
  plantoeat: "plantoeat",
  recipekeeper: "recipekeeper",
  tandoor: "tandoor",
  cookn: "cookn",
};

definePageMeta({
  middleware: ["auth", "advanced-only"],
});

const i18n = useI18n();
const { $globals } = useNuxtApp();

useSeoMeta({
  title: i18n.t("settings.migrations"),
});

const api = useUserApi();

const state = reactive({
  addMigrationTag: false,
  loading: false,
  treeState: true,
  migrationType: MIGRATIONS.mealie as SupportedMigrations,
  fileObject: {} as File,
  reports: [] as ReportSummary[],
});

const items: MenuItem[] = [
  {
    text: i18n.t("migration.mealie-pre-v1.title"),
    value: MIGRATIONS.mealie,
    divider: true,
  },
  {
    text: i18n.t("migration.chowdown.title"),
    value: MIGRATIONS.chowdown,
  },
  {
    text: i18n.t("migration.copymethat.title"),
    value: MIGRATIONS.copymethat,
  },
  {
    text: i18n.t("migration.myrecipebox.title"),
    value: MIGRATIONS.myrecipebox,
  },
  {
    text: i18n.t("migration.nextcloud.title"),
    value: MIGRATIONS.nextcloud,
  },
  {
    text: i18n.t("migration.paprika.title"),
    value: MIGRATIONS.paprika,
  },
  {
    text: i18n.t("migration.plantoeat.title"),
    value: MIGRATIONS.plantoeat,
  },
  {
    text: i18n.t("migration.recipekeeper.title"),
    value: MIGRATIONS.recipekeeper,
  },
  {
    text: i18n.t("migration.tandoor.title"),
    value: MIGRATIONS.tandoor,
  },
  {
    text: i18n.t("migration.cookn.title"),
    value: MIGRATIONS.cookn,
  },
];
const _content: Record<string, MigrationContent> = {
  [MIGRATIONS.mealie]: {
    text: i18n.t("migration.mealie-pre-v1.description-long"),
    acceptedFileType: ".zip",
    tree: [
      {
        icon: $globals.icons.zip,
        title: "mealie.zip",
        children: [
          {
            title: "recipes",
            icon: $globals.icons.folderOutline,
            children: [
              {
                title: "recipe-name",
                icon: $globals.icons.folderOutline,
                children: [
                  { title: "recipe-name.json", icon: $globals.icons.codeJson },
                  {
                    title: "images",
                    icon: $globals.icons.folderOutline,
                    children: [
                      { title: "original.webp", icon: $globals.icons.codeJson },
                      { title: "full.jpg", icon: $globals.icons.fileImage },
                      { title: "thumb.jpg", icon: $globals.icons.fileImage },
                    ],
                  },
                ],
              },
              {
                title: "recipe-name-1",
                icon: $globals.icons.folderOutline,
                children: [
                  { title: "recipe-name-1.json", icon: $globals.icons.codeJson },
                  {
                    title: "images",
                    icon: $globals.icons.folderOutline,
                    children: [
                      { title: "original.webp", icon: $globals.icons.codeJson },
                      { title: "full.jpg", icon: $globals.icons.fileImage },
                      { title: "thumb.jpg", icon: $globals.icons.fileImage },
                    ],
                  },
                ],
              },
            ],
          },
        ],
      },
    ],
  },
  [MIGRATIONS.chowdown]: {
    text: i18n.t("migration.chowdown.description-long"),
    acceptedFileType: ".zip",
    tree: [
      {
        icon: $globals.icons.zip,
        title: "chowdown-gh-pages.zip",
        children: [
          {
            title: "chowdown-gh-pages",
            icon: $globals.icons.folderOutline,
            children: [
              {
                title: "_recipes",
                icon: $globals.icons.folderOutline,
                children: [
                  { title: "recipe-one.md", icon: $globals.icons.codeJson },
                  { title: "recipe-two.md", icon: $globals.icons.codeJson },
                ],
              },
              {
                title: "images",
                icon: $globals.icons.folderOutline,
                children: [
                  { title: "recipe-one.jpg", icon: $globals.icons.fileImage },
                  { title: "recipe-two.jpg", icon: $globals.icons.fileImage },
                ],
              },
            ],
          },
        ],
      },
    ],
  },
  [MIGRATIONS.copymethat]: {
    text: i18n.t("migration.copymethat.description-long"),
    acceptedFileType: ".zip",
    tree: [
      {
        icon: $globals.icons.zip,
        title: "Copy_Me_That_20230306.zip",
        children: [
          {
            title: "images",
            icon: $globals.icons.folderOutline,
            children: [
              { title: "recipe_1_an5zy.jpg", icon: $globals.icons.fileImage },
              { title: "recipe_2_82el8.jpg", icon: $globals.icons.fileImage },
              { title: "recipe_3_j75qg.jpg", icon: $globals.icons.fileImage },
            ],
          },
          { title: "recipes.html", icon: $globals.icons.codeJson },
        ],
      },
    ],
  },
  [MIGRATIONS.myrecipebox]: {
    text: i18n.t("migration.myrecipebox.description-long"),
    acceptedFileType: ".csv",
    tree: false,
  },
  [MIGRATIONS.nextcloud]: {
    text: i18n.t("migration.nextcloud.description-long"),
    acceptedFileType: ".zip",
    tree: [
      {
        icon: $globals.icons.zip,
        title: "nextcloud.zip",
        children: [
          {
            title: i18n.t("migration.recipe-1"),
            icon: $globals.icons.folderOutline,
            children: [
              { title: "recipe.json", icon: $globals.icons.codeJson },
              { title: "full.jpg", icon: $globals.icons.fileImage },
              { title: "thumb.jpg", icon: $globals.icons.fileImage },
            ],
          },
          {
            title: i18n.t("migration.recipe-2"),
            icon: $globals.icons.folderOutline,
            children: [
              { title: "recipe.json", icon: $globals.icons.codeJson },
              { title: "full.jpg", icon: $globals.icons.fileImage },
              { title: "thumb.jpg", icon: $globals.icons.fileImage },
            ],
          },
        ],
      },
    ],
  },
  [MIGRATIONS.paprika]: {
    text: i18n.t("migration.paprika.description-long"),
    acceptedFileType: ".zip",
    tree: false,
  },
  [MIGRATIONS.plantoeat]: {
    text: i18n.t("migration.plantoeat.description-long"),
    acceptedFileType: ".zip,.csv,.txt",
    tree: false,
  },
  [MIGRATIONS.recipekeeper]: {
    text: i18n.t("migration.recipekeeper.description-long"),
    acceptedFileType: ".zip",
    tree: [
      {
        icon: $globals.icons.zip,
        title: "recipekeeperhtml.zip",
        children: [
          { title: "recipes.html", icon: $globals.icons.codeJson },
          {
            title: "images", icon: $globals.icons.folderOutline,
            children: [
              { title: "image1.jpg", icon: $globals.icons.fileImage },
              { title: "image2.jpg", icon: $globals.icons.fileImage },
            ],
          },
        ],
      },
    ],
  },
  [MIGRATIONS.tandoor]: {
    text: i18n.t("migration.tandoor.description-long"),
    acceptedFileType: ".zip",
    tree: [
      {
        icon: $globals.icons.zip,
        title: "tandoor_default_export_full_2023-06-29.zip",
        children: [
          {
            title: "1.zip",
            icon: $globals.icons.zip,
            children: [
              { title: "image.jpeg", icon: $globals.icons.fileImage },
              { title: "recipe.json", icon: $globals.icons.codeJson },
            ],
          },
          {
            title: "2.zip",
            icon: $globals.icons.zip,
            children: [
              { title: "image.jpeg", icon: $globals.icons.fileImage },
              { title: "recipe.json", icon: $globals.icons.codeJson },
            ],
          },
          {
            title: "3.zip",
            icon: $globals.icons.zip,
            children: [
              { title: "image.jpeg", icon: $globals.icons.fileImage },
              { title: "recipe.json", icon: $globals.icons.codeJson },
            ],
          },
        ],
      },
    ],
  },
  [MIGRATIONS.cookn]: {
    text: i18n.t("migration.cookn.description-long"),
    acceptedFileType: ".zip",
    tree: [
      {
        icon: $globals.icons.zip,
        title: "cookn.zip",
        children: [
          { title: "temp_brand.dsv", icon: $globals.icons.codeJson },
          { title: "temp_chapter_desc.dsv", icon: $globals.icons.codeJson },
          { title: "temp_chapter.dsv", icon: $globals.icons.codeJson },
          { title: "temp_cookBook_desc.dsv", icon: $globals.icons.codeJson },
          { title: "temp_cookBook.dsv", icon: $globals.icons.codeJson },
          { title: "temp_food_brand.dsv", icon: $globals.icons.codeJson },
          { title: "temp_food_group.dsv", icon: $globals.icons.codeJson },
          { title: "temp_food.dsv", icon: $globals.icons.codeJson },
          { title: "temp_ingredient.dsv", icon: $globals.icons.codeJson },
          { title: "temp_media.dsv", icon: $globals.icons.codeJson },
          { title: "temp_nutrient.dsv", icon: $globals.icons.codeJson },
          { title: "temp_recipe_desc.dsv", icon: $globals.icons.codeJson },
          { title: "temp_recipe.dsv", icon: $globals.icons.codeJson },
          { title: "temp_unit_equivalent.dsv", icon: $globals.icons.codeJson },
          { title: "temp_unit.dsv", icon: $globals.icons.codeJson },
          { title: "images", icon: $globals.icons.fileImage },
        ],
      },
    ],
  },
};

function addIdToNode(counter: number, node: TreeNode): number {
  node.id = counter;
  counter += 1;
  if (node.children) {
    node.children.forEach((child: TreeNode) => {
      counter = addIdToNode(counter, child);
    });
  }
  return counter;
}

for (const key in _content) {
  const migration = _content[key];
  if (migration.tree && Array.isArray(migration.tree)) {
    let counter = 1;
    migration.tree.forEach((node: TreeNode) => {
      counter = addIdToNode(counter, node);
    });
  }
}

function setFileObject(fileObject: File) {
  state.fileObject = fileObject;
}

async function startMigration() {
  state.loading = true;
  const payload = {
    addMigrationTag: state.addMigrationTag,
    migrationType: state.migrationType,
    archive: state.fileObject,
  };

  const { data } = await api.groupMigration.startMigration(payload);

  state.loading = false;

  if (data) {
    state.reports.unshift(data);
  }
}

async function getMigrationReports() {
  const { data } = await api.groupReports.getAll("migration");

  if (data) {
    state.reports = data;
  }
}

async function deleteReport(id: string) {
  await api.groupReports.deleteOne(id);
  getMigrationReports();
}

onMounted(() => {
  getMigrationReports();
});

const content = computed(() => {
  const data = _content[state.migrationType];

  if (data) {
    return data;
  }
  else {
    return {
      text: "",
      acceptedFileType: ".zip",
      tree: false,
    };
  }
});
</script>

<style lang="scss" scoped></style>
