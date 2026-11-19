<template>
  <div class="font-sans">
    <BaseDialog
      v-model="recipeEventEditDialog"
      :title="$t('recipe.edit-timeline-event')"
      :icon="$globals.icons.edit"
      can-submit
      disable-submit-on-enter
      :submit-text="$t('general.save')"
      @submit="submitEdit"
    >
      <div class="flex flex-col gap-1 px-6 pb-2">
        <TextField
          v-model="localEvent.subject"
          :label="$t('general.subject')"
        />
        <TextareaField
          v-model="localEvent.eventMessage"
          :label="$t('general.message')"
          :rows="4"
        />
        <div class="mt-2 flex flex-col gap-3">
          <img
            v-if="hasExistingImage"
            :src="imageUrl"
            alt=""
            class="max-h-72 w-full rounded-card border object-contain"
          >
          <ImageCropper
            v-if="newImage && newImagePreviewUrl"
            :img="newImagePreviewUrl"
            cropper-width="100%"
            @save="updateUploadedImage"
          />
          <div class="flex justify-end">
            <AppButtonUpload
              v-if="!newImage && !hasExistingImage"
              url="none"
              file-name="image"
              accept="image/*"
              :text="$t('recipe.upload-image')"
              :text-btn="false"
              :post="false"
              @uploaded="uploadImage"
            />
            <Button
              v-else
              type="button"
              variant="ghost"
              class="text-destructive hover:text-destructive"
              @click="clearImage"
            >
              <XIcon class="size-4" />
              {{ $t("recipe.remove-image") }}
            </Button>
          </div>
        </div>
      </div>
    </BaseDialog>

    <BaseDialog
      v-model="recipeEventDeleteDialog"
      :title="$t('events.delete-event')"
      color="error"
      :icon="$globals.icons.alertCircle"
      can-confirm
      @confirm="$emit('delete')"
    >
      <p class="m-0 px-6 pb-2 text-[15px]">
        {{ $t('events.event-delete-confirmation') }}
      </p>
    </BaseDialog>

    <DropdownMenu :modal="false">
      <DropdownMenuTrigger as-child>
        <button
          type="button"
          class="inline-flex size-9 items-center justify-center rounded-full text-muted-foreground hover:bg-highlight hover:text-foreground print:hidden"
          :aria-label="$t('general.options-for', { name: event.subject })"
          @click.prevent
        >
          <MdiIcon
            :path="icon"
            class="size-5"
          />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent :align="menuTop ? 'end' : 'end'">
        <DropdownMenuItem
          v-for="(item, index) in menuItems"
          :key="index"
          :variant="item.color === 'error' ? 'destructive' : 'default'"
          @select="contextMenuEventHandler(item.event)"
        >
          <MdiIcon
            :path="item.icon"
            class="size-4"
          />
          {{ item.title }}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  </div>
</template>

<script setup lang="ts">
import { XIcon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "~/components/ui/dropdown-menu";
import TextareaField from "~/components/ui/field/TextareaField.vue";
import TextField from "~/components/ui/field/TextField.vue";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { useI18n, useNuxtApp } from "#imports";
import type { RecipeTimelineEventOut, RecipeTimelineEventUpdate } from "~/lib/api/types/recipe";

export interface TimelineContextMenuIncludes {
  edit: boolean;
  delete: boolean;
}

export interface TimelineEventEdit {
  event: RecipeTimelineEventUpdate;
  image?: { file: Blob | File; fileName: string };
}

export interface ContextMenuItem {
  title: string;
  icon: string;
  color: string | undefined;
  event: string;
}

const props = defineProps<{
  useItems?: TimelineContextMenuIncludes;
  appendItems?: ContextMenuItem[];
  leadingItems?: ContextMenuItem[];
  menuTop?: boolean;
  fab?: boolean;
  elevation?: number | null;
  color?: string;
  event: RecipeTimelineEventOut;
  imageUrl?: string;
  menuIcon?: string | null;
}>();

const emit = defineEmits(["delete", "update"]);

const recipeEventEditDialog = ref(false);
const recipeEventDeleteDialog = ref(false);
const loading = ref(false);

const i18n = useI18n();
const { $globals } = useNuxtApp();

const defaultItems: { [key: string]: ContextMenuItem } = {
  edit: {
    title: i18n.t("general.edit"),
    icon: $globals.icons.edit,
    color: undefined,
    event: "edit",
  },
  delete: {
    title: i18n.t("general.delete"),
    icon: $globals.icons.delete,
    color: "error",
    event: "delete",
  },
};

const menuItems = computed(() => {
  const items: ContextMenuItem[] = [];
  const useItems = props.useItems ?? { edit: true, delete: true };
  for (const [key, value] of Object.entries(useItems)) {
    if (value) {
      const item = defaultItems[key];
      if (item) items.push(item);
    }
  }
  return [
    ...items,
    ...(props.leadingItems ?? []),
    ...(props.appendItems ?? []),
  ];
});

const icon = computed(() => props.menuIcon || $globals.icons.dotsVertical);

const localEvent = ref({ ...props.event });
watch(() => props.event, (val) => {
  localEvent.value = { ...val };
});

const newImage = ref<Blob | File>();
const newImageName = ref("");
const newImagePreviewUrl = ref<string>();
const removeExistingImage = ref(false);
const hasExistingImage = computed(() => !!props.imageUrl && !removeExistingImage.value && !newImage.value);

function uploadImage(fileObject: File) {
  newImage.value = fileObject;
  newImageName.value = fileObject.name;
  newImagePreviewUrl.value = URL.createObjectURL(fileObject);
}

function updateUploadedImage(fileObject: Blob) {
  newImage.value = fileObject;
  newImagePreviewUrl.value = URL.createObjectURL(fileObject);
}

function clearImage() {
  newImage.value = undefined;
  newImageName.value = "";
  newImagePreviewUrl.value = undefined;
  removeExistingImage.value = true;
}

function openEditDialog() {
  localEvent.value = { ...props.event };
  newImage.value = undefined;
  newImageName.value = "";
  newImagePreviewUrl.value = undefined;
  removeExistingImage.value = false;
  recipeEventEditDialog.value = true;
}
function openDeleteDialog() {
  recipeEventDeleteDialog.value = true;
}
function contextMenuEventHandler(eventKey: string) {
  if (eventKey === "edit") {
    openEditDialog();
    loading.value = false;
    return;
  }
  if (eventKey === "delete") {
    openDeleteDialog();
    loading.value = false;
    return;
  }
  emit(eventKey as "delete" | "update");
  loading.value = false;
}
function submitEdit() {
  const edit: TimelineEventEdit = {
    event: {
      ...localEvent.value,
      image: removeExistingImage.value ? "does not have image" : localEvent.value.image,
    },
    image: newImage.value ? { file: newImage.value, fileName: newImageName.value } : undefined,
  };
  emit("update", edit);
  recipeEventEditDialog.value = false;
}
</script>
