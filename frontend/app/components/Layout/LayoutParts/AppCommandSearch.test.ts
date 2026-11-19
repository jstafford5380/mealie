import { mount, type VueWrapper } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { nextTick, reactive, ref } from "vue";
import AppCommandSearch from "./AppCommandSearch.vue";

const routerPush = vi.fn();
const wrappers: VueWrapper[] = [];

const mocks = vi.hoisted(() => ({
  useRecipeSearch: vi.fn(),
}));

vi.mock("~/composables/use-logged-in-state", () => ({
  useLoggedInState: () => ({ isOwnGroup: ref(true), loggedIn: ref(true) }),
}));
vi.mock("~/composables/api", () => ({ useUserApi: () => ({}) }));
vi.mock("~/composables/api/api-client", () => ({ usePublicExploreApi: () => ({ explore: {} }) }));
vi.mock("~/composables/api/static-routes", () => ({ useStaticRoutes: () => ({ recipeTinyImage: () => "img" }) }));
vi.mock("~/composables/recipes/use-recipe-search", () => ({ useRecipeSearch: mocks.useRecipeSearch }));

const recipes = [
  { id: "1", name: "First Recipe", slug: "first-recipe", description: "", rating: 0 },
  { id: "2", name: "Second Recipe", slug: "second-recipe", description: "", rating: 0 },
];

let query = ref("");
let data = ref<typeof recipes>([]);

function input(): HTMLInputElement {
  return document.body.querySelector("input[role=combobox]") as HTMLInputElement;
}
function options() {
  return [...document.body.querySelectorAll("[role=option]")];
}
function selected() {
  return options().filter(option => option.getAttribute("aria-selected") === "true");
}
async function press(key: string, init: KeyboardEventInit = {}) {
  input().dispatchEvent(new KeyboardEvent("keydown", { key, cancelable: true, bubbles: true, ...init }));
  await nextTick();
}

async function mountSearch(props: Record<string, unknown> = {}) {
  const wrapper = mount(AppCommandSearch, {
    props: { open: true, ...props },
    attachTo: document.body,
    global: {
      mocks: {
        $globals: { icons: { primary: "p" } },
      },
    },
  });
  wrappers.push(wrapper);
  await nextTick();
  await nextTick();
  return wrapper;
}

describe("AppCommandSearch", () => {
  beforeEach(() => {
    routerPush.mockClear();
    query = ref("");
    data = ref([...recipes]);
    mocks.useRecipeSearch.mockReturnValue({ query, data, loading: ref(false) });
    vi.stubGlobal("useMealieAuth", () => ({ user: ref({ groupSlug: "family" }) }));
    vi.stubGlobal("useRoute", () => reactive({ params: { groupSlug: "family" }, fullPath: "/g/family" }));
    vi.stubGlobal("useRouter", () => ({ push: routerPush }));
    Element.prototype.scrollIntoView = vi.fn();
  });

  afterEach(() => {
    wrappers.forEach(wrapper => wrapper.unmount());
    wrappers.length = 0;
    document.body.replaceChildren();
    vi.unstubAllGlobals();
  });

  test("ArrowUp and ArrowDown clamp the selected result", async () => {
    await mountSearch();
    query.value = "rec";
    await nextTick();

    await press("ArrowDown");
    expect(selected()).toHaveLength(1);
    expect(selected()[0]?.textContent).toContain("First Recipe");

    await press("ArrowDown");
    await press("ArrowDown");
    expect(selected()[0]?.textContent).toContain("Second Recipe");

    await press("ArrowUp");
    await press("ArrowUp");
    await press("ArrowUp");
    expect(selected()).toHaveLength(0);
  });

  test("Enter opens the selected recipe", async () => {
    await mountSearch();
    query.value = "rec";
    await nextTick();

    await press("ArrowDown");
    await press("ArrowDown");
    await press("Enter");

    expect(routerPush).toHaveBeenCalledWith("/g/family/r/second-recipe");
  });

  test("Enter opens the first recipe when none is selected", async () => {
    await mountSearch();
    query.value = "rec";
    await nextTick();

    await press("Enter");

    expect(routerPush).toHaveBeenCalledWith("/g/family/r/first-recipe");
  });

  test("Enter is ignored while an IME composition is active", async () => {
    await mountSearch();
    query.value = "rec";
    await nextTick();

    await press("Enter", { isComposing: true });

    expect(routerPush).not.toHaveBeenCalled();
  });

  test("keyboard navigation does nothing without results", async () => {
    data.value = [];
    await mountSearch();
    query.value = "nothing";
    await nextTick();

    await press("ArrowDown");
    await press("Enter");

    expect(selected()).toHaveLength(0);
    expect(routerPush).not.toHaveBeenCalled();
  });

  test("an empty query offers navigation commands", async () => {
    await mountSearch({
      sections: [{ key: "s", items: [{ key: "plan", title: "Meal Planner", icon: "i", to: "/household/mealplan/planner/view" }] }],
    });

    expect(options().map(option => option.textContent?.trim())).toEqual(["Meal Planner"]);
    await press("Enter");
    expect(routerPush).toHaveBeenCalledWith("/household/mealplan/planner/view");
  });

  test("closing clears the query and results", async () => {
    const wrapper = await mountSearch();
    query.value = "rec";
    await nextTick();

    await wrapper.setProps({ open: false });

    expect(query.value).toBe("");
    expect(data.value).toEqual([]);
  });

  test("slash opens search outside text fields", async () => {
    const wrapper = await mountSearch({ open: false });
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "/", cancelable: true }));
    await nextTick();
    expect(wrapper.emitted("update:open")?.at(-1)).toEqual([true]);
  });
});
