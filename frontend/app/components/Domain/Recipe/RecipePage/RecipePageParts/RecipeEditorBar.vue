<script setup lang="ts">
import type { RecipeOut } from "~/lib/api/types/recipe";
import { CheckIcon, EllipsisVerticalIcon, XIcon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "~/components/ui/dropdown-menu";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { EditorMode, usePageState } from "~/composables/recipe-page/shared-state";

/** Sticky bar for the recipe editor: form/JSON switch, parse, delete, cancel and save. */
const props = defineProps<{ recipe: RecipeOut; saving?: boolean }>();
const emit = defineEmits<{ save: []; close: []; delete: [] }>();

const { isEditJSON, setEditMode, toggleIsParsing } = usePageState(props.recipe.slug);
const deleteDialog = ref(false);

const i18n = useI18n();
const modes = computed(() => [
  { value: EditorMode.FORM, label: i18n.t("recipe.editor-form") },
  { value: EditorMode.JSON, label: i18n.t("general.json") },
]);
</script>

<template>
  <div class="sticky top-14 z-[900] -mx-4 mb-6 border-b bg-background/95 px-4 py-2.5 font-sans backdrop-blur sm:-mx-6 sm:px-6 lg:-mx-8 lg:px-8 print:hidden">
    <div class="flex items-center gap-2 sm:gap-3">
      <Button
        variant="ghost"
        size="icon"
        :aria-label="$t('general.cancel')"
        :title="$t('general.cancel')"
        @click="emit('close')"
      >
        <XIcon class="size-5" />
      </Button>
      <div class="min-w-0 flex-1">
        <div class="text-xs font-semibold text-muted-foreground">
          {{ $t("recipe.edit-recipe") }}
        </div>
        <div class="truncate font-serif text-lg leading-tight">
          {{ recipe.name || $t("recipe.untitled-recipe") }}
        </div>
      </div>

      <div
        role="radiogroup"
        :aria-label="$t('recipe.editor-mode')"
        class="inline-flex rounded-control bg-muted p-1 text-sm max-sm:display-none"
      >
        <button
          v-for="mode in modes"
          :key="mode.value"
          type="button"
          role="radio"
          :aria-checked="(mode.value === EditorMode.JSON) === isEditJSON"
          class="rounded-item px-3 py-1 font-semibold transition-colors"
          :class="(mode.value === EditorMode.JSON) === isEditJSON ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'"
          @click="setEditMode(mode.value)"
        >
          {{ mode.label }}
        </button>
      </div>

      <DropdownMenu :modal="false">
        <DropdownMenuTrigger as-child>
          <Button
            variant="ghost"
            size="icon"
            :aria-label="$t('general.more')"
          >
            <EllipsisVerticalIcon class="size-5" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent
          align="end"
          class="min-w-52"
        >
          <DropdownMenuItem
            class="sm:display-none"
            @select="setEditMode(isEditJSON ? EditorMode.FORM : EditorMode.JSON)"
          >
            <MdiIcon
              :path="isEditJSON ? $globals.icons.edit : $globals.icons.codeBraces"
              class="size-4"
            />
            {{ isEditJSON ? $t("recipe.editor-form") : $t("general.json") }}
          </DropdownMenuItem>
          <DropdownMenuItem
            v-if="!isEditJSON && recipe.recipeIngredient.length"
            @select="toggleIsParsing(true)"
          >
            <MdiIcon
              :path="$globals.icons.foods"
              class="size-4"
            />
            {{ $t("recipe.parse-ingredients") }}
          </DropdownMenuItem>
          <DropdownMenuItem
            variant="destructive"
            @select="deleteDialog = true"
          >
            <MdiIcon
              :path="$globals.icons.delete"
              class="size-4"
            />
            {{ $t("recipe.delete-recipe") }}
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <Button
        :disabled="saving"
        @click="emit('save')"
      >
        <CheckIcon class="size-[18px]" />
        {{ $t("general.save") }}
      </Button>
    </div>

    <BaseDialog
      v-model="deleteDialog"
      :title="$t('recipe.delete-recipe')"
      color="error"
      :icon="$globals.icons.alertCircle"
      can-delete
      @delete="emit('delete')"
    >
      <p class="m-0 px-6 pb-2 text-[15px]">
        {{ $t("recipe.delete-confirmation") }}
      </p>
    </BaseDialog>
  </div>
</template>
