<script setup lang="ts">
import type { HouseholdSummary } from "~/lib/api/types/household";
import type { RecipeOut } from "~/lib/api/types/recipe";
import type { UserSummary } from "~/lib/api/types/user";
import { ExternalLinkIcon, PlayIcon } from "@lucide/vue";
import { useMediaQuery } from "@vueuse/core";
import RecipeContextMenu from "~/components/Domain/Recipe/RecipeContextMenu/RecipeContextMenu.vue";
import RecipeFavoriteBadge from "~/components/Domain/Recipe/RecipeFavoriteBadge.vue";
import RecipeImageLightbox from "~/components/Domain/Recipe/RecipeImageLightbox.vue";
import RecipeLastMade from "~/components/Domain/Recipe/RecipeLastMade.vue";
import RecipeRating from "~/components/Domain/Recipe/RecipeRating.vue";
import RecipeTimelineBadge from "~/components/Domain/Recipe/RecipeTimelineBadge.vue";
import { Avatar, AvatarFallback, AvatarImage } from "~/components/ui/avatar";
import { Button } from "~/components/ui/button";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { useStaticRoutes, useUserApi } from "~/composables/api";
import { useRecipePermissions, useRecipeTime } from "~/composables/recipes";
import { useScaledAmount } from "~/composables/recipes/use-scaled-amount";
import { PageMode, usePageState, usePageUser } from "~/composables/recipe-page/shared-state";
import { useRecipeLightboxItems } from "~/composables/recipe-page/use-recipe-lightbox-items";
import { useUserStore } from "~/composables/store/use-user-store";
import { useLoggedInState } from "~/composables/use-logged-in-state";
import { isHttpUrl } from "~/lib/validators/url";

/** Reader header: title, description, key facts, the cook's own controls, and the photo. */
const props = withDefaults(defineProps<{
  recipe: RecipeOut;
  recipeScale?: number;
  /** Photo above the text instead of beside it (recipe setting, and always on phones). */
  landscape?: boolean;
}>(), {
  recipeScale: 1,
  landscape: false,
});

const i18n = useI18n();
const { isOwnGroup, loggedIn } = useLoggedInState();
const { imageKey, setMode, toggleCookMode } = usePageState(props.recipe.slug);
const { user } = usePageUser();
const { recipeImage, recipeSmallImage } = useStaticRoutes();
const { recipeTimeDisplay } = useRecipeTime();

// Edit access depends on the recipe's household preferences.
const recipeHousehold = ref<HouseholdSummary>();
if (user) {
  useUserApi().households.getOne(props.recipe.householdId).then(({ data }) => {
    recipeHousehold.value = data || undefined;
  });
}
const { canEditRecipe } = useRecipePermissions(props.recipe, recipeHousehold, user);

// Group members aren't visible outside the group, so they aren't fetched there.
const users = isOwnGroup.value ? useUserStore().store : ref<UserSummary[]>([]);
const owner = computed(() => users.value.find(u => u.id === props.recipe.userId));
const ownerInitials = computed(() => (owner.value?.fullName || "?").split(/\s+/).map(p => p[0]).join("").slice(0, 2).toUpperCase());

const facts = computed(() => {
  const list: { key: string; label: string; value: string }[] = [];
  const total = recipeTimeDisplay(props.recipe.totalTimeSeconds, props.recipe.totalTime);
  const prep = recipeTimeDisplay(props.recipe.prepTimeSeconds, props.recipe.prepTime);
  const cook = recipeTimeDisplay(props.recipe.performTimeSeconds, props.recipe.performTime);
  if (total) {
    list.push({ key: "total", label: i18n.t("recipe.total-time"), value: total });
  }
  if (prep) {
    list.push({ key: "prep", label: i18n.t("recipe.prep-time"), value: prep });
  }
  if (cook) {
    list.push({ key: "cook", label: i18n.t("recipe.perform-time"), value: cook });
  }
  const { scaledAmountDisplay } = useScaledAmount(props.recipe.recipeYieldQuantity, props.recipeScale);
  const yieldText = [scaledAmountDisplay, props.recipe.recipeYield].filter(Boolean).join(" ");
  if (yieldText) {
    list.push({ key: "yield", label: i18n.t("recipe.yield"), value: yieldText });
  }
  return list;
});

// The original URL, shown by its site name.
const sourceHost = computed(() => {
  const url = props.recipe.orgURL;
  if (!url || !isHttpUrl(url)) {
    return "";
  }
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  }
  catch {
    return "";
  }
});

// Photo: small image on phones, full size otherwise; hidden if it fails to load.
const imageFailed = ref(false);
const fullImageUrl = computed(() => recipeImage(props.recipe.id, props.recipe.image, imageKey.value));
const isNarrow = useMediaQuery("(max-width: 959.98px)");
const displayImageUrl = computed(() => (isNarrow.value
  ? recipeSmallImage(props.recipe.id, props.recipe.image, imageKey.value)
  : fullImageUrl.value));
watch(displayImageUrl, () => {
  imageFailed.value = false;
});
const showImage = computed(() => !!props.recipe.image && !imageFailed.value);

const lightboxOpen = ref(false);
const lightboxIndex = ref(0);
const { buildItems } = useRecipeLightboxItems();
const lightboxItems = computed(() => buildItems(props.recipe.id, {
  heroUrl: fullImageUrl.value,
  heroAlt: props.recipe.name,
  assets: props.recipe.assets,
}));
function printRecipe() {
  window.print();
}

function openLightbox() {
  lightboxIndex.value = 0;
  lightboxOpen.value = true;
}
</script>

<template>
  <header
    class="grid gap-6 font-sans print:hidden"
    :class="landscape || !showImage ? 'grid-cols-1' : 'lg:grid-cols-[minmax(0,1fr)_minmax(0,0.95fr)] lg:items-stretch lg:gap-10'"
  >
    <button
      v-if="showImage"
      type="button"
      class="group relative block w-full cursor-zoom-in overflow-hidden rounded-panel bg-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
      :class="landscape ? 'h-[220px] sm:h-[400px]' : 'aspect-[4/3] lg:order-2 lg:aspect-auto lg:min-h-[380px]'"
      :aria-label="$t('recipe.view-image')"
      @click="openLightbox"
    >
      <img
        :key="imageKey"
        :src="displayImageUrl"
        :alt="recipe.name"
        class="absolute inset-0 size-full object-cover"
        @error="imageFailed = true"
      >
    </button>

    <div class="flex min-w-0 flex-col gap-4 lg:order-1">
      <h1 class="m-0 font-serif text-[32px] font-normal leading-[1.1] tracking-[-0.01em] text-foreground sm:text-[42px]">
        {{ recipe.name }}
      </h1>
      <div
        v-if="recipe.description"
        class="max-w-[62ch] text-[16.5px] leading-relaxed text-muted-foreground [&_p]:m-0 [&_p+p]:mt-2"
      >
        <SafeMarkdown :source="recipe.description" />
      </div>

      <dl
        v-if="facts.length"
        class="m-0 flex flex-wrap gap-x-8 gap-y-3"
      >
        <div
          v-for="fact in facts"
          :key="fact.key"
          class="flex flex-col gap-0.5"
        >
          <dt class="text-[13px] text-muted-foreground">
            {{ fact.label }}
          </dt>
          <dd class="m-0 text-[17px] font-semibold">
            {{ fact.value }}
          </dd>
        </div>
      </dl>

      <div class="flex flex-wrap items-center gap-x-4 gap-y-2">
        <RecipeRating
          :key="recipe.slug"
          :model-value="recipe.rating"
          :recipe-id="recipe.id"
          :slug="recipe.slug"
        />
        <span
          v-if="isOwnGroup && owner"
          class="inline-flex items-center gap-2 text-sm text-muted-foreground"
        >
          <Avatar class="size-7">
            <AvatarImage
              :src="`/api/media/users/${owner.id}/profile.webp`"
              alt=""
            />
            <AvatarFallback class="bg-highlight text-[11px] font-bold text-highlight-foreground">{{ ownerInitials }}</AvatarFallback>
          </Avatar>
          {{ owner.fullName }}
        </span>
        <a
          v-if="sourceHost"
          :href="recipe.orgURL!"
          target="_blank"
          rel="noopener noreferrer"
          class="inline-flex items-center gap-1 text-sm font-medium text-primary underline-offset-2 hover:underline"
        >
          {{ sourceHost }}
          <ExternalLinkIcon class="size-3.5" />
          <span class="sr-only">({{ $t('recipe.original-url') }}, {{ $t('general.opens-in-new-tab') }})</span>
        </a>
        <RecipeLastMade
          v-if="isOwnGroup"
          :recipe="recipe"
        />
      </div>

      <div class="mt-auto flex flex-wrap items-center gap-2 pt-2">
        <Button
          size="lg"
          @click="toggleCookMode()"
        >
          <PlayIcon class="size-[18px] fill-current" />
          {{ $t("recipe.cook-mode") }}
        </Button>
        <RecipeFavoriteBadge
          v-if="isOwnGroup"
          button-style
          :recipe-id="recipe.id"
          show-always
        />
        <RecipeTimelineBadge
          v-if="isOwnGroup"
          button-style
          :slug="recipe.slug"
          :recipe-name="recipe.name"
        />
        <button
          v-if="isOwnGroup && canEditRecipe"
          type="button"
          class="inline-flex size-11 items-center justify-center rounded-full bg-card text-foreground shadow-sm ring-1 ring-border transition-colors hover:bg-highlight"
          :aria-label="$t('general.edit')"
          :title="$t('general.edit')"
          @click="setMode(PageMode.EDIT)"
        >
          <MdiIcon
            :path="$globals.icons.edit"
            class="size-[22px]"
          />
        </button>
        <RecipeContextMenu
          show-print
          :menu-top="false"
          :name="recipe.name"
          :slug="recipe.slug"
          :menu-icon="$globals.icons.dotsVertical"
          fab
          :card-menu="false"
          :recipe="recipe"
          :recipe-id="recipe.id"
          :recipe-scale="recipeScale"
          :use-items="{
            edit: false,
            download: loggedIn,
            downloadPdf: loggedIn,
            duplicate: loggedIn,
            mealplanner: loggedIn,
            shoppingList: loggedIn,
            print: true,
            printPreferences: true,
            share: loggedIn,
            recipeActions: true,
            delete: loggedIn,
          }"
          @print="printRecipe"
        />
      </div>
    </div>

    <RecipeImageLightbox
      v-if="lightboxOpen"
      v-model="lightboxOpen"
      v-model:index="lightboxIndex"
      :items="lightboxItems"
    />
  </header>
</template>
