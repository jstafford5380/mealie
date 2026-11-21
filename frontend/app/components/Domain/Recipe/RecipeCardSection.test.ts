import { flushPromises, mount, type VueWrapper } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { reactive, ref } from "vue";
import RecipeCardSection from "./RecipeCardSection.vue";
import { makeRecipeSummary } from "~/tests/factories";

const mocks = vi.hoisted(() => ({
  preferences: { value: { useMobileCards: false, orderBy: "name", orderDirection: "asc" } },
}));

vi.mock("~/composables/use-logged-in-state", () => ({
  useLoggedInState: () => ({ isOwnGroup: ref(true) }),
}));

vi.mock("~/composables/recipes", () => ({
  useLazyRecipes: () => ({
    fetchMore: vi.fn().mockResolvedValue([]),
    getRandom: vi.fn(),
  }),
}));

vi.mock("~/composables/api", () => ({
  useStaticRoutes: () => ({ recipeSmallImage: () => "img" }),
}));

vi.mock("~/composables/use-users/preferences", () => ({
  useUserSortPreferences: () => mocks.preferences,
}));

const tag = { id: "t0000000-0000-4000-8000-000000000001", name: "Dinner", slug: "dinner", groupId: "g1", recipeCount: 1 };
const recipe = makeRecipeSummary({ id: "1", name: "Soup", slug: "soup", image: "image", tags: [tag] });

const wrappers: VueWrapper[] = [];

async function mountSection(items = [recipe]) {
  const wrapper = mount(RecipeCardSection, {
    props: { recipes: items, disableToolbar: true },
    global: {
      mocks: { $globals: { icons: {} } },
      stubs: {
        NuxtLink: { template: "<a><slot /></a>" },
        RecipeCardRating: true,
        RecipeFavoriteBadge: true,
        RecipeContextMenu: true,
        SafeMarkdown: true,
        AppScrollToTop: true,
      },
    },
  });
  wrappers.push(wrapper);
  await flushPromises();
  return wrapper;
}

describe("RecipeCardSection", () => {
  beforeEach(() => {
    vi.stubGlobal("useMealieAuth", () => ({ user: ref({ groupSlug: "family" }) }));
    vi.stubGlobal("useNuxtApp", () => ({ $globals: { icons: {} } }));
    vi.stubGlobal("useRoute", () => reactive({ path: "/g/family", params: { groupSlug: "family" } }));
    vi.stubGlobal("useRouter", () => ({ push: vi.fn() }));
    vi.stubGlobal("useScrollPosition", () => ({
      savePosition: vi.fn(),
      getSavedPage: vi.fn(() => null),
      restorePosition: vi.fn(),
    }));
  });

  afterEach(() => {
    wrappers.forEach(wrapper => wrapper.unmount());
    wrappers.length = 0;
    vi.unstubAllGlobals();
  });

  test.each([
    ["grid tiles", false],
    ["list rows", true],
  ])("clicking a tag on %s emits itemSelected", async (_, useMobileCards) => {
    mocks.preferences.value.useMobileCards = useMobileCards;
    const wrapper = await mountSection();

    const chip = wrapper.findAll("button").find(button => button.text() === "Dinner")!;
    expect(chip?.exists()).toBe(true);
    await chip.trigger("click");

    expect(wrapper.emitted("itemSelected")).toEqual([[tag, "tags"]]);
  });

  test("shows available nutrition on grid cards", async () => {
    mocks.preferences.value.useMobileCards = false;
    const wrapper = await mountSection([
      { ...recipe, nutrition: { calories: "255 kcal", proteinContent: "23 g", carbohydrateContent: "12", fatContent: "4" } },
      { ...recipe, id: "2", nutrition: { proteinContent: "0", fatContent: "unknown" } },
      { ...recipe, id: "3" },
    ]);
    const images = wrapper.findAll("article").map(card => card.element.firstElementChild!.textContent!.replaceAll("\u00A0", " "));
    expect(images[0]).toContain("255kcal | 23g P | 12g C | 4g F");
    expect(images[1]).toContain("0g P");
    expect(images[1]).not.toContain("|");
    expect(images[2]).not.toMatch(/kcal|g [PCF]/);
  });
});
