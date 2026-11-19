<template>
  <BaseDialog
    v-model="dialog"
    :title="$t('recipe-share.share-recipe')"
    :icon="$globals.icons.link"
  >
    <div
      v-if="qrCodeToken"
      class="flex flex-col items-center gap-3 px-6 pb-4 font-sans"
    >
      <img
        class="block h-auto w-full max-w-80 rounded-card bg-white p-2"
        :src="qrCodeDataUrl"
        :alt="$t('recipe-share.scan-qr-code')"
      >
      <p class="m-0 text-center text-sm text-muted-foreground">
        {{ $t("recipe-share.scan-qr-code") }}
      </p>
      <div class="flex gap-2">
        <Button
          variant="ghost"
          @click="qrCodeToken = null"
        >
          <ArrowLeftIcon class="size-4" />
          {{ $t("general.back") }}
        </Button>
        <Button
          variant="outline"
          @click="downloadQrCode"
        >
          <MdiIcon
            :path="$globals.icons.download"
            class="size-4"
          />
          {{ $t("general.download") }}
        </Button>
      </div>
    </div>
    <div
      v-else
      class="flex flex-col gap-4 px-6 pb-4 font-sans"
    >
      <p class="m-0 text-sm text-muted-foreground">
        {{ $t("recipe-share.share-link-explainer") }}
      </p>
      <div class="flex flex-wrap items-end gap-2">
        <div class="min-w-48 flex-1">
          <DateField
            v-model="expirationDate"
            :label="$t('recipe-share.expiration-date')"
            :hint="$t('recipe-share.default-30-days')"
            :min="new Date()"
            required
          />
        </div>
        <Button
          class="mb-7"
          @click="createNewToken"
        >
          <PlusIcon class="size-4" />
          {{ $t("recipe-share.create-link") }}
        </Button>
      </div>
      <ul
        v-if="tokens.length"
        class="m-0 flex list-none flex-col gap-1 border-t p-0 pt-3"
      >
        <li
          v-for="token in tokens"
          :key="token.id"
          class="flex items-center gap-1 rounded-control hover:bg-highlight/60"
        >
          <button
            type="button"
            class="flex min-w-0 flex-1 items-center gap-3 px-2 py-2 text-left text-[15px]"
            @click="shareRecipe(token.id)"
          >
            <span class="flex size-9 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground">
              <MdiIcon
                :path="$globals.icons.link"
                class="size-4"
              />
            </span>
            <span class="min-w-0 flex-1">
              {{ $t("recipe-share.expires-at") + ' ' + $d(new Date(token.expiresAt!)) }}
            </span>
          </button>
          <Button
            variant="ghost"
            size="icon"
            :aria-label="$t('general.copy')"
            :title="$t('general.copy')"
            @click="copyTokenLink(token.id)"
          >
            <MdiIcon
              :path="$globals.icons.contentCopy"
              class="size-4"
            />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            :aria-label="$t('recipe-share.show-qr-code')"
            :title="$t('recipe-share.show-qr-code')"
            @click="qrCodeToken = token.id"
          >
            <MdiIcon
              :path="$globals.icons.qrCode"
              class="size-4"
            />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            class="text-muted-foreground hover:text-destructive"
            :aria-label="$t('general.delete')"
            :title="$t('general.delete')"
            @click="deleteToken(token.id)"
          >
            <MdiIcon
              :path="$globals.icons.delete"
              class="size-4"
            />
          </Button>
        </li>
      </ul>
    </div>
  </BaseDialog>
</template>

<script setup lang="ts">
import { ArrowLeftIcon, PlusIcon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import DateField from "~/components/ui/field/DateField.vue";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { useClipboard, useShare, whenever } from "@vueuse/core";
import { renderSVG } from "uqr";
import type { RecipeShareTokenOut } from "~/lib/api/types/recipe";
import { useUserApi } from "~/composables/api";
import { alert } from "~/composables/use-toast";

interface Props {
  recipeId: string;
  name: string;
}
const props = defineProps<Props>();

const dialog = defineModel<boolean>({ default: false });

const expirationDate = ref(new Date(Date.now() - new Date().getTimezoneOffset() * 60000));
const tokens = ref<RecipeShareTokenOut[]>([]);
const qrCodeToken = ref<string | null>(null);

whenever(
  () => dialog.value,
  () => {
    // Set expiration date to today + 30 Days
    const today = new Date();
    expirationDate.value = new Date(today.getTime() + 30 * 24 * 60 * 60 * 1000);
    qrCodeToken.value = null;
    refreshTokens();
  },
);

const i18n = useI18n();
const auth = useMealieAuth();
const route = useRoute();
const groupSlug = computed(() => route.params.groupSlug as string || auth.user.value?.groupSlug || "");

// ============================================================
// Token Actions

const userApi = useUserApi();

async function createNewToken() {
  // Convert expiration date to timestamp
  const { data } = await userApi.recipes.share.createOne({
    recipeId: props.recipeId,
    expiresAt: expirationDate.value.toISOString(),
  });

  if (data) {
    tokens.value.push(data);
  }
}

async function deleteToken(id: string) {
  await userApi.recipes.share.deleteOne(id);
  tokens.value = tokens.value.filter(token => token.id !== id);
}

async function refreshTokens() {
  const { data } = await userApi.recipes.share.getAll(1, -1, { recipe_id: props.recipeId });

  if (data) {
    // @ts-expect-error - TODO: This routes doesn't have pagination, but the type are mismatched.
    tokens.value = data ?? [];
  }
}

const { share, isSupported: shareIsSupported } = useShare();
const { copy, copied, isSupported } = useClipboard({ legacy: true });

function getTokenLink(token: string) {
  return `${window.location.origin}/g/${groupSlug.value}/shared/r/${token}`;
}

async function copyTokenLink(token: string) {
  if (isSupported.value) {
    await copy(getTokenLink(token));
    if (copied.value) {
      alert.success(i18n.t("recipe-share.recipe-link-copied-message") as string);
    }
    else {
      alert.error(i18n.t("general.clipboard-copy-failure") as string);
    }
  }
  else {
    alert.error(i18n.t("general.clipboard-not-supported") as string);
  }
}

async function shareRecipe(token: string) {
  if (shareIsSupported.value) {
    share({
      title: props.name,
      url: getTokenLink(token),
    });
  }
  else {
    await copyTokenLink(token);
  }
}

// ============================================================
// QR Code

const qrCodeDataUrl = computed(() => qrCodeToken.value
  ? `data:image/svg+xml;charset=utf-8,${encodeURIComponent(renderSVG(getTokenLink(qrCodeToken.value)))}`
  : "");

async function downloadQrCode() {
  // Rasterize the SVG so the download opens in any photo viewer
  const image = new Image();
  image.src = qrCodeDataUrl.value;
  await image.decode();

  const size = 1024;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const context = canvas.getContext("2d");
  if (!context) {
    return;
  }
  context.imageSmoothingEnabled = false;
  context.drawImage(image, 0, 0, size, size);

  const a = document.createElement("a");
  a.download = `${props.name}.png`;
  a.href = canvas.toDataURL("image/png");
  a.click();
}
</script>
