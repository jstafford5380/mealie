<script setup lang="ts">
import type { RecipeAsset, RecipeIngredient, RecipeNote, RecipeOut, RecipeStep } from "~/lib/api/types/recipe";
import { EllipsisVerticalIcon, GripVerticalIcon, LinkIcon, PlusIcon, Trash2Icon } from "@lucide/vue";
import { VueDraggable } from "vue-draggable-plus";
import DropZone from "~/components/global/DropZone.vue";
import RecipeDialogBulkAdd from "~/components/Domain/Recipe/RecipeDialogBulkAdd.vue";
import RecipeIngredientHtml from "~/components/Domain/Recipe/RecipeIngredientHtml.vue";
import { Button } from "~/components/ui/button";
import { Checkbox } from "~/components/ui/checkbox";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "~/components/ui/dropdown-menu";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { useStaticRoutes, useUserApi } from "~/composables/api";
import { useExtractIngredientReferences } from "~/composables/recipe-page/use-extract-ingredient-references";
import { alert } from "~/composables/use-toast";
import { uuid4 } from "~/composables/use-utils";
import { mergeSteps, type StepMerge, undoStepMerge } from "~/lib/recipe/instruction-merge";
import CookTime from "./CookTime.vue";

/** The recipe editor's method: step cards with sections, durations, links to ingredients and notes, and images. */
const steps = defineModel<RecipeStep[]>({ required: true });
const assets = defineModel<RecipeAsset[]>("assets", { default: () => [] });
const props = withDefaults(defineProps<{ recipe: RecipeOut; scale?: number }>(), { scale: 1 });

const i18n = useI18n();

// ---- adding
function newStep(text = ""): RecipeStep {
  return { id: uuid4(), text, title: "", summary: "", ingredientReferences: [], noteReferences: [], durationSeconds: null };
}
function addStep() {
  steps.value.push(newStep());
}
function addSteps(lines: string[]) {
  steps.value.push(...lines.map(line => newStep(line)));
}
function insert(index: number) {
  steps.value.splice(index, 0, newStep());
}

// ---- sections: a step with a title starts a section
const sectionShown = ref<Record<string, boolean>>({});
const sectionToFocus = ref<string | null>(null);
function hasSection(step: RecipeStep) {
  return !!step.title || !!(step.id && sectionShown.value[step.id]);
}
function toggleSection(step: RecipeStep) {
  if (!step.id) {
    return;
  }
  if (hasSection(step)) {
    // the menu entry clears the section, so the title goes with it
    step.title = "";
    sectionShown.value = { ...sectionShown.value, [step.id]: false };
  }
  else {
    sectionShown.value = { ...sectionShown.value, [step.id]: true };
    sectionToFocus.value = step.id;
  }
}
function focusSection(el: unknown, id?: string) {
  if (el instanceof HTMLInputElement && id && sectionToFocus.value === id) {
    sectionToFocus.value = null;
    nextTick(() => el.focus());
  }
}

// ---- merge, move
const mergeHistory = ref<StepMerge[]>([]);
function mergeAbove(index: number) {
  const merge = mergeSteps(steps.value, index - 1, index);
  if (merge) {
    mergeHistory.value.push(merge);
  }
}
function undoMerge(event: KeyboardEvent) {
  if (!(event.ctrlKey || event.metaKey) || event.code !== "KeyZ") {
    return;
  }
  const last = mergeHistory.value.pop();
  if (last) {
    event.preventDefault();
    undoStepMerge(steps.value, last);
  }
}
function moveTo(dest: "top" | "bottom", index: number) {
  const [step] = steps.value.splice(index, 1);
  if (!step) {
    return;
  }
  if (dest === "top") {
    steps.value.unshift(step);
  }
  else {
    steps.value.push(step);
  }
}

const preview = ref<Record<string, boolean>>({});
function togglePreview(step: RecipeStep) {
  const id = step.id || "";
  preview.value = { ...preview.value, [id]: !preview.value[id] };
}

// ---- linked ingredients and notes
const ingredientByRef = computed(() => {
  const map: Record<string, RecipeIngredient> = {};
  for (const ing of props.recipe.recipeIngredient) {
    if (ing.referenceId) {
      map[ing.referenceId] = ing;
    }
  }
  return map;
});
const noteByRef = computed(() => {
  const map: Record<string, RecipeNote> = {};
  for (const note of props.recipe.notes ?? []) {
    if (note.referenceId) {
      map[note.referenceId] = note;
    }
  }
  return map;
});
function linkedIngredients(step: RecipeStep) {
  return (step.ingredientReferences ?? [])
    .map(r => (r.referenceId ? ingredientByRef.value[r.referenceId] : undefined))
    .filter((i): i is RecipeIngredient => !!i);
}
function linkedNotes(step: RecipeStep) {
  return (step.noteReferences ?? [])
    .map(r => (r.referenceId ? noteByRef.value[r.referenceId] : undefined))
    .filter((n): n is RecipeNote => !!n);
}

const linkDialog = ref(false);
const linkIndex = ref(0);
const linkRefs = ref<string[]>([]);
const linkNotes = ref<string[]>([]);
const linkStep = computed(() => steps.value[linkIndex.value]);
const hasNextStep = computed(() => linkIndex.value < steps.value.length - 1);
const linkableNotes = computed(() => (props.recipe.notes ?? []).filter((n): n is RecipeNote & { referenceId: string } => !!n.referenceId));

// The ingredient's section heading carries down to the ingredients below it.
const ingredientSection = computed(() => {
  const map: Record<string, string> = {};
  let current = "";
  for (const ing of props.recipe.recipeIngredient) {
    if (ing.title) {
      current = ing.title;
    }
    if (ing.referenceId) {
      map[ing.referenceId] = current;
    }
  }
  return map;
});
const usedElsewhere = computed(() => {
  const used = new Set<string>();
  steps.value.forEach((step, i) => {
    if (i !== linkIndex.value) {
      step.ingredientReferences?.forEach(r => r.referenceId && used.add(r.referenceId));
    }
  });
  return used;
});
function grouped(used: boolean) {
  const groups: { title: string; items: RecipeIngredient[] }[] = [];
  for (const ing of props.recipe.recipeIngredient) {
    if (!ing.referenceId || usedElsewhere.value.has(ing.referenceId) !== used) {
      continue;
    }
    const title = ingredientSection.value[ing.referenceId] || "";
    let group = groups.find(g => g.title === title);
    if (!group) {
      group = { title, items: [] };
      groups.push(group);
    }
    group.items.push(ing);
  }
  return groups;
}
const unlinkedGroups = computed(() => grouped(false));
const linkedElsewhereGroups = computed(() => grouped(true));

// Templates unwrap refs, so the list is named rather than passed.
function toggleLink(list: "ingredients" | "notes", id: string, on: boolean) {
  const target = list === "ingredients" ? linkRefs : linkNotes;
  target.value = on ? [...new Set([...target.value, id])] : target.value.filter(x => x !== id);
}

function openLinks(index: number) {
  const step = steps.value[index];
  if (!step) {
    return;
  }
  linkIndex.value = index;
  linkRefs.value = (step.ingredientReferences ?? []).map(r => r.referenceId ?? "").filter(Boolean);
  linkNotes.value = (step.noteReferences ?? []).map(r => r.referenceId ?? "").filter(Boolean);
  linkDialog.value = true;
}
function saveLinks() {
  const step = linkStep.value;
  if (step) {
    step.ingredientReferences = linkRefs.value.map(referenceId => ({ referenceId }));
    step.noteReferences = linkNotes.value.map(referenceId => ({ referenceId }));
  }
  linkDialog.value = false;
}
function saveAndNext() {
  const next = linkIndex.value + 1;
  saveLinks();
  nextTick(() => openLinks(next));
}
const { extractIngredientReferences } = useExtractIngredientReferences();
function autoLink() {
  const found = extractIngredientReferences(props.recipe.recipeIngredient, linkRefs.value, linkStep.value?.text ?? "");
  linkRefs.value = [...new Set([...linkRefs.value, ...found])];
}

// ---- images
const api = useUserApi();
const { recipeAssetPath } = useStaticRoutes();
const uploading = ref<Record<string, boolean>>({});

function embed(step: RecipeStep, asset: RecipeAsset) {
  assets.value = [...(assets.value ?? []), asset];
  const url = recipeAssetPath(props.recipe.id, asset.fileName as string);
  step.text = `${step.text ?? ""}<img src="${url}" height="100%" width="100%"/>`;
}
async function dropFiles(step: RecipeStep, files: File[]) {
  const file = files?.[0];
  if (!file || !file.type.startsWith("image/")) {
    return;
  }
  uploading.value = { ...uploading.value, [step.id!]: true };
  const { data } = await api.recipes.createAsset(props.recipe.slug, {
    name: file.name,
    icon: "mdi-file-image",
    file,
    extension: file.name.split(".").pop() || "",
  });
  uploading.value = { ...uploading.value, [step.id!]: false };
  if (data) {
    embed(step, data);
  }
}
/** Images dragged out of another tab carry a URL; the server fetches them. */
async function dropUrl(step: RecipeStep, url: string) {
  uploading.value = { ...uploading.value, [step.id!]: true };
  const { data } = await api.recipes.createAssetFromUrl(props.recipe.slug, url);
  uploading.value = { ...uploading.value, [step.id!]: false };
  if (!data) {
    alert.error(i18n.t("recipe.failed-to-attach-image"));
    return;
  }
  embed(step, data);
}
/** blob: images can't be read from here, so say what does work. */
function dropUnsupported() {
  alert.error(i18n.t("recipe.image-drop-unsupported"));
}
function pickImage(step: RecipeStep) {
  const input = document.createElement("input");
  input.type = "file";
  input.accept = "image/*";
  input.onchange = async () => {
    if (input.files) {
      await dropFiles(step, Array.from(input.files));
    }
    input.remove();
  };
  input.click();
}

function menuItems(step: RecipeStep, index: number) {
  return [
    { key: "section", label: hasSection(step) ? i18n.t("recipe.clear-section") : i18n.t("recipe.add-section"), run: () => toggleSection(step) },
    { key: "link", label: i18n.t("recipe.link-references"), run: () => openLinks(index) },
    { key: "image", label: i18n.t("recipe.upload-image"), run: () => pickImage(step) },
    { key: "preview", label: preview.value[step.id || ""] ? i18n.t("recipe.edit-markdown") : i18n.t("markdown-editor.preview-markdown-button-label"), run: () => togglePreview(step), separator: true },
    ...(index > 0 ? [{ key: "merge", label: i18n.t("recipe.merge-above"), run: () => mergeAbove(index) }] : []),
    { key: "top", label: i18n.t("recipe.move-to-top"), run: () => moveTo("top", index) },
    { key: "bottom", label: i18n.t("recipe.move-to-bottom"), run: () => moveTo("bottom", index) },
    { key: "above", label: i18n.t("recipe.insert-above"), run: () => insert(index), separator: true },
    { key: "below", label: i18n.t("recipe.insert-below"), run: () => insert(index + 1) },
  ];
}
</script>

<template>
  <div
    class="font-sans"
    @keydown="undoMerge"
  >
    <VueDraggable
      v-if="steps.length"
      v-model="steps"
      handle=".step-handle"
      :delay="250"
      :delay-on-touch-only="true"
      :animation="200"
      ghost-class="opacity-50"
      class="flex flex-col gap-3"
    >
      <div
        v-for="(step, index) in steps"
        :key="step.id!"
      >
        <input
          v-if="hasSection(step)"
          :ref="el => focusSection(el, step.id)"
          v-model="step.title"
          type="text"
          :placeholder="$t('recipe.section-title')"
          :aria-label="$t('recipe.section-title')"
          class="mb-2 mt-4 h-10 w-full max-w-md border-0 border-b-2 border-primary/40 bg-transparent px-1 text-[17px] font-semibold outline-none placeholder:font-normal placeholder:text-muted-foreground/80 focus:border-primary"
        >
        <div class="rounded-card border bg-background p-3 sm:p-4">
          <div class="flex flex-wrap items-center gap-2">
            <button
              type="button"
              class="step-handle inline-flex h-10 w-6 shrink-0 cursor-grab touch-none items-center justify-center rounded-item text-muted-foreground hover:bg-highlight hover:text-foreground active:cursor-grabbing"
              :aria-label="$t('general.drag-to-reorder')"
              :title="$t('general.drag-to-reorder')"
            >
              <GripVerticalIcon class="size-4" />
            </button>
            <span
              class="w-7 shrink-0 text-center font-serif text-2xl leading-none text-primary"
              aria-hidden="true"
            >{{ index + 1 }}</span>
            <input
              v-model="step.summary"
              type="text"
              :placeholder="$t('recipe.step-index', { step: index + 1 })"
              :aria-label="$t('recipe.step-index', { step: index + 1 })"
              class="h-10 min-w-0 flex-1 basis-40 rounded-control border border-transparent bg-transparent px-2 text-[16px] font-semibold outline-none placeholder:font-normal placeholder:text-muted-foreground/80 hover:border-input focus:border-ring focus:bg-card focus:ring-3 focus:ring-ring/25"
            >
            <div class="ms-auto flex items-center gap-1">
              <CookTime
                :model-value="step.durationSeconds ?? null"
                is-edit-mode
                @update:model-value="step.durationSeconds = $event"
              />
              <DropdownMenu :modal="false">
                <DropdownMenuTrigger as-child>
                  <Button
                    variant="ghost"
                    size="icon"
                    :aria-label="$t('recipe.step-options')"
                  >
                    <EllipsisVerticalIcon class="size-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent
                  align="end"
                  class="min-w-52"
                >
                  <template
                    v-for="item in menuItems(step, index)"
                    :key="item.key"
                  >
                    <DropdownMenuSeparator v-if="item.separator" />
                    <DropdownMenuItem @select="item.run()">
                      {{ item.label }}
                    </DropdownMenuItem>
                  </template>
                </DropdownMenuContent>
              </DropdownMenu>
              <Button
                variant="ghost"
                size="icon"
                class="text-muted-foreground hover:text-destructive"
                :aria-label="$t('general.delete')"
                :title="$t('general.delete')"
                @click="steps.splice(index, 1)"
              >
                <Trash2Icon class="size-4" />
              </Button>
            </div>
          </div>

          <DropZone
            class="mt-2"
            @drop="files => dropFiles(step, files)"
            @drop-url="url => dropUrl(step, url)"
            @drop-unsupported="dropUnsupported"
          >
            <MarkdownEditor
              v-model="step.text"
              :preview="!!preview[step.id || '']"
              :display-preview="false"
              :textarea="{ hint: $t('recipe.attach-images-hint'), placeholder: $t('recipe.step-index', { step: index + 1 }) }"
            />
            <div
              v-if="uploading[step.id || '']"
              class="mt-2 h-1 overflow-hidden rounded-full bg-muted"
            >
              <div class="h-full w-1/3 animate-pulse rounded-full bg-primary" />
            </div>
          </DropZone>

          <div class="mt-3 flex flex-wrap items-center gap-1.5">
            <span
              v-for="ing in linkedIngredients(step)"
              :key="ing.referenceId"
              class="inline-flex max-w-full items-center rounded-full bg-subtle px-2.5 py-0.5 text-[13px] text-subtle-foreground [&_p]:m-0 [&_p]:inline"
            >
              <RecipeIngredientHtml
                :ingredient="ing"
                :scale="scale"
              />
            </span>
            <span
              v-for="note in linkedNotes(step)"
              :key="note.referenceId"
              class="inline-flex items-center gap-1 rounded-full border-s-2 border-brand bg-card px-2.5 py-0.5 text-[13px]"
            >
              <MdiIcon
                :path="$globals.icons.noteTextOutline"
                class="size-3.5"
              />
              {{ note.title || $t('recipe.note') }}
            </span>
            <Button
              variant="ghost"
              size="sm"
              class="h-7 text-primary"
              @click="openLinks(index)"
            >
              <LinkIcon class="size-3.5" />
              {{ linkedIngredients(step).length || linkedNotes(step).length ? $t('general.edit') : $t('recipe.link-references') }}
            </Button>
          </div>
        </div>
      </div>
    </VueDraggable>
    <p
      v-else
      class="m-0 rounded-card border border-dashed px-4 py-6 text-center text-sm text-muted-foreground"
    >
      {{ $t('recipe.no-steps-yet') }}
    </p>

    <div class="mt-4 flex flex-wrap justify-end gap-2">
      <RecipeDialogBulkAdd @bulk-data="addSteps" />
      <Button @click="addStep">
        <PlusIcon class="size-4" />
        {{ $t('recipe.add-step') }}
      </Button>
    </div>

    <!-- Link ingredients and notes to a step -->
    <BaseDialog
      v-model="linkDialog"
      :title="$t('recipe.link-references')"
      :icon="$globals.icons.link"
      max-width="600px"
    >
      <div class="flex max-h-[60dvh] flex-col gap-4 overflow-y-auto px-6 pb-2 font-sans">
        <p class="m-0 rounded-control bg-muted px-3 py-2 text-sm leading-relaxed text-muted-foreground">
          <span class="font-semibold text-foreground">{{ $t('recipe.step-index', { step: linkIndex + 1 }) }}.</span>
          {{ linkStep?.text }}
        </p>
        <template
          v-for="block in [{ key: 'free', title: $t('recipe.unlinked'), groups: unlinkedGroups }, { key: 'used', title: $t('recipe.linked-to-other-step'), groups: linkedElsewhereGroups }]"
          :key="block.key"
        >
          <section
            v-if="block.groups.length"
            class="flex flex-col"
          >
            <h3 class="m-0 mb-1 text-sm font-semibold">
              {{ block.title }}
            </h3>
            <template
              v-for="group in block.groups"
              :key="group.title"
            >
              <div
                v-if="group.title"
                class="mt-2 text-xs font-semibold text-muted-foreground"
              >
                {{ group.title }}
              </div>
              <label
                v-for="ing in group.items"
                :key="ing.referenceId"
                class="flex cursor-pointer items-center gap-3 rounded-item px-1 py-1.5 text-[15px] hover:bg-highlight/50 [&_p]:m-0"
              >
                <Checkbox
                  :model-value="linkRefs.includes(ing.referenceId!)"
                  class="size-5"
                  @update:model-value="toggleLink('ingredients', ing.referenceId!, !!$event)"
                />
                <RecipeIngredientHtml
                  :ingredient="ing"
                  :scale="scale"
                />
              </label>
            </template>
          </section>
        </template>
        <section class="flex flex-col border-t pt-3">
          <h3 class="m-0 mb-1 text-sm font-semibold">
            {{ $t('recipe.notes') }}
          </h3>
          <p
            v-if="!linkableNotes.length"
            class="m-0 text-sm text-muted-foreground"
          >
            {{ $t('recipe.no-notes-to-link') }}
          </p>
          <label
            v-for="note in linkableNotes"
            :key="note.referenceId"
            class="flex cursor-pointer items-center gap-3 rounded-item px-1 py-1.5 text-[15px] hover:bg-highlight/50"
          >
            <Checkbox
              :model-value="linkNotes.includes(note.referenceId)"
              class="size-5"
              @update:model-value="toggleLink('notes', note.referenceId, !!$event)"
            />
            {{ note.title || $t('recipe.note') }}
          </label>
        </section>
      </div>
      <template #card-actions>
        <div class="flex w-full flex-wrap items-center gap-2">
          <Button
            variant="ghost"
            @click="linkDialog = false"
          >
            {{ $t('general.cancel') }}
          </Button>
          <Button
            variant="outline"
            class="ms-auto"
            @click="autoLink"
          >
            <MdiIcon
              :path="$globals.icons.robot"
              class="size-4"
            />
            {{ $t('recipe.auto') }}
          </Button>
          <Button
            :variant="hasNextStep ? 'outline' : 'default'"
            @click="saveLinks"
          >
            {{ $t('general.save') }}
          </Button>
          <Button
            v-if="hasNextStep"
            @click="saveAndNext"
          >
            {{ $t('recipe.nextStep') }}
            <MdiIcon
              :path="$globals.icons.forward"
              class="size-4"
            />
          </Button>
        </div>
      </template>
    </BaseDialog>
  </div>
</template>
