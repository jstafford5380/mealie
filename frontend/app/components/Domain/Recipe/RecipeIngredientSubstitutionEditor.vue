<template>
  <div class="flex flex-col gap-2 font-sans">
    <div
      v-for="substitution, i in substitutions"
      :key="i"
    >
      <!-- wraps rather than stacking: on a narrow screen the food takes its own line and the
           note keeps the remove button company -->
      <div class="flex flex-wrap items-center gap-2">
        <SearchSelect
          v-model:search="searchTerms[i]"
          :model-value="foodById(substitution.substituteFoodId)"
          :items="filtered(i)"
          :placeholder="$t('recipe.choose-substitute-food')"
          class="min-w-48 flex-[6_1_12rem]"
          @update:model-value="substitution.substituteFoodId = $event?.id ?? null; emit('food-changed', i)"
        />
        <input
          v-model="substitution.note"
          type="text"
          :placeholder="$t('recipe.note')"
          :aria-label="$t('recipe.note')"
          class="h-10 min-w-32 flex-[4_1_8rem] rounded-control border border-input bg-card px-3 text-[15px] outline-none placeholder:text-muted-foreground/80 focus:border-ring focus:ring-3 focus:ring-ring/25"
        >
        <Button
          variant="ghost"
          size="icon"
          :aria-label="$t('general.delete')"
          :title="$t('general.delete')"
          @click="emit('delete', i)"
        >
          <Trash2Icon class="size-4" />
        </Button>
      </div>
      <slot
        name="after-row"
        :substitution="substitution"
        :index="i"
      />
    </div>
    <Button
      variant="ghost"
      size="sm"
      class="self-start text-primary"
      @click="emit('add')"
    >
      <PlusIcon class="size-4" />
      {{ $t("general.add") }}
    </Button>
  </div>
</template>

<script setup lang="ts">
import { PlusIcon, Trash2Icon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import SearchSelect from "~/components/ui/field/SearchSelect.vue";
import { normalize } from "~/composables/use-utils";
import type { IngredientFoodOut } from "~/lib/api/types/recipe";

/**
 * The shape both tiers share. Callers hold richer rows of their own -- the food dialog tracks a
 * reverse-substitution choice alongside each one -- so rows are mutated in place here and added
 * or removed by the caller, which is the only side that knows what a new row should contain.
 */
export interface EditableSubstitution {
  substituteFoodId?: string | null;
  note?: string | null;
}

interface Props {
  substitutions: EditableSubstitution[];
  foods: IngredientFoodOut[];
  /** Kept for callers; the list now always opens in the top layer. */
  menuAttachTarget?: string;
}

const props = defineProps<Props>();

// One search box per row; matching mirrors the old autocomplete (case- and accent-insensitive).
const searchTerms = ref<string[]>([]);
function filtered(index: number) {
  const term = normalize(searchTerms.value[index] ?? "");
  return term ? props.foods.filter(f => normalize(f.name ?? "").includes(term)) : props.foods;
}
function foodById(id?: string | null) {
  return id ? props.foods.find(f => f.id === id) ?? null : null;
}

const emit = defineEmits<{
  "add": [];
  "delete": [index: number];
  "food-changed": [index: number];
}>();
</script>
