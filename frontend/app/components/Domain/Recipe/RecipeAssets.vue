<template>
  <section
    v-if="model.length > 0 || edit"
    class="font-sans"
    :aria-label="$t('asset.assets')"
  >
    <h2
      v-if="!edit"
      class="m-0 mb-2 text-sm font-semibold text-muted-foreground"
    >
      {{ $t("asset.assets") }}
    </h2>
    <ul
      v-if="model.length"
      class="m-0 flex list-none flex-col gap-1 p-0"
    >
      <li
        v-for="(item, i) in model"
        :key="item.fileName ?? i"
        class="group/asset flex items-center gap-1 rounded-control transition-colors hover:bg-highlight/60"
      >
        <a
          :href="assetURL(item.fileName ?? '')"
          :target="isImage(item.fileName) ? undefined : '_blank'"
          rel="noopener"
          class="flex min-w-0 flex-1 items-center gap-3 p-1.5 text-[15px] text-foreground no-underline"
          @click="handleViewClick($event, item)"
        >
          <span class="flex size-11 shrink-0 items-center justify-center overflow-hidden rounded-item bg-muted">
            <img
              v-if="isImage(item.fileName)"
              :src="assetURL(item.fileName ?? '')"
              :alt="item.name"
              loading="lazy"
              class="size-full object-cover"
            >
            <MdiIcon
              v-else
              :path="getIconDefinition(item.icon).icon"
              class="size-6 text-muted-foreground"
            />
          </span>
          <span class="min-w-0 flex-1 truncate font-medium">{{ item.name }}</span>
        </a>
        <Button
          v-if="!edit"
          as="a"
          variant="ghost"
          size="icon"
          :href="assetURL(item.fileName ?? '')"
          download
          :aria-label="`${$t('general.download')}: ${item.name}`"
          :title="$t('general.download')"
        >
          <MdiIcon
            :path="$globals.icons.download"
            class="size-4"
          />
        </Button>
        <DropdownMenu
          v-else
          :modal="false"
        >
          <DropdownMenuTrigger as-child>
            <Button
              variant="ghost"
              size="icon"
              :aria-label="`${$t('general.menu')}: ${item.name}`"
            >
              <EllipsisVerticalIcon class="size-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            align="end"
            class="min-w-48"
          >
            <DropdownMenuItem as-child>
              <a
                :href="assetURL(item.fileName ?? '')"
                :target="isImage(item.fileName) ? undefined : '_blank'"
                rel="noopener"
                @click="handleViewClick($event, item)"
              >
                <MdiIcon
                  :path="$globals.icons.eye"
                  class="size-4"
                />
                {{ $t('general.view') }}
              </a>
            </DropdownMenuItem>
            <DropdownMenuItem as-child>
              <a
                :href="assetURL(item.fileName ?? '')"
                download
              >
                <MdiIcon
                  :path="$globals.icons.download"
                  class="size-4"
                />
                {{ $t('general.download') }}
              </a>
            </DropdownMenuItem>
            <DropdownMenuItem @select="copyText(assetEmbed(item.fileName ?? ''))">
              <MdiIcon
                :path="$globals.icons.contentCopy"
                class="size-4"
              />
              {{ $t('general.copy') }}
            </DropdownMenuItem>
            <DropdownMenuItem
              variant="destructive"
              @select="model.splice(i, 1)"
            >
              <MdiIcon
                :path="$globals.icons.delete"
                class="size-4"
              />
              {{ $t('general.delete') }}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </li>
    </ul>
    <p
      v-else
      class="m-0 rounded-card border border-dashed px-4 py-6 text-center text-sm text-muted-foreground"
    >
      {{ $t('asset.no-assets-yet') }}
    </p>
    <div
      v-if="edit"
      class="mt-4 flex justify-end"
    >
      <Button
        variant="outline"
        @click="state.newAssetDialog = true"
      >
        <PlusIcon class="size-4" />
        {{ $t('asset.new-asset') }}
      </Button>
    </div>

    <RecipeImageLightbox
      v-if="lightbox.open"
      v-model="lightbox.open"
      v-model:index="lightbox.index"
      :items="lightboxItems"
    />
    <BaseDialog
      v-model="state.newAssetDialog"
      :title="$t('asset.new-asset')"
      :icon="getIconDefinition(state.newAsset.icon).icon"
      can-submit
      :submit-disabled="!state.fileObject?.name"
      @submit="addAsset"
    >
      <div class="flex flex-col gap-4 px-6 pb-2">
        <div class="flex flex-wrap items-center gap-3">
          <Button
            variant="outline"
            @click="assetFileInput?.click()"
          >
            <MdiIcon
              :path="$globals.icons.upload"
              class="size-4"
            />
            {{ $t('asset.choose-file') }}
          </Button>
          <span class="min-w-0 flex-1 truncate text-sm text-muted-foreground">
            {{ state.fileObject?.name || $t('asset.no-file-chosen') }}
          </span>
          <input
            ref="assetFileInput"
            type="file"
            class="display-none"
            @change="onAssetFile"
          >
        </div>
        <TextField
          v-model="state.newAsset.name"
          :label="$t('general.name')"
        />
        <SelectField
          v-model="state.newAsset.icon"
          :label="$t('asset.icon')"
          :items="iconOptions"
          item-title="title"
          item-value="name"
        />
      </div>
    </BaseDialog>
  </section>
</template>

<script setup lang="ts">
import { EllipsisVerticalIcon, PlusIcon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "~/components/ui/dropdown-menu";
import SelectField from "~/components/ui/field/SelectField.vue";
import TextField from "~/components/ui/field/TextField.vue";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { useStaticRoutes, useUserApi } from "~/composables/api";
import { alert } from "~/composables/use-toast";
import type { RecipeAsset } from "~/lib/api/types/recipe";
import { useCopy } from "~/composables/use-copy";
import { isImage, useRecipeLightboxItems, findLightboxStartIndex } from "~/composables/recipe-page/use-recipe-lightbox-items";

const props = defineProps({
  slug: {
    type: String,
    required: true,
  },
  recipeId: {
    type: String,
    required: true,
  },
  edit: {
    type: Boolean,
    default: true,
  },
  // Optional so the lightbox can open a gallery that includes the recipe's hero image
  // ahead of the asset list; omit when the caller has no hero to show (or doesn't care).
  heroImageUrl: {
    type: String,
    default: undefined,
  },
  heroImageAlt: {
    type: String,
    default: undefined,
  },
});

const model = defineModel<RecipeAsset[]>({ required: true });

const api = useUserApi();

const state = reactive({
  newAssetDialog: false,
  fileObject: {} as File,
  newAsset: {
    name: "",
    icon: "mdi-file",
  },
});

const i18n = useI18n();
const { $globals } = useNuxtApp();
const { copyText } = useCopy();

const iconOptions = [
  {
    name: "mdi-file",
    title: i18n.t("asset.file"),
    icon: $globals.icons.file,
  },
  {
    name: "mdi-file-pdf-box",
    title: i18n.t("asset.pdf"),
    icon: $globals.icons.filePDF,
  },
  {
    name: "mdi-file-image",
    title: i18n.t("asset.image"),
    icon: $globals.icons.fileImage,
  },
  {
    name: "mdi-code-json",
    title: i18n.t("asset.code"),
    icon: $globals.icons.codeJson,
  },
  {
    name: "mdi-silverware-fork-knife",
    title: i18n.t("asset.recipe"),
    icon: $globals.icons.primary,
  },
];

const serverBase = useRequestURL().origin;

function getIconDefinition(icon: string) {
  return iconOptions.find(item => item.name === icon) || iconOptions[0];
}

const { buildItems } = useRecipeLightboxItems();
const lightboxItems = computed(() => buildItems(props.recipeId, {
  heroUrl: props.heroImageUrl,
  heroAlt: props.heroImageAlt,
  assets: model.value,
}));

const lightbox = reactive({
  open: false,
  index: 0,
});

function openLightbox(item: RecipeAsset) {
  lightbox.index = findLightboxStartIndex(lightboxItems.value, assetURL(item.fileName ?? ""));
  lightbox.open = true;
}

function handleViewClick(event: Event, item: RecipeAsset) {
  if (!isImage(item.fileName)) {
    return;
  }

  event.preventDefault();
  openLightbox(item);
}

const { recipeAssetPath } = useStaticRoutes();
function assetURL(assetName: string) {
  return recipeAssetPath(props.recipeId, assetName);
}

function assetEmbed(name: string) {
  return `<img src="${serverBase}${assetURL(name)}" height="100%" width="100%" />`;
}

const assetFileInput = ref<HTMLInputElement>();
function onAssetFile(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";
  if (file) {
    setFileObject(file);
  }
}

function setFileObject(fileObject: File) {
  state.fileObject = fileObject;
  // If the user didn't provide a name, default to the file base name
  if (!state.newAsset.name?.trim()) {
    state.newAsset.name = fileObject.name.substring(0, fileObject.name.lastIndexOf("."));
  }
}

function validFields() {
  // Only require a file; name will fall back to the file name if empty
  return Boolean(state.fileObject?.name);
}

async function addAsset() {
  if (!validFields()) {
    alert.error(i18n.t("asset.error-submitting-form") as string);
    return;
  }

  const nameToUse = state.newAsset.name?.trim() || state.fileObject.name;

  const { data } = await api.recipes.createAsset(props.slug, {
    name: nameToUse,
    icon: state.newAsset.icon,
    file: state.fileObject,
    extension: state.fileObject.name.split(".").pop() || "",
  });
  if (data) {
    model.value = [...model.value, data];
  }
  state.newAsset = { name: "", icon: "mdi-file" };
  state.fileObject = {} as File;
}
</script>
