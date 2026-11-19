<template>
  <button
    v-if="isFavorite || showAlways"
    type="button"
    :aria-pressed="isFavorite"
    :aria-label="isFavorite ? $t('recipe.remove-from-favorites') : $t('recipe.add-to-favorites')"
    :title="isFavorite ? $t('recipe.remove-from-favorites') : $t('recipe.add-to-favorites')"
    v-bind="$attrs"
    :class="buttonStyle
      ? 'inline-flex size-11 items-center justify-center rounded-full bg-card text-foreground shadow-sm ring-1 ring-border transition-colors hover:bg-highlight'
      : 'inline-flex size-9 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-highlight hover:text-destructive'"
    @click.prevent.stop="toggleFavorite"
  >
    <MdiIcon
      :path="isFavorite ? $globals.icons.heart : $globals.icons.heartOutline"
      :class="[buttonStyle ? 'size-6' : 'size-5', isFavorite && 'text-destructive']"
    />
  </button>
</template>

<script setup lang="ts">
import { MdiIcon } from "~/components/ui/mdi-icon";
import { useUserSelfRatings } from "~/composables/use-users";
import { useUserApi } from "~/composables/api";

interface Props {
  recipeId?: string;
  showAlways?: boolean;
  buttonStyle?: boolean;
}
defineOptions({ inheritAttrs: false });

const props = withDefaults(defineProps<Props>(), {
  recipeId: "",
  showAlways: false,
  buttonStyle: false,
});

const { userRatings, refreshUserRatings } = useUserSelfRatings();

const isFavorite = computed(() => {
  const rating = userRatings.value.find(r => r.recipeId === props.recipeId);
  return rating?.isFavorite || false;
});

async function toggleFavorite() {
  const api = useUserApi();
  const auth = useMealieAuth();

  if (!auth.user.value) return;
  if (!isFavorite.value) {
    await api.users.addFavorite(auth.user.value?.id, props.recipeId);
  }
  else {
    await api.users.removeFavorite(auth.user.value?.id, props.recipeId);
  }
  await refreshUserRatings();
}
</script>
