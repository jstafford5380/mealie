import { flushPromises, mount, type VueWrapper } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { ref, type Ref } from "vue";
import GroupAIPromptEditor from "./GroupAIPromptEditor.vue";
import type { AIPromptsOut } from "~/lib/api/types/group";

const wrappers: VueWrapper[] = [];

const mocks = vi.hoisted(() => ({
  prompts: null as unknown as Ref<AIPromptsOut | null>,
  refresh: vi.fn(),
  save: vi.fn(),
  reset: vi.fn(),
}));

vi.mock("~/composables/use-ai-providers", () => ({
  useAIPrompts: () => ({
    prompts: mocks.prompts,
    loading: ref(false),
    refresh: mocks.refresh,
    save: mocks.save,
    reset: mocks.reset,
  }),
}));

vi.mock("~/composables/use-toast", () => ({
  alert: { success: vi.fn(), error: vi.fn() },
}));

const PROMPT_NAME = "recipes.build-recipe";
const DEFAULT_CONTENT = "Mealie's built-in prompt";

function promptsOut(overrides: Partial<AIPromptsOut["prompts"][number]> = {}): AIPromptsOut {
  return {
    globalInstructions: null,
    prompts: [{
      name: PROMPT_NAME,
      isSystem: false,
      defaultContent: DEFAULT_CONTENT,
      mode: null,
      content: null,
      defaultChanged: false,
      ...overrides,
    }],
  };
}

async function mountEditor(initial: AIPromptsOut = promptsOut()) {
  mocks.prompts = ref(initial);
  const wrapper = mount(GroupAIPromptEditor, {
    global: {
      mocks: {
        $globals: { icons: { alert: "alert" } },
      },
      stubs: {
        AppLoader: { template: "<div />" },
        Accordion: { template: "<div><slot /></div>" },
        AccordionItem: { template: "<div><slot /></div>" },
        AccordionTrigger: { template: "<div><slot /></div>" },
        AccordionContent: { template: "<div><slot /></div>" },
        MdiIcon: { template: "<span />" },
        Button: {
          props: { disabled: Boolean },
          template: "<button type=\"button\" :disabled=\"disabled\" @click=\"$emit('click')\"><slot /></button>",
        },
      },
    },
  });
  await flushPromises();

  wrappers.push(wrapper);
  return wrapper;
}

function textareas(wrapper: VueWrapper) {
  return wrapper.findAll("textarea").filter(textarea => !textarea.attributes("readonly"));
}

async function selectMode(wrapper: VueWrapper, mode: string) {
  await wrapper.find(`[role="radiogroup"] button[data-value="${mode}"]`).trigger("click");
}

async function savePrompt(wrapper: VueWrapper) {
  await wrapper.find("[data-testid=\"save-prompt\"]").trigger("click");
  await flushPromises();
}

describe("groupAIPromptEditor", () => {
  beforeEach(() => {
    mocks.refresh.mockReset().mockResolvedValue(null);
    mocks.save.mockReset().mockImplementation(async (name: string, payload: { mode: string; content: string }) => {
      mocks.prompts.value = name === "global"
        ? { ...promptsOut(), globalInstructions: payload.content }
        : promptsOut({ mode: payload.mode as "append" | "override", content: payload.content });
      return mocks.prompts.value;
    });
    mocks.reset.mockReset().mockImplementation(async () => {
      mocks.prompts.value = promptsOut();
      return mocks.prompts.value;
    });
    vi.stubGlobal("useNuxtApp", () => ({ $globals: { icons: {} } }));
  });

  afterEach(() => {
    wrappers.forEach(wrapper => wrapper.unmount());
    wrappers.length = 0;
    vi.unstubAllGlobals();
  });

  test("switching to override starts from the built-in prompt", async () => {
    const wrapper = await mountEditor();

    await selectMode(wrapper, "override");
    const editor = textareas(wrapper)[1]!;
    expect((editor.element as HTMLTextAreaElement).value).toBe(DEFAULT_CONTENT);

    await editor.setValue(`${DEFAULT_CONTENT} Use metric units.`);
    await savePrompt(wrapper);

    expect(mocks.save).toHaveBeenCalledWith(PROMPT_NAME, {
      mode: "override",
      content: `${DEFAULT_CONTENT} Use metric units.`,
    });
  });

  test("an existing override isn't replaced by the built-in prompt", async () => {
    const wrapper = await mountEditor(promptsOut({ mode: "override", content: "My prompt" }));

    await selectMode(wrapper, "append");
    await selectMode(wrapper, "override");

    expect((textareas(wrapper)[1]!.element as HTMLTextAreaElement).value).toBe("My prompt");
  });

  test("appending saves only the extra instructions", async () => {
    const wrapper = await mountEditor();

    await selectMode(wrapper, "append");
    await textareas(wrapper)[1]!.setValue("Use metric units.");
    await savePrompt(wrapper);

    expect(mocks.save).toHaveBeenCalledWith(PROMPT_NAME, { mode: "append", content: "Use metric units." });
  });

  test("switching back to default resets the prompt", async () => {
    const wrapper = await mountEditor(promptsOut({ mode: "append", content: "Use metric units." }));

    await selectMode(wrapper, "default");
    await savePrompt(wrapper);

    expect(mocks.reset).toHaveBeenCalledWith(PROMPT_NAME);
    expect(mocks.save).not.toHaveBeenCalled();
  });

  test("a failed save keeps the unsaved edit", async () => {
    mocks.save.mockResolvedValue(null);
    const wrapper = await mountEditor();

    await selectMode(wrapper, "append");
    await textareas(wrapper)[1]!.setValue("Use metric units.");
    await savePrompt(wrapper);

    expect((textareas(wrapper)[1]!.element as HTMLTextAreaElement).value).toBe("Use metric units.");
  });

  test("global instructions are appended, and cleared by saving them empty", async () => {
    const wrapper = await mountEditor();
    const saveGlobal = () => wrapper.find("[data-testid=\"save-global\"]").trigger("click");

    await textareas(wrapper)[0]!.setValue("  Use metric units.  ");
    await saveGlobal();
    await flushPromises();
    expect(mocks.save).toHaveBeenCalledWith("global", { mode: "append", content: "Use metric units." });

    await textareas(wrapper)[0]!.setValue("");
    await saveGlobal();
    await flushPromises();
    expect(mocks.reset).toHaveBeenCalledWith("global");
  });
});
