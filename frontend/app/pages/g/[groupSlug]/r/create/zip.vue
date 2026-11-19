<template>
  <form
    class="rounded-panel border bg-card p-5 font-sans sm:p-6"
    @submit.prevent="createByZip"
  >
    <h2 class="m-0 text-xl font-bold tracking-tight">
      {{ $t('recipe.import-from-zip') }}
    </h2>
    <p class="m-0 mt-1 text-[15px] text-muted-foreground">
      {{ $t('recipe.import-from-zip-description') }}
    </p>
    <div class="mt-4 flex flex-wrap items-center gap-3">
      <AppButtonUpload
        accept=".zip"
        :post="false"
        file-name="file"
        :text="$t('recipe.choose-zip-file')"
        :text-btn="false"
        @uploaded="newRecipeZip = $event"
      />
      <span
        class="min-w-0 truncate text-sm"
        :class="newRecipeZip ? 'font-semibold' : 'text-muted-foreground'"
      >{{ newRecipeZip?.name || $t('migration.no-file-selected') }}</span>
      <button
        v-if="newRecipeZip"
        type="button"
        class="inline-flex size-8 items-center justify-center rounded-full text-muted-foreground hover:bg-highlight"
        :aria-label="$t('general.clear')"
        @click="newRecipeZip = null"
      >
        <XIcon class="size-4" />
      </button>
    </div>
    <p class="m-0 mt-2 text-sm text-muted-foreground">
      {{ $t('recipe.zip-files-must-have-been-exported-from-mealie') }}
    </p>
    <div class="mt-5 flex flex-wrap items-center justify-end gap-3 border-t pt-4">
      <Button
        type="submit"
        :disabled="newRecipeZip === null || state.loading"
      >
        <LoaderCircleIcon
          v-if="state.loading"
          class="size-4 animate-spin"
        />
        {{ $t('recipe.import-recipe') }}
      </Button>
    </div>
  </form>
</template>

<script setup lang="ts">
import { LoaderCircleIcon, XIcon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import { useUserApi } from "~/composables/api";
import { useGlobalI18n } from "~/composables/use-global-i18n";
import { alert } from "~/composables/use-toast";

const state = reactive({
  loading: false,
});
const auth = useMealieAuth();
const route = useRoute();
const groupSlug = computed(() => route.params.groupSlug as string || auth.user.value?.groupSlug || "");

const api = useUserApi();
const router = useRouter();

const newRecipeZip = ref<File | null>(null);
const newRecipeZipFileName = "archive";

async function createByZip() {
  if (!newRecipeZip.value) {
    return;
  }
  const formData = new FormData();
  formData.append(newRecipeZipFileName, newRecipeZip.value);

  try {
    const response = await api.upload.file("/api/recipes/create/zip", formData);
    if (response?.status !== 201) {
      throw new Error("Failed to upload zip");
    }
    router.push(`/g/${groupSlug.value}/r/${response.data}`);
  }
  catch (error) {
    console.error(error);
    const i18n = useGlobalI18n();
    alert.error(i18n.t("events.something-went-wrong"));
  }
  finally {
    state.loading = false;
  }
}
</script>
