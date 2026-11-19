<template>
  <div class="mx-auto flex w-full max-w-[760px] flex-col gap-6 px-4 pb-16 pt-3 font-sans sm:px-6 lg:pt-8">
    <header>
      <h1 class="m-0 text-[26px] font-bold tracking-tight sm:text-[32px]">
        {{ $t('admin.debug-ai-providers') }}
      </h1>
      <p class="m-0 mt-1 max-w-[65ch] text-[15px] text-muted-foreground">
        {{ $t('admin.debug-ai-providers-description') }}
      </p>
      <DocLink
        class="mt-2"
        link="/documentation/getting-started/installation/ai-providers"
      />
    </header>

    <form
      class="rounded-panel border bg-card p-5 sm:p-6"
      @submit.prevent="testOpenAI"
    >
      <div class="grid gap-x-4 sm:grid-cols-2">
        <SelectField
          v-if="groups"
          v-model="selectedGroupId"
          :items="groups"
          item-title="name"
          item-value="id"
          :label="$t('group.group')"
        />
        <SelectField
          v-model="selectedProviderId"
          :items="groupProviders"
          item-title="name"
          item-value="id"
          :label="$t('group.ai-provider-settings.ai-provider')"
          :disabled="!selectedGroupId"
        />
      </div>
      <div class="mt-3 flex flex-wrap items-center gap-3">
        <AppButtonUpload
          v-if="!uploadedImage"
          url="none"
          file-name="image"
          accept="image/*"
          :text="$t('recipe.upload-image')"
          :text-btn="false"
          :post="false"
          @uploaded="uploadImage"
        />
        <template v-else>
          <img
            v-if="uploadedImagePreviewUrl"
            :src="uploadedImagePreviewUrl"
            alt=""
            class="size-20 rounded-control border object-cover"
          >
          <Button
            type="button"
            variant="ghost"
            class="text-destructive hover:text-destructive"
            @click="clearImage"
          >
            <XIcon class="size-4" />
            {{ $t("recipe.remove-image") }}
          </Button>
        </template>
      </div>
      <div class="mt-5 flex justify-end border-t pt-4">
        <Button
          type="submit"
          :disabled="!selectedProviderId || loading"
        >
          <LoaderCircleIcon
            v-if="loading"
            class="size-4 animate-spin"
          />
          {{ $t('admin.run-test') }}
        </Button>
      </div>
    </form>

    <section v-if="response">
      <h2 class="m-0 mb-2 text-base font-semibold">
        {{ $t('admin.test-results') }}
      </h2>
      <pre class="m-0 overflow-x-auto rounded-card border bg-muted p-4 text-sm whitespace-pre-wrap">{{ response }}</pre>
    </section>
  </div>
</template>

<script setup lang="ts">
import { LoaderCircleIcon, XIcon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import SelectField from "~/components/ui/field/SelectField.vue";
import { useAdminApi } from "~/composables/api";
import { useGroups } from "~/composables/use-groups";
import { alert } from "~/composables/use-toast";
import type { AIProviderSummary } from "~/lib/api/types/group";

definePageMeta({
  layout: "admin",
});

const api = useAdminApi();
const i18n = useI18n();

// Set page title
useSeoMeta({
  title: i18n.t("admin.debug-ai-providers"),
});

const loading = ref(false);
const response = ref("");

const uploadedImage = ref<Blob | File>();
const uploadedImageName = ref<string>("");
const uploadedImagePreviewUrl = ref<string>();

// Group + provider selection
const { groups } = useGroups();
const selectedGroupId = ref<string | null>(null);
const groupProviders = ref<AIProviderSummary[]>([]);
const selectedProviderId = ref<string | null>(null);

watch(selectedGroupId, (id) => {
  groupProviders.value = [];
  selectedProviderId.value = null;
  if (!id) return;
  const group = groups.value?.find(g => g.id === id);
  groupProviders.value = group?.aiProviderSettings?.providers ?? [];
});

function uploadImage(fileObject: unknown) {
  uploadedImage.value = fileObject as File;
  uploadedImageName.value = (fileObject as File).name;
  uploadedImagePreviewUrl.value = URL.createObjectURL(fileObject as File);
}

function clearImage() {
  uploadedImage.value = undefined;
  uploadedImageName.value = "";
  uploadedImagePreviewUrl.value = undefined;
}

async function testOpenAI() {
  if (!selectedProviderId.value) {
    alert.error("Please select a provider");
    return;
  }

  response.value = "";

  loading.value = true;
  const { data } = await api.debug.debugOpenAI(selectedProviderId.value, uploadedImage.value);
  loading.value = false;

  if (!data) {
    alert.error("Unable to test AI services");
  }
  else {
    response.value = data.response || (data.success ? "Test Successful" : "Test Failed");
  }
}
</script>
