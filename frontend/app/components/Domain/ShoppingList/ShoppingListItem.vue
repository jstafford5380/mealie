<template>
  <div class="overflow-hidden font-sans">
    <template v-if="!edit">
      <div
        ref="swipeRowRef"
        class="group/item relative flex min-h-14 items-start gap-3 px-3 py-2 [touch-action:pan-y]"
        :style="{
          transform: `translateX(${isRtl ? -swiping : swiping}px)`,
          transition: swiping === 0 ? 'transform 0.2s ease' : 'none',
          opacity: swiping >= SWIPE_THRESHOLD ? 0.5 : 1,
        }"
        @touchstart.passive="onSwipeStart({ originalEvent: $event })"
        @touchmove="onSwipeMove({ originalEvent: $event })"
        @touchend="onSwipeEnd"
        @touchcancel="resetSwipe"
      >
        <button
          type="button"
          role="checkbox"
          :aria-checked="listItem.checked"
          :aria-label="listItem.checked ? $t('shopping-list.put-back-item', { item: itemName }) : $t('shopping-list.got-item', { item: itemName })"
          class="mt-1 inline-flex size-[26px] shrink-0 items-center justify-center rounded-full border-2 transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
          :class="listItem.checked ? 'border-primary bg-primary text-primary-foreground' : 'border-muted-foreground/60 bg-card hover:border-primary'"
          @click="toggleChecked"
        >
          <CheckIcon
            v-if="listItem.checked"
            class="size-4 stroke-[3]"
          />
        </button>
        <div class="min-w-0 flex-1 py-0.5">
          <RecipeIngredientListItem
            :ingredient="listItem"
            :class="listItem.checked && 'text-muted-foreground [&_.ing-inline]:line-through'"
          />
          <button
            v-if="!listItem.checked && recipeList.length"
            type="button"
            class="mt-0.5 block max-w-full truncate text-left text-[13px] text-muted-foreground hover:text-primary"
            :aria-expanded="displayRecipeRefs"
            @click="displayRecipeRefs = !displayRecipeRefs"
          >
            {{ $t('shopping-list.for-recipes', { recipes: recipeList.map(r => r.name).join(', ') }) }}
          </button>
          <div
            v-if="listItem.checked"
            class="mt-0.5 text-xs italic text-muted-foreground"
          >
            {{ $t("shopping-list.completed-on", {
              date: listItem.updatedAt ? $d(new Date(listItem.updatedAt)) : '',
            }) }}
          </div>
        </div>
        <div
          v-if="!listItem.checked"
          class="flex shrink-0 items-center"
        >
          <button
            type="button"
            class="inline-flex size-10 items-center justify-center rounded-full text-muted-foreground hover:bg-highlight hover:text-foreground"
            :aria-label="`${$t('general.edit')}: ${itemName}`"
            :title="$t('general.edit')"
            @click="$emit('edit')"
          >
            <PencilIcon class="size-4" />
          </button>
          <DropdownMenu :modal="false">
            <DropdownMenuTrigger as-child>
              <button
                type="button"
                class="handle inline-flex size-10 cursor-grab touch-none items-center justify-center rounded-full text-muted-foreground hover:bg-highlight hover:text-foreground active:cursor-grabbing"
                :aria-label="`${$t('general.actions')}: ${itemName}`"
              >
                <GripVerticalIcon class="size-4" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              align="end"
              class="min-w-40"
            >
              <DropdownMenuItem @select="$emit('edit')">
                {{ $t('general.edit') }}
              </DropdownMenuItem>
              <DropdownMenuItem
                variant="destructive"
                @select="$emit('delete')"
              >
                {{ $t('general.delete') }}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
      <div
        v-if="!listItem.checked && recipeList.length && displayRecipeRefs"
        class="px-3 pb-2 ps-12"
      >
        <RecipeList
          :recipes="recipeList"
          :list-item="listItem"
          :disabled="isOffline"
          :tile="true"
        />
      </div>
    </template>
    <div
      v-else
      class="p-2"
    >
      <ShoppingListItemEditor
        v-model="localListItem"
        :labels="labels"
        :units="units"
        :foods="foods"
        @save="save"
        @cancel="$emit('view')"
        @delete="$emit('delete')"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { CheckIcon, GripVerticalIcon, PencilIcon } from "@lucide/vue";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "~/components/ui/dropdown-menu";
import { useOnline } from "@vueuse/core";
import RecipeIngredientListItem from "../Recipe/RecipeIngredientListItem.vue";
import ShoppingListItemEditor from "./ShoppingListItemEditor.vue";
import RecipeList from "~/components/Domain/Recipe/RecipeList.vue";
import type { ShoppingListItemOut } from "~/lib/api/types/household";
import type { MultiPurposeLabelOut } from "~/lib/api/types/labels";
import type { IngredientUnitOut, IngredientFoodOut, RecipeSummary } from "~/lib/api/types/recipe";

const model = defineModel<ShoppingListItemOut>({ type: Object as () => ShoppingListItemOut, required: true });

const props = defineProps({
  labels: {
    type: Array as () => MultiPurposeLabelOut[],
    required: true,
  },
  units: {
    type: Array as () => IngredientUnitOut[],
    required: true,
  },
  foods: {
    type: Array as () => IngredientFoodOut[],
    required: true,
  },
  recipes: {
    type: Map as unknown as () => Map<string, RecipeSummary>,
    default: undefined,
  },
  edit: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits<{
  (e: "checked" | "save", item: ShoppingListItemOut): void;
  (e: "delete" | "edit" | "view"): void;
}>();

const SWIPE_THRESHOLD = 50;

const { isRtl } = useRtl();
const swipeRowRef = ref<HTMLElement | null>(null);

onMounted(() => {
  const el = swipeRowRef.value;
  if (!el) return;
  el.addEventListener(
    "touchmove",
    (e: TouchEvent) => {
      if (swipeInfo.value.gesture === "swipe") {
        e.preventDefault();
      }
    },
    { passive: false },
  );
});
const displayRecipeRefs = ref(false);
const online = useOnline();
const isOffline = computed(() => online.value === false);

// copy prop value so a refresh doesn't interrupt the user
const localListItem = ref(Object.assign({}, model.value));

const listItem = computed<ShoppingListItemOut>({
  get: () => model.value,
  set: (val: ShoppingListItemOut) => {
    localListItem.value = val;
    model.value = val;
  },
});

function toggleChecked() {
  const updated = { ...model.value, checked: !model.value.checked } as ShoppingListItemOut;
  model.value = updated;
  emit("checked", updated);
}

function save() {
  emit("save", localListItem.value);
}

type SwipeGesture = null | "scroll" | "swipe";

const swipeInfo = ref({
  touchstartX: 0,
  touchstartY: 0,
  touchendX: 0,
  touchendY: 0,
  gesture: null as SwipeGesture,
});

function getSwipePoint(e: any) {
  const touch = e?.touches?.[0] ?? e?.changedTouches?.[0] ?? e;
  return { x: touch?.clientX ?? 0, y: touch?.clientY ?? 0 };
}

function resetSwipe() {
  swipeInfo.value = { touchstartX: 0, touchstartY: 0, touchendX: 0, touchendY: 0, gesture: null };
}

function onSwipeStart(payload: any) {
  const { x, y } = getSwipePoint(payload.originalEvent);
  swipeInfo.value = { touchstartX: x, touchstartY: y, touchendX: x, touchendY: y, gesture: null };
}

function onSwipeMove(payload: any) {
  const { x, y } = getSwipePoint(payload.originalEvent);
  swipeInfo.value.touchendX = x;
  swipeInfo.value.touchendY = y;

  if (!swipeInfo.value.gesture) {
    const deltaX = Math.abs(x - swipeInfo.value.touchstartX);
    const deltaY = Math.abs(y - swipeInfo.value.touchstartY);
    if (deltaY > 8 && deltaY > deltaX) {
      swipeInfo.value.gesture = "scroll";
    }
    else if (deltaX > 8 && deltaX > deltaY) {
      swipeInfo.value.gesture = "swipe";
    }
    else if (deltaX > 8 || deltaY > 8) {
      // Diagonal / ambiguous — default to scroll
      swipeInfo.value.gesture = "scroll";
    }
  }
}

function onSwipeEnd() {
  if (swipeInfo.value.gesture === "swipe" && swiping.value >= SWIPE_THRESHOLD) {
    toggleChecked();
  }
  resetSwipe();
}

const swiping = computed(() => {
  if (swipeInfo.value.gesture !== "swipe") {
    return 0;
  }
  const deltaX = isRtl.value
    ? swipeInfo.value.touchstartX - swipeInfo.value.touchendX
    : swipeInfo.value.touchendX - swipeInfo.value.touchstartX;
  return Math.max(0, Math.min(deltaX, 100));
});

const itemName = computed(() => listItem.value.food?.name || listItem.value.note || listItem.value.display || "");

const recipeList = computed<RecipeSummary[]>(() => {
  const ret: RecipeSummary[] = [];
  if (!listItem.value.recipeReferences) return ret;
  listItem.value.recipeReferences.forEach((ref) => {
    const recipe = props.recipes?.get(ref.recipeId);
    if (recipe) ret.push(recipe);
  });
  return ret;
});
</script>
