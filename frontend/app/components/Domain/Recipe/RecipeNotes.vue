<template>
  <!-- Reader -->
  <div
    v-if="!edit && model.length > 0"
    class="flex flex-col gap-3 font-sans"
  >
    <h2 class="m-0 text-xl font-bold tracking-tight">
      {{ $t("recipe.note") }}
    </h2>
    <div
      v-for="(note, index) in model"
      :id="'note' + index"
      :key="'note' + index"
      class="rounded-card border-s-4 border-brand bg-card px-4 py-3"
    >
      <div
        v-if="note.title"
        class="mb-1 font-semibold"
      >
        {{ note.title }}
      </div>
      <SafeMarkdown
        class="text-[15.5px] leading-relaxed [&_p]:m-0 [&_p+p]:mt-2"
        :source="note.text"
      />
    </div>
  </div>

  <!-- Editor -->
  <div
    v-else-if="edit"
    class="flex flex-col gap-4 font-sans"
  >
    <div
      v-for="(note, index) in model"
      :id="'note' + index"
      :key="note.referenceId || 'note' + index"
      class="flex flex-col gap-3 rounded-card border bg-background p-4"
    >
      <div class="flex items-end gap-2">
        <div class="min-w-0 flex-1">
          <TextField
            v-model="model[index]!.title"
            :label="$t('recipe.title')"
          />
        </div>
        <Button
          variant="ghost"
          size="icon"
          class="text-destructive hover:text-destructive"
          :aria-label="`${$t('general.remove')}: ${note.title || $t('recipe.note')}`"
          @click="removeByIndex(index)"
        >
          <Trash2Icon class="size-4" />
        </Button>
      </div>
      <TextareaField
        v-model="model[index]!.text"
        :label="$t('recipe.note')"
        :rows="3"
      />
    </div>
    <Button
      variant="outline"
      class="self-start"
      @click="addNote"
    >
      <PlusIcon class="size-4" />
      {{ $t("recipe.add-note") }}
    </Button>
  </div>
</template>

<script setup lang="ts">
import { PlusIcon, Trash2Icon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import TextareaField from "~/components/ui/field/TextareaField.vue";
import TextField from "~/components/ui/field/TextField.vue";
import { uuid4 } from "~/composables/use-utils";
import type { RecipeNote } from "~/lib/api/types/recipe";

const model = defineModel<RecipeNote[]>({ default: () => [] });

defineProps({
  edit: {
    type: Boolean,
    default: true,
  },
});

function addNote() {
  model.value = [...model.value, { title: "", text: "", referenceId: uuid4() }];
}

function removeByIndex(index: number) {
  const newNotes = [...model.value];
  newNotes.splice(index, 1);
  model.value = newNotes;
}
</script>
