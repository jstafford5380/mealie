<script setup lang="ts">
import type { RecipeOut } from "~/lib/api/types/recipe";
import { ImageIcon, ImagePlusIcon, LinkIcon, Trash2Icon } from "@lucide/vue";
import RecipeTimeInput from "~/components/Domain/Recipe/RecipeTimeInput.vue";
import { Button } from "~/components/ui/button";
import NumberInputField from "~/components/ui/field/NumberInputField.vue";
import SelectField from "~/components/ui/field/SelectField.vue";
import TextareaField from "~/components/ui/field/TextareaField.vue";
import TextField from "~/components/ui/field/TextField.vue";
import { Popover, PopoverContent, PopoverTrigger } from "~/components/ui/popover";
import { useStaticRoutes, useUserApi } from "~/composables/api";
import { usePageState, usePageUser } from "~/composables/recipe-page/shared-state";
import { useHouseholdStore } from "~/composables/store";
import { useUserStore } from "~/composables/store/use-user-store";
import { validators } from "~/composables/use-validators";

/** Editor section: photo, name, description, servings and yield, times, owner. */
const recipe = defineModel<RecipeOut>({ required: true });

const api = useUserApi();
const { user } = usePageUser();
const { imageKey } = usePageState(recipe.value.slug);
const { recipeImage } = useStaticRoutes();

// ---- photo
const imageUrl = computed(() => (recipe.value.image ? recipeImage(recipe.value.id, recipe.value.image, imageKey.value) : ""));
const imageFailed = ref(false);
watch(imageUrl, () => {
  imageFailed.value = false;
});
const busy = ref(false);
const fileInput = ref<HTMLInputElement>();

async function uploadImage(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";
  if (!file || !recipe.value.slug) {
    return;
  }
  busy.value = true;
  const { data, error } = await api.recipes.updateImage(recipe.value.slug, file);
  busy.value = false;
  if (error) {
    return;
  }
  if (data?.image) {
    recipe.value.image = data.image;
  }
  imageKey.value++;
}

const urlOpen = ref(false);
const imageFromUrl = ref("");
async function getImageFromUrl() {
  if (!imageFromUrl.value.trim()) {
    return;
  }
  busy.value = true;
  const { data, error } = await api.recipes.updateImagebyURL(recipe.value.slug, imageFromUrl.value.trim());
  busy.value = false;
  if (error) {
    return;
  }
  if (data?.image) {
    recipe.value.image = data.image;
  }
  imageKey.value++;
  imageFromUrl.value = "";
  urlOpen.value = false;
}

const deleteDialog = ref(false);
async function deleteImage() {
  busy.value = true;
  const { error } = await api.recipes.deleteImage(recipe.value.slug);
  busy.value = false;
  if (error) {
    return;
  }
  recipe.value.image = "";
  imageKey.value++;
}

// ---- owner
const { store: allUsers } = useUserStore();
const { store: households } = useHouseholdStore();
const canEditOwner = computed(() => user.id === recipe.value.userId || user.admin);
const ownerItems = computed(() => {
  const multipleHouseholds = households.value.length > 1;
  return allUsers.value.map((u) => {
    const household = multipleHouseholds ? households.value.find(h => h.id === u.householdId)?.name : "";
    return { value: u.id, title: household ? `${u.fullName} · ${household}` : (u.fullName || "") };
  });
});
</script>

<template>
  <div class="grid gap-6 font-sans xl:grid-cols-[220px_minmax(0,1fr)]">
    <!-- photo -->
    <div class="flex flex-col gap-2">
      <div class="text-sm font-semibold">
        {{ $t("recipe.photo") }}
      </div>
      <button
        type="button"
        class="group relative flex aspect-[2/1] w-full max-w-md xl:max-w-none xl:aspect-[4/3] items-center justify-center overflow-hidden rounded-card border border-dashed border-input bg-muted text-muted-foreground transition-colors hover:border-ring hover:text-foreground"
        :aria-label="imageUrl && !imageFailed ? $t('recipe.replace-photo') : $t('recipe.add-photo')"
        :disabled="busy"
        @click="fileInput?.click()"
      >
        <img
          v-if="imageUrl && !imageFailed"
          :key="imageKey"
          :src="imageUrl"
          alt=""
          class="absolute inset-0 size-full object-cover"
          @error="imageFailed = true"
        >
        <span
          v-if="imageUrl && !imageFailed"
          class="absolute inset-x-0 bottom-0 flex items-center justify-center gap-1.5 bg-black/55 py-2 text-sm font-semibold text-white opacity-0 transition-opacity group-hover:opacity-100 group-focus-visible:opacity-100"
        >
          <ImageIcon class="size-4" />
          {{ $t("recipe.replace-photo") }}
        </span>
        <span
          v-else
          class="flex flex-col items-center gap-1.5 text-sm font-semibold"
        >
          <ImagePlusIcon class="size-7" />
          {{ $t("recipe.add-photo") }}
        </span>
      </button>
      <input
        ref="fileInput"
        type="file"
        accept="image/*"
        class="display-none"
        @change="uploadImage"
      >
      <div class="flex flex-wrap gap-1">
        <Popover v-model:open="urlOpen">
          <PopoverTrigger as-child>
            <Button
              variant="ghost"
              size="sm"
              :disabled="busy"
            >
              <LinkIcon class="size-4" />
              {{ $t("recipe.photo-from-url") }}
            </Button>
          </PopoverTrigger>
          <PopoverContent
            align="start"
            class="w-[min(360px,calc(100vw-2rem))]"
          >
            <form
              class="flex flex-col gap-2"
              @submit.prevent="getImageFromUrl"
            >
              <TextField
                v-model="imageFromUrl"
                type="url"
                :label="$t('general.url')"
                placeholder="https://"
                autofocus
              />
              <Button
                type="submit"
                class="self-end"
                :disabled="busy || !imageFromUrl.trim()"
              >
                {{ $t("general.get") }}
              </Button>
            </form>
          </PopoverContent>
        </Popover>
        <Button
          v-if="recipe.image"
          variant="ghost"
          size="sm"
          class="text-destructive hover:text-destructive"
          :disabled="busy"
          @click="deleteDialog = true"
        >
          <Trash2Icon class="size-4" />
          {{ $t("general.remove") }}
        </Button>
      </div>
    </div>

    <!-- text fields -->
    <div class="flex min-w-0 flex-col gap-5">
      <TextField
        v-model="recipe.name"
        :label="$t('recipe.recipe-name')"
        :rules="[validators.required]"
        required
      />
      <TextareaField
        v-model="recipe.description"
        :label="$t('recipe.description')"
        :rows="3"
      />
      <div class="grid grid-cols-2 gap-4 sm:grid-cols-[1fr_1fr_2fr]">
        <NumberInputField
          class="min-w-0"
          :model-value="recipe.recipeServings"
          :label="$t('recipe.servings')"
          :min="0"
          :precision="null"
          control-variant="hidden"
          @update:model-value="recipe.recipeServings = $event ?? 0"
        />
        <NumberInputField
          class="min-w-0"
          :model-value="recipe.recipeYieldQuantity"
          :label="$t('recipe.yield')"
          :min="0"
          :precision="null"
          control-variant="hidden"
          @update:model-value="recipe.recipeYieldQuantity = $event ?? 0"
        />
        <div class="col-span-2 min-w-0 sm:col-span-1">
          <TextField
            v-model="recipe.recipeYield"
            :label="$t('recipe.yield-text')"
          />
        </div>
      </div>
      <RecipeTimeInput
        v-model:seconds="recipe.totalTimeSeconds"
        v-model:text="recipe.totalTime"
        :label="$t('recipe.total-time')"
      />
      <RecipeTimeInput
        v-model:seconds="recipe.prepTimeSeconds"
        v-model:text="recipe.prepTime"
        :label="$t('recipe.prep-time')"
      />
      <RecipeTimeInput
        v-model:seconds="recipe.performTimeSeconds"
        v-model:text="recipe.performTime"
        :label="$t('recipe.perform-time')"
      />
      <div class="max-w-sm">
        <SelectField
          v-model="recipe.userId"
          :items="ownerItems"
          :label="$t('general.owner')"
          :disabled="!canEditOwner"
        />
      </div>
    </div>

    <BaseDialog
      v-model="deleteDialog"
      :title="$t('recipe.remove-photo')"
      color="error"
      :icon="$globals.icons.alertCircle"
      can-delete
      @delete="deleteImage"
    >
      <p class="m-0 px-6 pb-2 text-[15px]">
        {{ $t("recipe.delete-image-confirmation") }}
      </p>
    </BaseDialog>
  </div>
</template>
