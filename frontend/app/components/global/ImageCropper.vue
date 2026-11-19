<template>
  <div class="overflow-hidden rounded-card border bg-card font-sans">
    <div class="flex items-center gap-1 border-b px-2 py-1.5">
      <button
        v-for="control in controls.flat()"
        :key="control.label"
        type="button"
        class="inline-flex size-8 items-center justify-center rounded-item text-muted-foreground hover:bg-highlight hover:text-foreground disabled:opacity-40"
        :disabled="submitted"
        :aria-label="$t(control.label)"
        :title="$t(control.label)"
        @click="control.callback()"
      >
        <MdiIcon
          :path="control.icon"
          class="size-[18px]"
        />
      </button>
      <span class="flex-1" />
      <Button
        v-if="changed"
        type="button"
        size="sm"
        :disabled="submitted"
        @click="save"
      >
        {{ $t('general.save') }}
      </Button>
      <button
        type="button"
        class="inline-flex size-8 items-center justify-center rounded-item text-muted-foreground hover:bg-destructive/10 hover:text-destructive disabled:opacity-40"
        :disabled="submitted"
        :aria-label="$t('general.delete')"
        :title="$t('general.delete')"
        @click="$emit('delete')"
      >
        <Trash2Icon class="size-4" />
      </button>
    </div>
    <Cropper
      ref="cropper"
      class="cropper"
      :src="img"
      :default-size="defaultSize"
      :style="`width: ${cropperWidth}; aspect-ratio: ${aspectRatio};`"
      @change="changed = changed + 1"
      @ready="onReady"
    />
  </div>
</template>

<script setup lang="ts">
import { Trash2Icon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { Cropper } from "vue-advanced-cropper";
import "vue-advanced-cropper/dist/style.css";

defineProps({
  img: {
    type: String,
    required: true,
  },
  cropperWidth: {
    type: String,
    default: undefined,
  },
  submitted: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits<{
  (e: "save", item: Blob): void;
  (e: "delete"): void;
}>();

const cropper = ref<any>(null);
const changed = ref(0);
// Left to the cropper's own sizing until the image is rotated; see rotate().
const aspectRatio = ref<string | number>("auto");
const { $globals } = useNuxtApp();

function onReady() {
  aspectRatio.value = "auto";
  changed.value = -1;
}

type Control = {
  color: string;
  label: string;
  icon: string;
  callback: CallableFunction;
};

function flip(hortizontal: boolean, vertical?: boolean) {
  if (!cropper.value) return;
  cropper.value.flip(hortizontal, vertical);
  changed.value = changed.value + 1;
}

async function rotate(angle: number) {
  if (!cropper.value) return;
  cropper.value.rotate(angle);
  changed.value = changed.value + 1;

  // A quarter turn swaps the image's width and height. Pin the box to the new
  // orientation, otherwise the cropper keeps the visible area it computed for
  // the old one and part of the rotated image ends up outside of it.
  const { image } = cropper.value.getResult();
  const quarterTurned = Math.abs(image.transforms.rotate % 180) === 90;
  aspectRatio.value = quarterTurned ? image.height / image.width : image.width / image.height;

  // the cropper measures its own box, so let the new size land first
  await nextTick();
  cropper.value.refresh();
}

const controls = ref<Control[][]>([
  [
    {
      color: "info",
      label: "recipe.flip-horizontal",
      icon: $globals.icons.flipHorizontal,
      callback: () => flip(true, false),
    },
    {
      color: "info",
      label: "recipe.flip-vertical",
      icon: $globals.icons.flipVertical,
      callback: () => flip(false, true),
    },
  ],
  [
    {
      color: "info",
      label: "recipe.rotate-left",
      icon: $globals.icons.rotateLeft,
      callback: () => rotate(-90),
    },
    {
      color: "info",
      label: "recipe.rotate-right",
      icon: $globals.icons.rotateRight,
      callback: () => rotate(90),
    },
  ],
]);

function save() {
  if (!cropper.value) return;
  const { canvas } = cropper.value.getResult();
  if (!canvas) return;
  canvas.toBlob((blob) => {
    if (blob) {
      emit("save", blob);
    }
  });
}

function defaultSize({ imageSize, visibleArea }: any) {
  return {
    width: (visibleArea || imageSize).width,
    height: (visibleArea || imageSize).height,
  };
}
</script>
