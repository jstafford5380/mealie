<template>
  <div class="mx-auto w-full max-w-[1400px] px-4 pb-16 pt-3 font-sans sm:px-6 lg:pt-8">
    <!-- Edit Dialog -->
    <BaseDialog
      v-if="editTarget"
      v-model="dialogStates.edit"
      width="100%"
      max-width="1100px"
      :icon="$globals.icons.pages"
      :title="$t('general.edit')"
      :submit-icon="$globals.icons.save"
      :submit-text="$t('general.save')"
      :submit-disabled="!editTarget.queryFilterString"
      can-submit
      disable-submit-on-enter
      @submit="editCookbook"
    >
      <div class="px-6 pb-2">
        <CookbookEditor v-model="editTarget" />
      </div>
    </BaseDialog>

    <template v-if="book">
      <header class="mb-5 flex flex-wrap items-start gap-3">
        <div class="min-w-0 flex-1">
          <h1 class="m-0 text-[26px] font-bold tracking-tight sm:text-[32px]">
            {{ book.name }}
          </h1>
          <SafeMarkdown
            v-if="book.description"
            :source="book.description"
            class="mt-1 max-w-[65ch] text-[15px] text-muted-foreground"
          />
        </div>
        <div class="flex flex-wrap gap-2">
          <Button
            v-if="isOwnGroup"
            variant="outline"
            :disabled="downloadingPdf"
            @click="downloadPdf"
          >
            <LoaderCircleIcon
              v-if="downloadingPdf"
              class="size-4 animate-spin"
            />
            <MdiIcon
              v-else
              :path="$globals.icons.download"
              class="size-4"
            />
            {{ downloadingPdf ? $t("recipe.preparing-pdf") : $t("recipe.download-pdf") }}
          </Button>
          <Button
            v-if="canEdit"
            variant="outline"
            @click="handleEditCookbook"
          >
            <MdiIcon
              :path="$globals.icons.edit"
              class="size-4"
            />
            {{ $t("general.edit") }}
          </Button>
        </div>
      </header>

      <RecipeCardSection
        :recipes="recipes"
        :query="{ cookbook: slug }"
        @sort-recipes="assignSorted"
        @replace-recipes="replaceRecipes"
        @append-recipes="appendRecipes"
        @delete="removeRecipe"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { LoaderCircleIcon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { useLazyRecipes } from "~/composables/recipes";
import RecipeCardSection from "@/components/Domain/Recipe/RecipeCardSection.vue";
import { useCookbookStore } from "~/composables/store/use-cookbook-store";
import { useCookbook } from "~/composables/use-group-cookbooks";
import { useLoggedInState } from "~/composables/use-logged-in-state";
import type { CookBookOut } from "~/lib/api/types/cookbook";
import CookbookEditor from "~/components/Domain/Cookbook/CookbookEditor.vue";
import { useDownloader } from "~/composables/api/use-downloader";
import { loader } from "~/composables/use-toast";
import { useUserApi } from "~/composables/api";

const auth = useMealieAuth();
const { isOwnGroup } = useLoggedInState();

const route = useRoute();
const groupSlug = computed(() => route.params.groupSlug as string || auth.user.value?.groupSlug || "");

const { recipes, appendRecipes, assignSorted, removeRecipe, replaceRecipes } = useLazyRecipes(isOwnGroup.value ? null : groupSlug.value);
const slug = route.params.slug as string;
const { getOne } = useCookbook(isOwnGroup.value ? null : groupSlug.value);
const { actions } = useCookbookStore();
const router = useRouter();

const book = getOne(slug);

const isOwnHousehold = computed(() => {
  if (!(auth.user.value && book.value?.householdId)) {
    return false;
  }

  return auth.user.value.householdId === book.value.householdId;
});
const canEdit = computed(() => isOwnGroup.value && isOwnHousehold.value);

const api = useUserApi();
const download = useDownloader();
const i18n = useI18n();
const { $globals } = useNuxtApp();

const downloadingPdf = ref(false);

async function downloadPdf() {
  if (!book.value || downloadingPdf.value) {
    return;
  }
  downloadingPdf.value = true;
  // A big cookbook takes a while to render, and the browser shows nothing until the file arrives.
  loader.info(i18n.t("recipe.preparing-pdf"));
  try {
    await download(api.cookbooks.getPdfUrl(book.value.id), `${book.value.slug}.pdf`);
  }
  finally {
    downloadingPdf.value = false;
    loader.close();
  }
}

const dialogStates = reactive({
  edit: false,
});

const editTarget = ref<CookBookOut | null>(null);
function handleEditCookbook() {
  dialogStates.edit = true;
  editTarget.value = book.value;
}

async function editCookbook() {
  if (!editTarget.value) {
    return;
  }
  const response = await actions.updateOne(editTarget.value);

  if (response?.slug && book.value?.slug !== response?.slug) {
    // if name changed, redirect to new slug
    router.push(`/g/${route.params.groupSlug}/cookbooks/${response?.slug}`);
  }
  else {
    // otherwise reload the page, since the recipe criteria changed
    router.go(0);
  }
  dialogStates.edit = false;
  editTarget.value = null;
}

useSeoMeta({
  title: book?.value?.name || "Cookbook",
});
</script>
