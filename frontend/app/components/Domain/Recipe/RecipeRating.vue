<template>
  <div
    class="inline-flex items-center"
    @click.prevent
  >
    <span
      v-if="isReadonly"
      role="img"
      :aria-label="$t('recipe.rating-out-of-five', { rating: Math.round(displayRating * 10) / 10 })"
      class="inline-flex gap-0.5"
      :class="showGroupAverage || !displayRating ? 'text-muted-foreground/60' : 'text-brand'"
    >
      <svg
        v-for="n in 5"
        :key="n"
        viewBox="0 0 24 24"
        aria-hidden="true"
        :class="small ? 'size-4' : 'size-5'"
      >
        <path
          :d="STAR"
          :fill="displayRating >= n ? 'currentColor' : displayRating >= n - 0.75 ? 'currentColor' : 'none'"
          :fill-opacity="displayRating >= n ? 1 : displayRating >= n - 0.75 ? 0.5 : 1"
          stroke="currentColor"
          stroke-width="1.6"
          stroke-linejoin="round"
        />
      </svg>
    </span>
    <div
      v-else
      role="radiogroup"
      :aria-label="$t('general.rating')"
      class="inline-flex"
      @mouseleave="hover = 0"
    >
      <button
        v-for="n in 5"
        :key="n"
        type="button"
        role="radio"
        :aria-checked="displayRating === n"
        :aria-label="$t('recipe.rating-out-of-five', { rating: n })"
        class="inline-flex items-center justify-center rounded-full text-brand transition-transform hover:scale-110 focus-visible:outline-2 focus-visible:outline-ring"
        :class="small ? 'size-7' : 'size-9'"
        @mouseenter="canHover && (hover = n)"
        @click="updateRating(n)"
      >
        <svg
          viewBox="0 0 24 24"
          aria-hidden="true"
          :class="small ? 'size-4' : 'size-[22px]'"
        >
          <path
            :d="STAR"
            :fill="(hover || displayRating) >= n ? 'currentColor' : 'none'"
            stroke="currentColor"
            stroke-width="1.6"
            stroke-linejoin="round"
          />
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useMediaQuery } from "@vueuse/core";
import { useLoggedInState } from "~/composables/use-logged-in-state";
import { useUserSelfRatings } from "~/composables/use-users";

interface Props {
  readonly?: boolean;
  recipeId?: string;
  slug?: string;
  small?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  readonly: false,
  recipeId: "",
  slug: "",
  small: false,
});

const STAR = "M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01z";
const hover = ref(0);

const groupRating = defineModel<number | null>({ default: 0 });

const { isOwnGroup } = useLoggedInState();
const isReadonly = computed(() => props.readonly || !isOwnGroup.value);
const { userRatings, setRating } = useUserSelfRatings();

// on touch devices a tap fires mouseenter without a matching mouseleave, which leaves v-rating
// rendering the stuck hover value instead of the model value
const canHover = useMediaQuery("(hover: hover) and (pointer: fine)");

const userRating = computed<number | null>(() => {
  return userRatings.value.find(r => r.recipeId === props.recipeId)?.rating ?? null;
});

const localUserRating = ref(userRating.value);

// while a write is in flight a refetch may still report the pre-click value, so ignore it
const pendingWrites = ref(0);
watch(userRating, (value) => {
  if (!pendingWrites.value) {
    localUserRating.value = value;
  }
});

// only fall back to the group average when we can't offer the user their own rating,
// and only when there's actually a group average to show. An unset rating may be null or 0
const showGroupAverage = computed(() => {
  return isReadonly.value && !localUserRating.value && !!groupRating.value;
});

const displayRating = computed(() => {
  return showGroupAverage.value ? (groupRating.value ?? 0) : (localUserRating.value || 0);
});

async function updateRating(val?: number) {
  if (isReadonly.value) {
    return;
  }

  // user ratings are always whole stars
  let rating = Math.round(val ?? 0);
  if (rating === localUserRating.value) {
    rating = 0;
  }

  localUserRating.value = rating;

  pendingWrites.value++;
  try {
    await setRating(props.slug, rating, null);
  }
  finally {
    pendingWrites.value--;
  }
}
</script>
