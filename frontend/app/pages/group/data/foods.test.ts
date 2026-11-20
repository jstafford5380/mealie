import { flushPromises, shallowMount } from "@vue/test-utils";
import { defineComponent, ref } from "vue";
import { afterEach, expect, test, vi } from "vitest";
import FoodsPage from "./foods.vue";

const mocks = vi.hoisted(() => ({
  updateOne: vi.fn(),
  refresh: vi.fn(),
}));

vi.mock("~/composables/api", () => ({
  useUserApi: () => ({ foods: { updateOne: mocks.updateOne } }),
}));
vi.mock("~/composables/store", () => ({
  useFoodStore: () => ({ store: ref([]), actions: { refresh: mocks.refresh } }),
  useLabelStore: () => ({ store: ref([]) }),
}));
vi.mock("~/composables/use-locales", () => ({
  useLocales: () => ({ locales: [], locale: ref("en-US") }),
}));
vi.mock("~/components/Domain/ShoppingList/MultiPurposeLabel.vue", () => ({ default: { render: () => null } }));

const GroupDataPage = defineComponent({
  name: "GroupDataPage",
  props: ["editDialog", "editForm"],
  emits: ["update:editDialog", "edit-one"],
  render: () => null,
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.clearAllMocks();
});

test("keeps a failed food edit open and retries the paired write with the same draft", async () => {
  vi.stubGlobal("useMealieAuth", () => ({ user: ref({ householdSlug: "family" }) }));
  mocks.updateOne.mockResolvedValueOnce({ data: null }).mockResolvedValueOnce({ data: { id: "food" } });
  const wrapper = shallowMount(FoodsPage, {
    global: {
      stubs: { GroupDataPage, BaseDialog: true },
      mocks: { $globals: { icons: {} } },
    },
  });

  try {
    const editor = wrapper.getComponent(GroupDataPage);
    editor.props("editForm").data = { id: "food", name: "Edited food", onHand: true };
    editor.vm.$emit("update:editDialog", true);
    wrapper.getComponent({ name: "RecipeDataSubstitutionManagerDialog" }).vm.$emit(
      "submit",
      [{ substituteFoodId: "substitute" }],
      { add: ["substitute"], remove: [] },
    );

    editor.vm.$emit("edit-one");
    await flushPromises();
    expect(editor.props("editDialog")).toBe(true);
    expect(editor.props("editForm").data.name).toBe("Edited food");
    expect(mocks.updateOne).toHaveBeenCalledTimes(1);
    expect(mocks.updateOne).toHaveBeenCalledWith("food", expect.objectContaining({
      householdsWithIngredientFood: ["family"],
      substitutions: [{ substituteFoodId: "substitute" }],
      reverseSubstitutionsAdd: ["substitute"],
      reverseSubstitutionsRemove: [],
    }));

    editor.vm.$emit("edit-one");
    await flushPromises();
    expect(mocks.updateOne.mock.calls[1]).toEqual(mocks.updateOne.mock.calls[0]);
    expect(editor.props("editDialog")).toBe(false);
  }
  finally {
    wrapper.unmount();
  }
});
