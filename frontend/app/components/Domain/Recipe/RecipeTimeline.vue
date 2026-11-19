<template>
  <div class="h-full font-sans">
    <div class="mb-4 flex justify-end">
      <DropdownMenu :modal="false">
        <DropdownMenuTrigger as-child>
          <Button variant="outline">
            <MdiIcon
              :path="$globals.icons.filter"
              class="size-4"
            />
            {{ $t("general.filter") }}
            <span
              v-if="filterBadgeCount > 0"
              class="rounded-full bg-primary px-1.5 text-xs font-bold text-primary-foreground tabular-nums"
            >{{ filterBadgeCount }}</span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent
          align="end"
          class="min-w-56"
        >
          <DropdownMenuItem @select.prevent="reverseSort">
            <MdiIcon
              :path="preferences.orderDirection === 'asc' ? $globals.icons.sortCalendarDescending : $globals.icons.sortCalendarAscending"
              class="size-4"
            />
            {{ preferences.orderDirection === 'asc' ? $t('general.sort-descending') : $t('general.sort-ascending') }}
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuCheckboxItem
            v-for="option, idx in eventTypeFilterState"
            :key="idx"
            :model-value="option.checked"
            @select.prevent
            @update:model-value="toggleEventTypeOption(option.value)"
          >
            <MdiIcon
              :path="option.icon"
              class="size-4"
            />
            {{ option.label }}
          </DropdownMenuCheckboxItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
    <div
      v-if="timelineEvents.length"
      id="timeline-container"
      :style="maxHeight ? `max-height: ${maxHeight}; overflow-y: auto;` : ''"
    >
      <!-- the rail runs behind the dots -->
      <ol class="relative m-0 list-none p-0 before:absolute before:inset-y-2 before:start-[17px] before:w-0.5 before:bg-border">
        <RecipeTimelineItem
          v-for="(event, index) in timelineEvents"
          :key="event.id"
          :event="event"
          :recipe="recipes.get(event.recipeId)"
          :show-recipe-cards="showRecipeCards"
          @update="updateTimelineEvent(index, $event)"
          @delete="deleteTimelineEvent(index)"
        />
      </ol>
    </div>
    <p
      v-else-if="!loading"
      class="m-0 rounded-card border border-dashed px-4 py-10 text-center text-sm text-muted-foreground"
    >
      {{ $t("recipe.timeline-no-events-found-try-adjusting-filters") }}
    </p>
    <div
      v-if="loading"
      class="my-4 text-center"
    >
      <AppLoader
        :loading="loading"
        :waiting-text="$t('general.loading-events')"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Button } from "~/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "~/components/ui/dropdown-menu";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { useThrottleFn, whenever } from "@vueuse/core";
import RecipeTimelineItem from "./RecipeTimelineItem.vue";
import type { TimelineEventEdit } from "./RecipeTimelineContextMenu.vue";
import { useTimelinePreferences } from "~/composables/use-users/preferences";
import { useTimelineEventTypes } from "~/composables/recipes/use-recipe-timeline-events";
import { alert } from "~/composables/use-toast";
import { useUserApi } from "~/composables/api";
import type { RecipeSummary, RecipeTimelineEventOut, TimelineEventType } from "~/lib/api/types/recipe";

interface Props {
  modelValue?: boolean;
  queryFilter: string;
  maxHeight?: number | string;
  showRecipeCards?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: false,
  maxHeight: undefined,
  showRecipeCards: false,
});

const api = useUserApi();
const i18n = useI18n();
const preferences = useTimelinePreferences();
const { eventTypeOptions } = useTimelineEventTypes();
const loading = ref(true);
const ready = ref(false);

const page = ref(1);
const perPage = 32;
const hasMore = ref(true);

const timelineEvents = ref([] as RecipeTimelineEventOut[]);
const recipes = new Map<string, RecipeSummary>();
const filterBadgeCount = computed(() => eventTypeOptions.value.length - preferences.value.types.length);
const eventTypeFilterState = computed(() => {
  return eventTypeOptions.value.map((option) => {
    return {
      ...option,
      checked: preferences.value.types.includes(option.value),
    };
  });
});
const screenBuffer = 4;

whenever(
  () => props.modelValue,
  () => {
    initializeTimelineEvents();
  },
);

// Preferences
function reverseSort() {
  if (loading.value) {
    return;
  }

  preferences.value.orderDirection = preferences.value.orderDirection === "asc" ? "desc" : "asc";
  initializeTimelineEvents();
}

function toggleEventTypeOption(option: TimelineEventType) {
  if (loading.value) {
    return;
  }

  const index = preferences.value.types.indexOf(option);
  if (index === -1) {
    preferences.value.types.push(option);
  }
  else {
    preferences.value.types.splice(index, 1);
  }

  initializeTimelineEvents();
}

// Timeline Actions
async function updateTimelineEvent(index: number, edit: TimelineEventEdit) {
  const eventId = timelineEvents.value[index].id;
  const { response } = await api.recipes.updateTimelineEvent(eventId, edit.event);
  if (response?.status !== 200) {
    alert.error(i18n.t("events.something-went-wrong") as string);
    return;
  }

  const updatedEvent = response.data;
  if (edit.image) {
    try {
      const { data } = await api.recipes.updateTimelineEventImage(eventId, edit.image.file, edit.image.fileName);
      if (!data) {
        throw new Error("Failed to upload image");
      }
      updatedEvent.image = data.image;
    }
    catch (error) {
      console.error("Failed to upload image for timeline event:", error);
      timelineEvents.value[index] = updatedEvent;
      alert.error(i18n.t("events.something-went-wrong") as string);
      return;
    }
  }

  // Update the local event data to reflect the changes in the UI
  timelineEvents.value[index] = updatedEvent;

  alert.success(i18n.t("events.event-updated") as string);
}

async function deleteTimelineEvent(index: number) {
  const { response } = await api.recipes.deleteTimelineEvent(timelineEvents.value[index].id);
  if (response?.status !== 200) {
    alert.error(i18n.t("events.something-went-wrong") as string);
    return;
  }

  timelineEvents.value.splice(index, 1);
  alert.success(i18n.t("events.event-deleted") as string);
}

async function getRecipes(recipeIds: string[]): Promise<RecipeSummary[]> {
  if (!recipeIds.length) {
    return [];
  }

  const qf = "id IN [" + recipeIds.map(id => `"${id}"`).join(", ") + "]";
  const { data } = await api.recipes.getAll(1, -1, { queryFilter: qf });
  return data?.items || [];
}

async function updateRecipes(events: RecipeTimelineEventOut[]) {
  const recipeIds: string[] = [];
  events.forEach((event) => {
    if (recipeIds.includes(event.recipeId) || recipes.has(event.recipeId)) {
      return;
    }

    recipeIds.push(event.recipeId);
  });

  const results = await getRecipes(recipeIds);
  results.forEach((result) => {
    if (!result?.id) {
      return;
    }
    recipes.set(result.id, result);
  });
}

async function scrollTimelineEvents() {
  const orderBy = "timestamp";
  const orderDirection = preferences.value.orderDirection === "asc" ? "asc" : "desc";

  const eventTypeValue = `["${preferences.value.types.join("\", \"")}"]`;
  const queryFilter = `(${props.queryFilter}) AND eventType IN ${eventTypeValue}`;

  const response = await api.recipes.getAllTimelineEvents(page.value, perPage, { orderBy, orderDirection, queryFilter });
  page.value += 1;
  if (!response?.data) {
    return;
  }

  const events = response.data.items;
  if (events.length < perPage) {
    hasMore.value = false;
    if (!events.length) {
      return;
    }
  }

  // fetch recipes
  if (props.showRecipeCards) {
    await updateRecipes(events);
  }

  // this is set last so Vue knows to re-render
  timelineEvents.value.push(...events);
}

async function initializeTimelineEvents() {
  loading.value = true;
  ready.value = false;

  page.value = 1;
  hasMore.value = true;
  timelineEvents.value = [];
  await scrollTimelineEvents();

  ready.value = true;
  loading.value = false;
}

const infiniteScroll = useThrottleFn(async () => {
  if (!hasMore.value || loading.value) {
    return;
  }
  loading.value = true;
  try {
    await scrollTimelineEvents();
  }
  finally {
    loading.value = false;
  }
}, 500);

// preload events
initializeTimelineEvents();

onMounted(
  () => {
    document.onscroll = () => {
      // if the inner element is scrollable, let its scroll event handle the infiniteScroll
      const timelineContainerElement = document.getElementById("timeline-container");
      if (timelineContainerElement) {
        const { clientHeight, scrollHeight } = timelineContainerElement;

        // if scrollHeight == clientHeight, the element is not scrollable, so we need to look at the global position
        // if scrollHeight > clientHeight, it is scrollable and we don't need to do anything here
        if (scrollHeight > clientHeight) {
          return;
        }
      }

      const bottomOfWindow = document.documentElement.scrollTop + window.innerHeight >= document.documentElement.offsetHeight - (window.innerHeight * screenBuffer);
      if (bottomOfWindow) {
        infiniteScroll();
      }
    };
  },
);
</script>
