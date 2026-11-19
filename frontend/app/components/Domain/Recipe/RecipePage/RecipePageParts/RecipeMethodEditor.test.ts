import type { RecipeOut, RecipeStep } from "~/lib/api/types/recipe";
import { mount } from "@vue/test-utils";
import { describe, expect, test, vi } from "vitest";
import { nextTick } from "vue";
import messages from "~/lang/messages/en-US.json";
import RecipeMethodEditor from "./RecipeMethodEditor.vue";

const t = messages as any;

vi.mock("~/composables/api", () => ({
  useUserApi: () => ({ recipes: {} }),
  useStaticRoutes: () => ({ recipeAssetPath: () => "" }),
}));
vi.mock("~/composables/recipe-page/use-extract-ingredient-references", () => ({
  useExtractIngredientReferences: () => ({ extractIngredientReferences: () => new Set(["salt"]) }),
}));

function makeRecipe(steps: RecipeStep[]): RecipeOut {
  return {
    id: "r1",
    slug: "r1",
    recipeIngredient: [{ referenceId: "salt", note: "Salt" }, { referenceId: "oil", note: "Oil" }],
    notes: [{ referenceId: "n1", title: "Tip", text: "" }],
    recipeInstructions: steps,
  } as unknown as RecipeOut;
}

function mountEditor(steps: RecipeStep[]) {
  const recipe = makeRecipe(steps);
  const wrapper = mount(RecipeMethodEditor, {
    props: {
      "modelValue": steps,
      "onUpdate:modelValue": (v: RecipeStep[]) => wrapper.setProps({ modelValue: v }),
      recipe,
    },
    global: {
      mocks: { $globals: { icons: new Proxy({}, { get: (_, key) => String(key) }) } },
      stubs: {
        MdiIcon: true,
        BaseDialog: { props: ["modelValue"], template: "<div v-if=\"modelValue\" class=\"dialog\"><slot /><slot name=\"card-actions\" /></div>" },
        MarkdownEditor: true,
        DropZone: { template: "<div><slot /></div>" },
        RecipeIngredientHtml: { props: ["ingredient"], template: "<span>{{ ingredient.note }}</span>" },
        RecipeDialogBulkAdd: true,
        CookTime: true,
        VueDraggable: { props: ["modelValue"], template: "<div><slot /></div>" },
        DropdownMenu: { template: "<div><slot /></div>" },
        DropdownMenuTrigger: { template: "<div><slot /></div>" },
        DropdownMenuContent: { template: "<div class=\"menu\"><slot /></div>" },
        DropdownMenuItem: { emits: ["select"], template: "<button class=\"menu-item\" @click=\"$emit('select')\"><slot /></button>" },
        DropdownMenuSeparator: true,
      },
    },
  });
  return wrapper;
}

const step = (id: string, text: string, extra: Partial<RecipeStep> = {}): RecipeStep =>
  ({ id, text, title: "", summary: "", ingredientReferences: [], noteReferences: [], durationSeconds: null, ...extra });

function menuButton(wrapper: ReturnType<typeof mountEditor>, stepIndex: number, label: string) {
  const menus = wrapper.findAll(".menu");
  return menus[stepIndex]!.findAll(".menu-item").find(b => b.text() === label)!;
}

describe("RecipeMethodEditor", () => {
  test("adds a blank step", async () => {
    const steps = [step("a", "One")];
    const wrapper = mountEditor(steps);
    await wrapper.findAll("button").find(b => b.text() === t.recipe["add-step"])!.trigger("click");
    expect(steps).toHaveLength(2);
    expect(steps[1]!.text).toBe("");
    expect(steps[1]!.id).toBeTruthy();
  });

  test("adding a section shows a title box and clearing it drops the title", async () => {
    const steps = [step("a", "One")];
    const wrapper = mountEditor(steps);
    expect(wrapper.find(`input[placeholder='${t.recipe["section-title"]}']`).exists()).toBe(false);
    await menuButton(wrapper, 0, t.recipe["add-section"]).trigger("click");
    const title = wrapper.find(`input[placeholder='${t.recipe["section-title"]}']`);
    expect(title.exists()).toBe(true);
    await title.setValue("Prep");
    expect(steps[0]!.title).toBe("Prep");
    await menuButton(wrapper, 0, t.recipe["clear-section"]).trigger("click");
    expect(steps[0]!.title).toBe("");
    expect(wrapper.find(`input[placeholder='${t.recipe["section-title"]}']`).exists()).toBe(false);
  });

  test("merges a step into the one above and Ctrl+Z undoes it", async () => {
    const steps = [step("a", "One"), step("b", "Two")];
    const wrapper = mountEditor(steps);
    await menuButton(wrapper, 1, t.recipe["merge-above"]).trigger("click");
    expect(steps).toHaveLength(1);
    await wrapper.trigger("keydown", { key: "z", code: "KeyZ", ctrlKey: true });
    expect(steps.map(s => s.text)).toEqual(["One", "Two"]);
  });

  test("links ingredients and notes, including auto matches", async () => {
    const steps = [step("a", "Add salt"), step("b", "Fry")];
    const wrapper = mountEditor(steps);
    await menuButton(wrapper, 0, t.recipe["link-references"]).trigger("click");
    await nextTick();
    const dialog = wrapper.find(".dialog");
    expect(dialog.exists()).toBe(true);
    await dialog.findAll("button").find(b => b.text().includes(t.recipe.auto))!.trigger("click");
    const boxes = dialog.findAll("[role='checkbox']");
    // Salt (auto), Oil, then the note
    await boxes[2]!.trigger("click");
    await dialog.findAll("button").find(b => b.text() === t.general.save)!.trigger("click");
    expect(steps[0]!.ingredientReferences).toEqual([{ referenceId: "salt" }]);
    expect(steps[0]!.noteReferences).toEqual([{ referenceId: "n1" }]);
  });
});
