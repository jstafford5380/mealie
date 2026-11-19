<template>
  <li class="relative flex gap-3 pb-6 font-sans last:pb-0">
    <!-- event-type dot on the rail -->
    <span class="relative z-[1] mt-1 inline-flex size-9 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground ring-4 ring-background">
      <MdiIcon
        :path="icon"
        class="size-[18px]"
      />
    </span>
    <article class="min-w-0 flex-1 overflow-hidden rounded-card border bg-card">
      <header class="flex items-center gap-3 px-4 pt-3">
        <UserAvatar
          :user-id="event.userId"
          size="32"
        />
        <div class="min-w-0 flex-1">
          <p class="m-0 font-semibold break-words">
            {{ event.subject }}
          </p>
          <p
            v-if="event.timestamp"
            class="m-0 text-sm text-muted-foreground"
          >
            <time :datetime="event.timestamp">{{ $d(new Date(event.timestamp)) }}</time>
          </p>
        </div>
        <RecipeTimelineContextMenu
          v-if="currentUser && currentUser.id == event.userId && event.eventType != 'system'"
          :event="event"
          :image-url="eventImageUrl"
          :menu-icon="$globals.icons.dotsVertical"
          :use-items="{
            edit: true,
            delete: true,
          }"
          @update="$emit('update', $event)"
          @delete="$emit('delete')"
        />
      </header>
      <div class="flex flex-col gap-3 px-4 pt-2 pb-4">
        <div
          v-if="event.eventMessage"
          class="text-[15px] break-words"
        >
          <SafeMarkdown :source="event.eventMessage" />
        </div>
        <img
          v-if="eventImageUrl && !hideImage"
          :src="eventImageUrl"
          alt=""
          class="max-h-80 w-auto max-w-full self-start rounded-control border object-contain"
          @error="hideImage = true"
        >
        <div
          v-if="showRecipeCards && recipe"
          class="overflow-hidden rounded-control border"
          @click="$emit('selected')"
        >
          <RecipeCardLineItem
            :recipe="recipe"
            :disable-link="!!$attrs.selected"
          />
        </div>
      </div>
    </article>
  </li>
</template>

<script setup lang="ts">
import RecipeCardLineItem from "./RecipeCardLineItem.vue";
import { MdiIcon } from "~/components/ui/mdi-icon";
import RecipeTimelineContextMenu from "./RecipeTimelineContextMenu.vue";
import type { TimelineEventEdit } from "./RecipeTimelineContextMenu.vue";
import { useStaticRoutes } from "~/composables/api";
import { useTimelineEventTypes } from "~/composables/recipes/use-recipe-timeline-events";
import type { RecipeSummary, RecipeTimelineEventOut } from "~/lib/api/types/recipe";
import UserAvatar from "~/components/Domain/User/UserAvatar.vue";
import SafeMarkdown from "~/components/global/SafeMarkdown.vue";

interface Props {
  event: RecipeTimelineEventOut;
  recipe?: RecipeSummary;
  showRecipeCards?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  recipe: undefined,
  showRecipeCards: false,
});

defineEmits<{
  selected: [];
  update: [edit: TimelineEventEdit];
  delete: [];
}>();

const { $globals } = useNuxtApp();
const { recipeTimelineEventSmallImage } = useStaticRoutes();
const { eventTypeOptions } = useTimelineEventTypes();

const { user: currentUser } = useMealieAuth();

const icon = computed(() => {
  const option = eventTypeOptions.value.find(option => option.value === props.event.eventType);
  return option ? option.icon : $globals.icons.informationVariant;
});

const hideImage = ref(false);
const imageKey = ref(1);
watch(() => props.event, () => {
  hideImage.value = false;
  imageKey.value++;
});

const eventImageUrl = computed<string>(() => {
  if (props.event.image !== "has image") {
    return "";
  }

  return recipeTimelineEventSmallImage(props.event.recipeId, props.event.id, imageKey.value);
});
</script>
