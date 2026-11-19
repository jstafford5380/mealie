<template>
  <div class="flex flex-col gap-3 font-sans">
    <form
      class="relative flex items-center gap-2 rounded-card border bg-card p-1.5 shadow-sm focus-within:border-ring"
      @submit.prevent="submit()"
    >
      <MdiIcon
        :path="$globals.icons.foods"
        class="ms-2 size-5 shrink-0 text-muted-foreground"
      />
      <input
        ref="inputRef"
        v-model="search"
        type="text"
        role="combobox"
        autocomplete="off"
        autocapitalize="none"
        :aria-label="$t('shopping-list.add-item')"
        :placeholder="$t('shopping-list.add-item-placeholder')"
        :aria-expanded="suggestionsOpen"
        :aria-controls="listId"
        :aria-activedescendant="highlighted >= 0 ? `${listId}-${highlighted}` : undefined"
        class="h-11 min-w-0 flex-1 bg-transparent px-1 text-base outline-none placeholder:text-muted-foreground/80"
        @input="highlighted = -1; suggestionsOpen = true"
        @keydown.down.prevent="move(1)"
        @keydown.up.prevent="move(-1)"
        @keydown.escape="suggestionsOpen = false"
        @keydown.enter.prevent="onEnter"
        @blur="closeSoon"
      >
      <button
        v-if="search"
        type="button"
        class="inline-flex size-9 shrink-0 items-center justify-center rounded-full text-muted-foreground hover:bg-highlight"
        :aria-label="$t('general.clear')"
        @click="search = ''; inputRef?.focus()"
      >
        <XIcon class="size-4" />
      </button>
      <button
        type="button"
        class="inline-flex size-10 shrink-0 items-center justify-center rounded-control text-muted-foreground transition-colors hover:bg-highlight hover:text-foreground"
        :class="showDetails && 'bg-highlight text-foreground'"
        :aria-label="showDetails ? $t('shopping-list.fewer-options') : $t('shopping-list.more-options')"
        :title="showDetails ? $t('shopping-list.fewer-options') : $t('shopping-list.more-options')"
        :aria-expanded="showDetails"
        @click="showDetails = !showDetails"
      >
        <SlidersHorizontalIcon class="size-4" />
      </button>
      <Button
        type="submit"
        class="shrink-0"
      >
        {{ $t('general.add') }}
      </Button>

      <ul
        v-show="suggestionsOpen && search.trim() && suggestions.length"
        :id="listId"
        role="listbox"
        class="absolute inset-x-0 z-[1100] m-0 max-h-64 list-none overflow-y-auto rounded-card border bg-popover p-1 shadow-md"
        :class="suggestionsAbove ? 'bottom-full mb-2' : 'top-full mt-2'"
      >
        <li
          v-for="(food, index) in suggestions"
          :id="`${listId}-${index}`"
          :key="food.id"
          role="option"
          :aria-selected="index === highlighted"
          class="flex min-h-10 cursor-pointer items-center rounded-item px-3 text-[15px]"
          :class="index === highlighted ? 'bg-highlight text-highlight-foreground' : 'hover:bg-highlight/60'"
          @mousedown.prevent="pick(food)"
          @mousemove="highlighted = index"
        >
          {{ foodName(food) }}
        </li>
      </ul>
    </form>

    <div
      v-if="showDetails"
      class="flex flex-col gap-3 rounded-card border bg-card p-3"
    >
      <p
        v-if="pickedFood"
        class="m-0 text-sm"
      >
        <span class="text-muted-foreground">{{ $t('shopping-list.food') }}:</span>
        <span class="font-semibold"> {{ foodName(pickedFood) }}</span>
      </p>
      <ShoppingListItemDetails
        v-model="listItem"
        :labels="labels"
        :units="units"
        @save="submit()"
      />
      <div class="flex flex-wrap items-center gap-2">
        <Button
          v-if="search?.trim() && !pickedFood && !resolveFood(search, foods)"
          variant="outline"
          @click="createFoodAndSubmit"
        >
          <MdiIcon
            :path="$globals.icons.foods"
            class="size-4"
          />
          {{ $t('shopping-list.save-as-new-food', { text: search.trim() }) }}
        </Button>
        <Button
          class="ms-auto"
          @click="submit()"
        >
          {{ $t('general.save') }}
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { SlidersHorizontalIcon, XIcon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { useFoodName, useFoodPlurality } from "~/composables/recipes/use-recipe-ingredients";
import { resolveFood, useShoppingListItemEditor } from "~/composables/shopping-list-page/use-shopping-list-item-editor";
import { useSearch } from "~/composables/use-search";
import type { IngredientFoodOut, ShoppingListItemOut } from "~/lib/api/types/household";
import type { MultiPurposeLabelOut } from "~/lib/api/types/labels";
import type { IngredientUnitOut } from "~/lib/api/types/recipe";
import ShoppingListItemDetails from "./ShoppingListItemDetails.vue";

const listItem = defineModel<ShoppingListItemOut>({ required: true });
const showDetails = defineModel<boolean>("details", { default: false });

const props = defineProps({
  /** Open the suggestions above the field (the phone drawer sits at the bottom). */
  suggestionsAbove: {
    type: Boolean,
    default: false,
  },
  foods: {
    type: Array as () => IngredientFoodOut[],
    required: true,
  },
  labels: {
    type: Array as () => MultiPurposeLabelOut[],
    required: true,
  },
  units: {
    type: Array as () => IngredientUnitOut[],
    required: true,
  },
});

const emit = defineEmits<{ (e: "save"): void }>();

const { createAssignFood } = useShoppingListItemEditor(listItem);

const inputRef = ref<HTMLInputElement | null>(null);
const selected = ref<IngredientFoodOut | null>(null);
const listId = `quick-add-${useId()}`;
const suggestionsOpen = ref(false);
// Nothing is highlighted until the arrow keys move there, so Enter never picks a fuzzy match on its own
const highlighted = ref(-1);

const { search, filtered: filteredFoods } = useSearch(computed(() => props.foods));

// Show suggestions the way the list will display the new item (no quantity or unit)
const { shouldPluralizeFood } = useFoodPlurality();
const usePlural = computed(() => shouldPluralizeFood({ quantity: 0 }));
function foodName(food: IngredientFoodOut) {
  return useFoodName(food, usePlural.value);
}

const suggestions = computed(() => (search.value?.trim() ? filteredFoods.value.slice(0, 30) : []));

// Picking a suggestion is an explicit choice of that food; typing changes the text, which drops the choice
const pickedFood = computed(() => selected.value ?? undefined);
watch(search, (value) => {
  if (selected.value && value !== foodName(selected.value)) {
    selected.value = null;
  }
});

function move(step: number) {
  suggestionsOpen.value = true;
  const count = suggestions.value.length;
  if (!count) {
    return;
  }
  highlighted.value = highlighted.value + step < -1 ? count - 1 : (highlighted.value + step) % count;
}

function closeSoon() {
  setTimeout(() => {
    suggestionsOpen.value = false;
  }, 120);
}

// With the options open, picking a food only fills it in so the other fields can still be set before saving
function pick(food: IngredientFoodOut) {
  selected.value = food;
  search.value = foodName(food);
  suggestionsOpen.value = false;
  highlighted.value = -1;
  if (!showDetails.value) {
    submit();
  }
}

function onEnter() {
  const food = highlighted.value >= 0 ? suggestions.value[highlighted.value] : undefined;
  if (food && suggestionsOpen.value) {
    pick(food);
    return;
  }
  submit();
}

// Free text is a food only on an exact match; anything else is kept verbatim as a note,
// combined with anything typed in the note field
function submit(createdFood?: IngredientFoodOut) {
  const text = search.value?.trim() || "";
  const food = createdFood ?? pickedFood.value ?? resolveFood(text, props.foods);
  const note = food ? listItem.value.note : [text, listItem.value.note].filter(Boolean).join(", ");
  if (!food && !note) {
    return;
  }

  listItem.value.food = food ?? null;
  listItem.value.foodId = food?.id ?? null;
  if (food && !listItem.value.labelId) {
    listItem.value.label = food.label;
    listItem.value.labelId = food.labelId;
  }
  listItem.value.note = note;
  listItem.value.quantity ||= 0;
  emit("save");

  selected.value = null;
  search.value = "";
  suggestionsOpen.value = false;
  highlighted.value = -1;
  inputRef.value?.focus();
}

async function createFoodAndSubmit() {
  await createAssignFood(search.value.trim());
  if (listItem.value.foodId) {
    submit(listItem.value.food as IngredientFoodOut);
  }
}
</script>
