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
 * Grid tile for a recipe: photo, name, time, rating and up to two tags.
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
  <article class="group/tile flex min-w-0 flex-col gap-2.5 font-sans">
    <div class="relative">
      <component
        :is="to ? NuxtLink : 'div'"
        :to="to"
        :aria-label="name"
        tabindex="-1"
        class="relative block aspect-[4/3] overflow-hidden rounded-card bg-muted"
      >
        <img
          v-if="imageUrl"
          :src="imageUrl"
          alt=""
          loading="lazy"
          class="size-full object-cover transition-transform duration-300 group-hover/tile:scale-[1.03] motion-reduce:transition-none"
          @error="imageFailed = true"
        >
        <span
          v-else
          class="flex size-full items-center justify-center text-muted-foreground/50"
        >
          <MdiIcon
            :path="$globals.icons.primary"
            class="size-14"
          />
        </span>
        <span
          v-if="description"
          class="absolute inset-0 flex items-end bg-gradient-to-t from-black/75 via-black/30 to-transparent p-3 text-[13px] leading-snug text-white opacity-0 transition-opacity duration-200 group-hover/tile:opacity-100 max-md:hidden"
          aria-hidden="true"
        >
          <span class="line-clamp-4 [&_p]:m-0">
            <SafeMarkdown :source="description" />
          </span>
        </span>
      </component>
      <div
        v-if="isOwnGroup && actionable"
        class="absolute end-2 top-2 rounded-full bg-card/90 shadow-sm backdrop-blur"
      >
        <RecipeFavoriteBadge
          :recipe-id="recipeId"
          show-always
        />
      </div>
    </div>

    <div class="flex items-start gap-1">
      <component
        :is="to ? NuxtLink : 'span'"
        :to="to"
        class="line-clamp-2 min-w-0 flex-1 font-serif text-[17px] leading-snug text-foreground no-underline hover:text-primary focus-visible:rounded-item focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
      >
        {{ name }}
      </component>
      <RecipeContextMenu
        v-if="isOwnGroup && actionable"
        class="-me-1.5 -mt-1.5 shrink-0"
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
  </article>
</template>
