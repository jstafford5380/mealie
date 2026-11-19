<template>
  <div class="flex flex-col gap-6 font-sans">
    <header>
      <h2 class="m-0 text-xl font-bold tracking-tight">
        {{ $t('group.ai-prompts.ai-prompts') }}
      </h2>
      <p class="m-0 mt-1 max-w-[65ch] text-[15px] text-muted-foreground">
        {{ $t("group.ai-prompts.ai-prompts-description") }}
      </p>
    </header>

    <AppLoader v-if="!prompts" />
    <template v-else>
      <section class="flex flex-col gap-2">
        <h3 class="m-0 text-base font-semibold">
          {{ $t('group.ai-prompts.global-instructions') }}
        </h3>
        <p class="m-0 text-sm text-muted-foreground">
          {{ $t("group.ai-prompts.global-instructions-description") }}
        </p>
        <textarea
          v-model="globalDraft"
          rows="3"
          :aria-label="$t('group.ai-prompts.global-instructions')"
          :placeholder="$t('group.ai-prompts.global-instructions-placeholder')"
          class="w-full resize-y rounded-control border border-input bg-card px-3 py-2 font-mono text-[13.5px] leading-relaxed outline-none focus:border-ring focus:ring-3 focus:ring-ring/25 font-sans text-[15px]"
        />
        <Button
          data-testid="save-global"
          class="self-end"
          :disabled="globalDraft.trim() === (prompts.globalInstructions ?? '') || loading"
          @click="saveGlobal"
        >
          {{ $t('general.save') }}
        </Button>
      </section>

      <section class="flex flex-col gap-2">
        <h3 class="m-0 text-base font-semibold">
          {{ $t('group.ai-prompts.prompts') }}
        </h3>
        <Accordion
          type="single"
          collapsible
          class="rounded-card border bg-card"
        >
          <AccordionItem
            v-for="prompt in prompts.prompts"
            :key="prompt.name"
            :value="prompt.name"
            class="px-4 last:border-b-0"
          >
            <AccordionTrigger class="py-3.5">
              <span class="flex flex-wrap items-center gap-2">
                <span>{{ promptTitle(prompt.name) }}</span>
                <span
                  v-if="prompt.isSystem"
                  class="rounded-full bg-muted px-2 py-0.5 text-xs font-semibold text-muted-foreground"
                >{{ $t("group.ai-prompts.system") }}</span>
                <span
                  v-if="prompt.mode"
                  class="rounded-full bg-primary/15 px-2 py-0.5 text-xs font-semibold text-primary"
                >{{ prompt.mode === "override" ? $t("group.ai-prompts.overridden") : $t("group.ai-prompts.appended") }}</span>
                <MdiIcon
                  v-if="prompt.defaultChanged"
                  :path="$globals.icons.alert"
                  class="size-4 text-brand-strong"
                  :aria-label="$t('group.ai-prompts.default-changed')"
                />
              </span>
            </AccordionTrigger>
            <AccordionContent v-if="drafts[prompt.name]">
              <div class="flex flex-col gap-3 pb-2">
                <p class="m-0 text-[15px]">
                  {{ promptDescription(prompt.name) }}
                </p>
                <p
                  v-if="prompt.isSystem"
                  class="m-0 rounded-control border border-brand/50 bg-brand/10 px-3 py-2 text-sm"
                >
                  {{ $t("group.ai-prompts.system-description") }}
                </p>
                <p
                  v-if="prompt.defaultChanged"
                  class="m-0 rounded-control border border-brand/50 bg-brand/10 px-3 py-2 text-sm"
                >
                  {{ $t("group.ai-prompts.default-changed") }}
                </p>

                <div
                  role="radiogroup"
                  :aria-label="promptTitle(prompt.name)"
                  class="inline-flex w-fit rounded-control border bg-muted/50 p-0.5"
                >
                  <button
                    v-for="mode in MODES"
                    :key="mode.value"
                    type="button"
                    role="radio"
                    :data-value="mode.value"
                    :aria-checked="drafts[prompt.name]!.mode === mode.value"
                    class="h-8 rounded-item px-3 text-sm font-semibold transition-colors"
                    :class="drafts[prompt.name]!.mode === mode.value ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'"
                    @click="setMode(prompt, mode.value)"
                  >
                    {{ $t(mode.label) }}
                  </button>
                </div>

                <template v-if="drafts[prompt.name]!.mode === 'append'">
                  <p class="m-0 text-sm text-muted-foreground">
                    {{ $t("group.ai-prompts.append-description") }}
                  </p>
                  <textarea
                    v-model="drafts[prompt.name]!.append"
                    rows="4"
                    :aria-label="$t('group.ai-prompts.mode-append')"
                    class="w-full resize-y rounded-control border border-input bg-card px-3 py-2 font-mono text-[13.5px] leading-relaxed outline-none focus:border-ring focus:ring-3 focus:ring-ring/25"
                  />
                </template>
                <template v-else-if="drafts[prompt.name]!.mode === 'override'">
                  <p class="m-0 text-sm text-muted-foreground">
                    {{ $t("group.ai-prompts.override-description") }}
                  </p>
                  <textarea
                    v-model="drafts[prompt.name]!.override"
                    rows="10"
                    :aria-label="$t('group.ai-prompts.mode-override')"
                    class="w-full resize-y rounded-control border border-input bg-card px-3 py-2 font-mono text-[13.5px] leading-relaxed outline-none focus:border-ring focus:ring-3 focus:ring-ring/25"
                  />
                </template>

                <div class="flex flex-wrap items-center gap-2">
                  <Button
                    variant="ghost"
                    @click="drafts[prompt.name]!.showDefault = !drafts[prompt.name]!.showDefault"
                  >
                    <MdiIcon
                      :path="drafts[prompt.name]!.showDefault ? $globals.icons.eyeOff : $globals.icons.eye"
                      class="size-4"
                    />
                    {{ drafts[prompt.name]!.showDefault
                      ? $t('group.ai-prompts.hide-default-prompt')
                      : $t('group.ai-prompts.view-default-prompt') }}
                  </Button>
                  <Button
                    data-testid="save-prompt"
                    class="ms-auto"
                    :disabled="!isDirty(prompt) || loading"
                    @click="savePrompt(prompt)"
                  >
                    {{ $t('general.save') }}
                  </Button>
                </div>

                <textarea
                  v-if="drafts[prompt.name]!.showDefault"
                  :value="prompt.defaultContent"
                  readonly
                  rows="10"
                  :aria-label="$t('group.ai-prompts.default-prompt')"
                  class="w-full resize-y rounded-control border border-input bg-card px-3 py-2 font-mono text-[13.5px] leading-relaxed outline-none focus:border-ring focus:ring-3 focus:ring-ring/25 bg-muted"
                />
              </div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "~/components/ui/accordion";
import { Button } from "~/components/ui/button";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { useAIPrompts } from "~/composables/use-ai-providers";
import { alert } from "~/composables/use-toast";
import type { AIPromptOut } from "~/lib/api/types/group";

const GLOBAL_PROMPT_NAME = "global";

type DraftMode = "default" | "append" | "override";

interface Draft {
  mode: DraftMode;
  append: string;
  override: string;
  showDefault: boolean;
}

const props = defineProps<{
  /** Set when an admin is managing another group's prompts */
  groupId?: string;
}>();

const i18n = useI18n();
const { prompts, loading, refresh, save, reset } = useAIPrompts(
  props.groupId === undefined ? undefined : () => props.groupId,
);

const MODES: { value: DraftMode; label: string }[] = [
  { value: "default", label: "group.ai-prompts.mode-default" },
  { value: "append", label: "group.ai-prompts.mode-append" },
  { value: "override", label: "group.ai-prompts.mode-override" },
];

const globalDraft = ref("");
const drafts = reactive<Record<string, Draft>>({});

function syncDraft(prompt: AIPromptOut) {
  drafts[prompt.name] = {
    mode: prompt.mode ?? "default",
    append: prompt.mode === "append" ? prompt.content ?? "" : "",
    override: prompt.mode === "override" ? prompt.content ?? "" : "",
    showDefault: drafts[prompt.name]?.showDefault ?? false,
  };
}

// Only the prompt that was saved is synced, so unsaved edits to the others aren't lost
function syncFromServer(name?: string) {
  if (!prompts.value) {
    return;
  }

  if (!name || name === GLOBAL_PROMPT_NAME) {
    globalDraft.value = prompts.value.globalInstructions ?? "";
  }

  for (const prompt of prompts.value.prompts) {
    if (!name || prompt.name === name) {
      syncDraft(prompt);
    }
  }
}

watch(() => props.groupId, async () => {
  await refresh();
  syncFromServer();
}, { immediate: true });

function promptKey(name: string) {
  return name.replaceAll(".", "-");
}

function promptTitle(name: string) {
  const key = `group.ai-prompts.prompt-titles.${promptKey(name)}`;
  return i18n.te(key) ? i18n.t(key) : name;
}

function promptDescription(name: string) {
  const key = `group.ai-prompts.prompt-descriptions.${promptKey(name)}`;
  return i18n.te(key) ? i18n.t(key) : "";
}

function setMode(prompt: AIPromptOut, mode: DraftMode) {
  const draft = drafts[prompt.name]!;
  draft.mode = mode;

  // An override starts from the built-in prompt, so it can be edited rather than rewritten
  if (mode === "override" && !draft.override.trim()) {
    draft.override = prompt.defaultContent;
  }
}

function draftContent(draft: Draft) {
  return draft.mode === "override" ? draft.override : draft.append;
}

function isDirty(prompt: AIPromptOut) {
  const draft = drafts[prompt.name]!;
  if (draft.mode === "default") {
    return !!prompt.mode;
  }

  const content = draftContent(draft);
  return !!content.trim() && (draft.mode !== prompt.mode || content !== prompt.content);
}

function notify(data: unknown) {
  if (data) {
    alert.success(i18n.t("group.ai-prompts.prompt-saved"));
  }
  else {
    alert.error(i18n.t("group.ai-prompts.prompt-save-failed"));
  }
}

async function savePrompt(prompt: AIPromptOut) {
  const draft = drafts[prompt.name]!;
  const data = draft.mode === "default"
    ? await reset(prompt.name)
    : await save(prompt.name, { mode: draft.mode, content: draftContent(draft) });

  notify(data);
  if (data) {
    syncFromServer(prompt.name);
  }
}

async function saveGlobal() {
  const content = globalDraft.value.trim();
  const data = content
    ? await save(GLOBAL_PROMPT_NAME, { mode: "append", content })
    : await reset(GLOBAL_PROMPT_NAME);

  notify(data);
  if (data) {
    syncFromServer(GLOBAL_PROMPT_NAME);
  }
}
</script>
