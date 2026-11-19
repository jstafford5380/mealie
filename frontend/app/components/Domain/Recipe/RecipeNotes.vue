<template>
  <div
    v-if="model.length > 0 || edit"
    :class="edit ? 'mt-8' : 'flex flex-col gap-3 font-sans'"
  >
    <h2
      v-if="edit"
      class="my-4 text-h5 font-weight-medium opacity-80"
    >
      {{ $t("recipe.note") }}
    </h2>
    <h2
      v-else
      class="m-0 text-xl font-bold tracking-tight"
    >
      {{ $t("recipe.note") }}
    </h2>
    <div
      v-for="(note, index) in model"
      :id="'note' + index"
      :key="'note' + index"
      :class="edit && 'mt-1'"
    >
      <v-card v-if="edit">
        <v-card-text>
          <div class="d-flex align-center">
            <v-text-field
              v-model="model[index]['title']"
              variant="underlined"
              :label="$t('recipe.title')"
            />
            <v-btn
              icon
              class="mr-2"
              elevation="0"
              @click="removeByIndex(index)"
            >
              <v-icon>{{ $globals.icons.delete }}</v-icon>
            </v-btn>
          </div>
          <v-textarea
            v-model="model[index]['text']"
            variant="underlined"
            auto-grow
            :placeholder="$t('recipe.note')"
          />
        </v-card-text>
      </v-card>
      <div
        v-else
        class="rounded-card border-s-4 border-brand bg-card px-4 py-3 font-sans"
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

    <div
      v-if="edit"
      class="d-flex justify-end"
    >
      <BaseButton
        class="ml-auto my-2"
        @click="addNote"
      >
        {{ $t("general.add") }}
      </BaseButton>
    </div>
  </div>
</template>

<script setup lang="ts">
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
