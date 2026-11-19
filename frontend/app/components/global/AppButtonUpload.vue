<template>
  <div class="inline-flex">
    <input
      ref="uploader"
      class="display-none"
      type="file"
      :accept="accept"
      :multiple="multiple"
      @change="onFileChanged"
    >
    <slot v-bind="{ isSelecting, onButtonClick }">
      <Button
        :size="small ? 'sm' : 'default'"
        :variant="textBtn ? 'ghost' : 'outline'"
        :disabled="disabled || isSelecting"
        @click="onButtonClick"
      >
        <LoaderCircleIcon
          v-if="isSelecting"
          class="size-4 animate-spin"
        />
        <MdiIcon
          v-else
          :path="effIcon"
          class="size-4"
        />
        {{ text ? text : defaultText }}
      </Button>
    </slot>
  </div>
</template>

<script setup lang="ts">
import { LoaderCircleIcon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { useUserApi } from "~/composables/api";

const UPLOAD_EVENT = "uploaded";

const props = defineProps({
  small: {
    type: Boolean,
    default: false,
  },
  post: {
    type: Boolean,
    default: true,
  },
  url: {
    type: String,
    default: "",
  },
  text: {
    type: String,
    default: "",
  },
  icon: {
    type: String,
    default: null,
  },
  fileName: {
    type: String,
    default: "archive",
  },
  textBtn: {
    type: Boolean,
    default: true,
  },
  accept: {
    type: String,
    default: "",
  },
  color: {
    type: String,
    default: "info",
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  multiple: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits<{
  (e: "uploaded", payload: File | File[] | unknown | null): void;
}>();

const selectedFiles = ref<File[]>([]);
const uploader = ref<HTMLInputElement | null>(null);
const isSelecting = ref(false);

const i18n = useI18n();
const { $globals } = useNuxtApp();
const effIcon = props.icon ? props.icon : $globals.icons.upload;

const defaultText = i18n.t("general.upload");

const api = useUserApi();
async function upload() {
  if (selectedFiles.value.length === 0) {
    return;
  }

  isSelecting.value = true;

  if (!props.post) {
    emit(UPLOAD_EVENT, props.multiple ? selectedFiles.value : selectedFiles.value[0]);
    isSelecting.value = false;
    return;
  }

  if (props.multiple && selectedFiles.value.length > 1) {
    console.warn("Multiple file uploads are not supported by the API.");
    return;
  }

  const file = selectedFiles.value[0];
  const formData = new FormData();
  formData.append(props.fileName, file);

  try {
    const response = await api.upload.file(props.url, formData);
    if (response) {
      emit(UPLOAD_EVENT, response);
    }
  }
  catch (e) {
    console.error(e);
    emit(UPLOAD_EVENT, null);
  }

  isSelecting.value = false;
}

function onFileChanged(e: Event) {
  const target = e.target as HTMLInputElement;

  if (target.files !== null && target.files.length > 0) {
    selectedFiles.value = Array.from(target.files);
    upload();
  }
}

function onButtonClick() {
  isSelecting.value = true;
  window.addEventListener(
    "focus",
    () => {
      isSelecting.value = false;
    },
    { once: true },
  );
  uploader.value?.click();
}
</script>

<style></style>
