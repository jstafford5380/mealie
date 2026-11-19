<template>
  <span
    class="inline-flex items-center gap-px"
    :class="showGroupAverage || !ratingValue ? 'text-muted-foreground/60' : 'text-brand'"
    role="img"
    :aria-label="$t('recipe.rating-out-of-five', { rating: Math.round(ratingValue * 10) / 10 })"
  >
    <svg
      v-for="(star, index) in ratingDisplay"
      :key="index"
      viewBox="0 0 24 24"
      aria-hidden="true"
      class="size-[15px]"
    >
      <defs v-if="star === 'half'">
        <linearGradient :id="`half-${uid}`">
          <stop
            offset="50%"
            stop-color="currentColor"
          />
          <stop
            offset="50%"
            stop-color="transparent"
          />
        </linearGradient>
      </defs>
      <path
        d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01z"
        :fill="star === 'full' ? 'currentColor' : star === 'half' ? `url(#half-${uid})` : 'none'"
        stroke="currentColor"
        stroke-width="1.6"
        stroke-linejoin="round"
      />
    </svg>
  </span>
</template>

<script setup lang="ts">
import { useUserSelfRatings } from "~/composables/use-users";

type Star = "full" | "half" | "empty";

const props = defineProps({
  modelValue: {
    type: Number,
    default: 0,
  },
  recipeId: {
    type: String,
    default: "",
  },
});

const { userRatings } = useUserSelfRatings();
const uid = useId();

const userRating = computed(() => {
  return userRatings.value.find(r => r.recipeId === props.recipeId)?.rating ?? null;
});

// this display is always readonly, so we show the user's own rating if they have one,
// and otherwise fall back to the group average (in grey), if there is one.
// An unset rating may be null or 0
const showGroupAverage = computed(() => !userRating.value && !!props.modelValue);
const ratingValue = computed(() => (showGroupAverage.value ? props.modelValue : userRating.value) || 0);
const ratingDisplay = computed<Star[]>(
  () => {
    const stars: Star[] = [];

    for (let i = 0; i < 5; i++) {
      const diff = ratingValue.value - i;
      if (diff >= 1) {
        stars.push("full");
      }
      else if (diff >= 0.25) { // round to half star if rating is at least 0.25 but not quite a full star
        stars.push("half");
      }
      else {
        stars.push("empty");
      }
    }

    return stars;
  },
);
</script>
