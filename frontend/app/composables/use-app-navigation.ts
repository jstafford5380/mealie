import type { CookBookOut } from "~/lib/api/types/cookbook";
import { useCookbookPreferences } from "~/composables/use-users/preferences";
import { useCookbookStore, usePublicCookbookStore } from "~/composables/store/use-cookbook-store";
import { useGroupSelf } from "~/composables/use-groups";
import { useLoggedInState } from "~/composables/use-logged-in-state";

export interface AppNavItem {
  key: string;
  title: string;
  /** @mdi/js path */
  icon: string;
  to?: string;
  children?: AppNavItem[];
}

export interface AppNavSection {
  key: string;
  title?: string;
  items: AppNavItem[];
}

export interface AppCreateLink {
  key: string;
  title: string;
  subtitle: string;
  icon: string;
  to: string;
}

/** Route group for links: the group in the URL, else the signed-in user's group. */
export function useNavGroupSlug() {
  const auth = useMealieAuth();
  const route = useRoute();
  return computed(() => (route.params.groupSlug as string) || auth.user.value?.groupSlug || "");
}

/**
 * Navigation for the default layout. Public visitors (or members viewing another group)
 * see only that group's recipes, the recipe finder and its cookbooks; planning, shopping,
 * timeline, cookbooks and organizers belong to the user's own group.
 */
export function useAppNavigation() {
  const i18n = useI18n();
  const { $globals } = useNuxtApp();
  const auth = useMealieAuth();
  const { isOwnGroup } = useLoggedInState();
  const { group } = useGroupSelf();
  const groupSlug = useNavGroupSlug();
  const icons = $globals.icons;

  const sections = computed<AppNavSection[]>(() => {
    const slug = groupSlug.value;
    const cook: AppNavItem[] = [
      { key: "recipes", title: i18n.t("general.recipes"), icon: icons.silverwareForkKnife, to: `/g/${slug}` },
      { key: "finder", title: i18n.t("recipe-finder.recipe-finder"), icon: icons.search, to: `/g/${slug}/recipes/finder` },
    ];
    if (!isOwnGroup.value) {
      return [{ key: "cook", items: cook }];
    }
    cook.push(
      { key: "cookbooks", title: i18n.t("cookbook.cookbooks"), icon: icons.book, to: `/g/${slug}/cookbooks` },
      { key: "timeline", title: i18n.t("recipe.timeline"), icon: icons.timelineText, to: `/g/${slug}/recipes/timeline` },
      {
        key: "organizers",
        title: i18n.t("general.organizers"),
        icon: icons.organizers,
        children: [
          { key: "categories", title: i18n.t("sidebar.categories"), icon: icons.categories, to: `/g/${slug}/recipes/categories` },
          { key: "tags", title: i18n.t("sidebar.tags"), icon: icons.tags, to: `/g/${slug}/recipes/tags` },
          { key: "tools", title: i18n.t("tool.tools"), icon: icons.potSteam, to: `/g/${slug}/recipes/tools` },
        ],
      },
    );
    return [
      { key: "cook", title: i18n.t("sidebar.section-cook"), items: cook },
      {
        key: "plan",
        title: i18n.t("sidebar.section-plan"),
        items: [
          { key: "mealplan", title: i18n.t("meal-plan.meal-planner"), icon: icons.calendarMultiselect, to: "/household/mealplan/planner/view" },
          { key: "mealconfigurator", title: i18n.t("meal-plan.configurator"), icon: icons.calendarEdit, to: "/household/mealplan/configurator" },
        ],
      },
      {
        key: "shop",
        title: i18n.t("sidebar.section-shop"),
        items: [{ key: "shopping", title: i18n.t("shopping-list.shopping-lists"), icon: icons.formatListCheck, to: "/shopping-lists" }],
      },
    ];
  });

  // Cookbooks: own household first (by position), then other households grouped by name.
  const cookbookPreferences = useCookbookPreferences();
  const ownCookbookStore = computed(() => (isOwnGroup.value ? useCookbookStore(i18n) : null));
  const publicStores: Record<string, ReturnType<typeof usePublicCookbookStore>> = {};
  function publicStore(slug: string) {
    publicStores[slug] ||= usePublicCookbookStore(slug, i18n);
    return publicStores[slug];
  }
  const cookbooks = computed<CookBookOut[]>(() => {
    if (ownCookbookStore.value) {
      return ownCookbookStore.value.store.value;
    }
    if (groupSlug.value) {
      return unref(publicStore(groupSlug.value).store) as CookBookOut[];
    }
    return [];
  });

  const cookbookItems = computed<AppNavItem[]>(() => {
    if (!cookbooks.value?.length) {
      return [];
    }
    const toItem = (cookbook: CookBookOut): AppNavItem => ({
      key: `cookbook-${cookbook.slug}`,
      title: cookbook.name,
      icon: icons.pages,
      to: `/g/${groupSlug.value}/cookbooks/${cookbook.slug || ""}`,
    });
    const sorted = [...cookbooks.value].sort((a, b) => (a.position || 0) - (b.position || 0));
    const byHousehold = sorted.reduce((acc, cookbook) => {
      (acc[cookbook.household?.name || ""] ||= []).push(cookbook);
      return acc;
    }, {} as Record<string, CookBookOut[]>);

    const own: AppNavItem[] = [];
    const others: AppNavItem[] = [];
    for (const [householdName, list] of Object.entries(byHousehold)) {
      if (!list.length) {
        continue;
      }
      if (list[0]!.householdId === auth.user.value?.householdId) {
        own.push(...list.map(toItem));
      }
      else {
        others.push({ key: `household-${householdName}`, title: householdName, icon: icons.book, children: list.map(toItem) });
      }
    }
    others.sort((a, b) => a.title.localeCompare(b.title));
    if (auth.user.value && cookbookPreferences.value.hideOtherHouseholds) {
      return own;
    }
    return [...own, ...others];
  });

  const createLinks = computed<AppCreateLink[]>(() => {
    if (!isOwnGroup.value) {
      return [];
    }
    const slug = groupSlug.value;
    const links: AppCreateLink[] = [
      { key: "url", title: i18n.t("general.import"), subtitle: i18n.t("new-recipe.import-by-url"), icon: icons.link, to: `/g/${slug}/r/create/url` },
    ];
    if (group.value?.aiProviderSettings?.aiEnabled) {
      links.push({ key: "ai", title: i18n.t("recipe.import-with-ai"), subtitle: i18n.t("recipe.import-with-ai-subtitle"), icon: icons.autoFix, to: `/g/${slug}/r/create/ai` });
    }
    links.push({ key: "new", title: i18n.t("general.create"), subtitle: i18n.t("new-recipe.create-manually"), icon: icons.edit, to: `/g/${slug}/r/create/new` });
    return links;
  });

  return { sections, cookbookItems, createLinks, groupSlug, isOwnGroup };
}

/** Navigation for the admin layout. Route guards remain the authorization boundary. */
export function useAdminNavigation() {
  const i18n = useI18n();
  const { $globals } = useNuxtApp();
  const icons = $globals.icons;
  const sections = computed<AppNavSection[]>(() => [
    {
      key: "admin",
      title: i18n.t("settings.admin-settings"),
      items: [
        { key: "site", title: i18n.t("sidebar.site-settings"), icon: icons.cog, to: "/admin/site-settings" },
        { key: "users", title: i18n.t("user.users"), icon: icons.user, to: "/admin/manage/users" },
        { key: "households", title: i18n.t("household.households"), icon: icons.household, to: "/admin/manage/households" },
        { key: "groups", title: i18n.t("group.groups"), icon: icons.group, to: "/admin/manage/groups" },
        { key: "backups", title: i18n.t("sidebar.backups"), icon: icons.database, to: "/admin/backups" },
      ],
    },
    {
      key: "developer",
      title: i18n.t("sidebar.developer"),
      items: [
        { key: "maintenance", title: i18n.t("sidebar.maintenance"), icon: icons.wrench, to: "/admin/maintenance" },
        {
          key: "debug",
          title: i18n.t("recipe.debug"),
          icon: icons.robot,
          children: [
            { key: "ai-providers", title: i18n.t("admin.ai-providers"), icon: icons.autoFix, to: "/admin/debug/ai-providers" },
            { key: "parser", title: i18n.t("sidebar.parser"), icon: icons.slotMachine, to: "/admin/debug/parser" },
          ],
        },
      ],
    },
  ]);
  return { sections };
}
