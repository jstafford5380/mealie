<script setup lang="ts">
import type { RecipeNote, RecipeOut } from "~/lib/api/types/recipe";
import { CheckIcon, ChevronDownIcon, ClockIcon } from "@lucide/vue";
import { MdiIcon } from "~/components/ui/mdi-icon";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "~/components/ui/sheet";
import { useRecipeMethod } from "~/composables/recipe-page/use-recipe-method";

/** The reader's method: numbered steps in sections. Tap a step to mark it done and fold it away. */
const props = defineProps<{ recipe: RecipeOut }>();

const {
  sections,
  steps,
  linkedNotes,
  formatDuration,
  isDone,
  toggleDone,
  isSectionDone,
  toggleSection,
} = useRecipeMethod(() => props.recipe);

const notesOpen = ref(false);
const activeNotes = ref<RecipeNote[]>([]);
function openNotes(index: number) {
  activeNotes.value = linkedNotes(steps.value[index]!);
  notesOpen.value = activeNotes.value.length > 0;
}
</script>

<template>
  <section
    v-if="steps.length"
    class="font-sans"
    :aria-label="$t('recipe.instructions')"
  >
    <h2 class="m-0 mb-3 text-xl font-bold tracking-tight">
      {{ $t("recipe.instructions") }}
    </h2>

    <div
      v-for="(section, sectionIndex) in sections"
      :key="sectionIndex"
    >
      <button
        v-if="section.title"
        type="button"
        class="mb-1 mt-6 flex w-full items-center gap-2 border-b pb-2 text-left text-[17px] font-semibold"
        :aria-expanded="!isSectionDone(section)"
        @click="toggleSection(section)"
      >
        <span class="flex-1">{{ section.title }}</span>
        <ChevronDownIcon
          class="size-5 text-muted-foreground transition-transform"
          :class="isSectionDone(section) && '-rotate-90'"
        />
      </button>

      <ol class="m-0 list-none p-0">
        <li
          v-for="index in section.steps"
          :key="steps[index]!.id || index"
          class="border-b border-border/60 last:border-b-0"
        >
          <div
            class="grid grid-cols-[2.75rem_minmax(0,1fr)] gap-x-3 py-4"
            :class="isDone(index) && 'py-3'"
          >
            <button
              type="button"
              class="flex size-11 items-center justify-center rounded-full font-serif text-[26px] leading-none transition-colors focus-visible:outline-2 focus-visible:outline-ring"
              :class="isDone(index) ? 'bg-primary text-primary-foreground text-base' : 'text-primary hover:bg-highlight'"
              :aria-pressed="isDone(index)"
              :aria-label="isDone(index) ? $t('recipe.step-index', { step: index + 1 }) + ' — ' + $t('general.done') : $t('recipe.step-index', { step: index + 1 })"
              @click="toggleDone(index)"
            >
              <CheckIcon
                v-if="isDone(index)"
                class="size-5"
              />
              <template v-else>
                {{ index + 1 }}
              </template>
            </button>

            <div
              class="min-w-0 cursor-pointer pt-1"
              @click="toggleDone(index)"
            >
              <div
                v-if="steps[index]!.summary || steps[index]!.durationSeconds || linkedNotes(steps[index]!).length"
                class="mb-1 flex flex-wrap items-center gap-2"
              >
                <SafeMarkdown
                  v-if="steps[index]!.summary"
                  class="font-semibold [&_p]:m-0"
                  :source="steps[index]!.summary!"
                />
                <span
                  v-if="steps[index]!.durationSeconds"
                  class="inline-flex items-center gap-1 rounded-full bg-subtle px-2 py-0.5 text-xs font-semibold text-subtle-foreground"
                >
                  <ClockIcon class="size-3.5" />
                  {{ formatDuration(steps[index]!.durationSeconds) }}
                </span>
                <button
                  v-if="linkedNotes(steps[index]!).length"
                  type="button"
                  class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold text-primary hover:bg-highlight"
                  @click.stop="openNotes(index)"
                >
                  <MdiIcon
                    :path="$globals.icons.noteTextOutline"
                    class="size-3.5"
                  />
                  {{ $t('recipe.linked-notes-with-count', { count: linkedNotes(steps[index]!).length }) }}
                </button>
              </div>
              <SafeMarkdown
                v-if="!isDone(index)"
                class="recipe-step-text text-[16.5px] leading-relaxed"
                :source="steps[index]!.text || ''"
              />
              <p
                v-else
                class="m-0 line-clamp-1 text-sm text-muted-foreground"
              >
                {{ (steps[index]!.text || '').replace(/<[^>]+>|[*_#>`]/g, '') }}
              </p>
            </div>
          </div>
        </li>
      </ol>
    </div>

    <Sheet v-model:open="notesOpen">
      <SheetContent
        side="bottom"
        class="mx-auto max-h-[80vh] max-w-[900px] overflow-y-auto rounded-t-panel"
      >
        <SheetHeader>
          <SheetTitle>{{ $t('recipe.linked-notes-with-count', { count: activeNotes.length }) }}</SheetTitle>
          <SheetDescription class="sr-only">
            {{ $t('recipe.linked-notes-with-count', { count: activeNotes.length }) }}
          </SheetDescription>
        </SheetHeader>
        <div class="flex flex-col gap-4 px-4 pb-6">
          <div
            v-for="note in activeNotes"
            :key="note.referenceId ?? note.title"
          >
            <div class="mb-1 font-semibold">
              {{ note.title || $t('recipe.note') }}
            </div>
            <SafeMarkdown
              class="text-[15px] leading-relaxed [&_p]:m-0"
              :source="note.text"
            />
          </div>
        </div>
      </SheetContent>
    </Sheet>
  </section>
</template>

<style>
.recipe-step-text p {
  margin: 0;
}
.recipe-step-text p + p {
  margin-top: 0.6em;
}
.recipe-step-text img {
  max-width: 100%;
  height: auto;
  border-radius: 12px;
  margin-top: 0.5rem;
}
.recipe-step-text a {
  color: var(--primary);
  text-decoration: underline;
}
</style>
