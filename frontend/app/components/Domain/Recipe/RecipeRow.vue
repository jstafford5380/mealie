<script setup lang="ts">
import type { UrlPrefixParam } from "./RecipeChips.vue";
import type { TagOut } from "~/lib/api/types/recipe";
import { ClockIcon } from "@lucide/vue";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { useStaticRoutes } from "~/composables/api";
import { useLoggedInState } from "~/composables/use-logged-in-state";
import RecipeCardRating from "./RecipeCardRating.vue";
import RecipeContextMenu from "./RecipeContextMenu/RecipeContextMenu.vue";
import RecipeFavoriteBadge from "./RecipeFavoriteBadge.vue";

/**
 * List row for a recipe (compact view and phones): thumbnail, name, description, time, rating, tags.
 * The photo and name are links; favorite, tags and the action menu are separate controls.
 */
const props = withDefaults(defineProps<{
  name: string;
  slug: string;
  recipeId: string;
  description?: string | null;
  rating?: number | null;
  image?: unknown;
  tags?: TagOut[];
  totalTime?: string | null;
}>(), {
  description: null,
  rating: 0,
  image: null,
  tags: () => [],
  totalTime: null,
});

const emit = defineEmits<{
  delete: [slug: string];
  itemSelected: [item: TagOut, urlPrefix: UrlPrefixParam];
}>();

const NuxtLink = resolveComponent("NuxtLink");
const auth = useMealieAuth();
const route = useRoute();
const { isOwnGroup } = useLoggedInState();
const { recipeSmallImage } = useStaticRoutes();

const groupSlug = computed(() => (route.params.groupSlug as string) || auth.user.value?.groupSlug || "");
const actionable = computed(() => !!(props.recipeId && props.slug));
const to = computed(() => (actionable.value ? `/g/${groupSlug.value}/r/${props.slug}` : undefined));

const imageFailed = ref(false);
watch(() => [props.recipeId, props.image], () => {
  imageFailed.value = false;
});
const imageUrl = computed(() => (props.image && !imageFailed.value ? recipeSmallImage(props.recipeId, props.image) : null));
const visibleTags = computed(() => props.tags.slice(0, 2));
</script>

<template>
  <article class="group/tile flex min-w-0 items-center gap-3 rounded-card border bg-card p-2.5 font-sans">
    <div class="relative shrink-0">
      <component
        :is="to ? NuxtLink : 'div'"
        :to="to"
        :aria-label="name"
        tabindex="-1"
        class="relative block size-[84px] overflow-hidden rounded-control bg-muted sm:size-24"
      >
        <img
          v-if="imageUrl"
          :src="imageUrl"
          alt=""
          loading="lazy"
          class="size-full object-cover"
          @error="imageFailed = true"
        >
        <span
          v-else
          class="flex size-full items-center justify-center text-muted-foreground/50"
        >
          <MdiIcon
            :path="$globals.icons.primary"
            class="size-9"
          />
        </span>
      </component>
    </div>

    <div class="flex min-w-0 flex-1 flex-col gap-1">
      <div class="flex items-start gap-1">
        <component
          :is="to ? NuxtLink : 'span'"
          :to="to"
          class="line-clamp-2 min-w-0 flex-1 font-serif text-[16px] leading-snug text-foreground no-underline hover:text-primary focus-visible:rounded-item focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
        >
          {{ name }}
        </component>
        <RecipeFavoriteBadge
          v-if="isOwnGroup && actionable"
          class="-mt-1.5 shrink-0"
          :recipe-id="recipeId"
          show-always
        />
        <RecipeContextMenu
          v-if="isOwnGroup && actionable"
          class="-me-1 -mt-1.5 shrink-0"
          :slug="slug"
          :name="name"
          :recipe-id="recipeId"
          :use-items="{
            delete: false,
            edit: false,
            download: true,
            downloadPdf: true,
            mealplanner: true,
            shoppingList: true,
            print: false,
            printPreferences: false,
            share: true,
          }"
          @deleted="emit('delete', slug)"
        />
      </div>

      <div
        v-if="description"
        class="line-clamp-2 text-[13px] leading-snug text-muted-foreground [&_p]:m-0"
      >
        <SafeMarkdown :source="description" />
      </div>
      <div class="flex min-w-0 flex-wrap items-center gap-x-3 gap-y-1.5 text-[13px] text-muted-foreground">
        <span
          v-if="totalTime"
          class="inline-flex items-center gap-1"
        >
          <ClockIcon class="size-3.5" />
          {{ totalTime }}
        </span>
        <RecipeCardRating
          :model-value="rating ?? 0"
          :recipe-id="recipeId"
        />
        <button
          v-for="tag in visibleTags"
          :key="tag.id"
          type="button"
          class="max-w-36 truncate rounded-full bg-subtle px-2 py-0.5 text-xs font-medium text-subtle-foreground transition-colors hover:bg-highlight hover:text-highlight-foreground"
          @click.prevent="emit('itemSelected', tag, 'tags')"
        >
          {{ tag.name }}
        </button>
      </div>
    </div>
  </article>
</template>
