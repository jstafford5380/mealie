<script setup lang="ts">
import type { AppNavItem } from "~/composables/use-app-navigation";
import { ChevronRightIcon } from "@lucide/vue";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "~/components/ui/collapsible";
import { MdiIcon } from "~/components/ui/mdi-icon";

const props = defineProps<{
  items: AppNavItem[];
  nested?: boolean;
}>();

const route = useRoute();

/** A link is current on its own path and on pages beneath it; the recipe list owns recipe pages. */
function isActive(item: AppNavItem): boolean {
  if (!item.to) {
    return false;
  }
  const path = route.path.replace(/\/$/, "");
  const to = item.to.replace(/\/$/, "");
  if (path === to) {
    return true;
  }
  if (/^\/g\/[^/]+$/.test(to)) {
    return path.startsWith(`${to}/r/`);
  }
  if (to === "/household/mealplan/planner/view") {
    const planner = "/household/mealplan/planner";
    return path === planner || path.startsWith(`${planner}/`) || path === "/household/mealplan/settings";
  }
  return path.startsWith(`${to}/`);
}

function hasActiveChild(item: AppNavItem): boolean {
  return !!item.children?.some(child => isActive(child) || hasActiveChild(child));
}

const open = reactive<Record<string, boolean>>({});
watchEffect(() => {
  for (const item of props.items) {
    if (item.children && hasActiveChild(item) && open[item.key] === undefined) {
      open[item.key] = true;
    }
  }
});

const linkClass = "group/nav flex no-underline h-10 w-full items-center gap-3 rounded-item px-2.5 text-[14.5px] font-medium text-sidebar-foreground transition-colors hover:bg-sidebar-highlight/70 hover:text-sidebar-highlight-foreground focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-sidebar-ring aria-[current=page]:bg-sidebar-highlight aria-[current=page]:font-semibold aria-[current=page]:text-sidebar-highlight-foreground";
</script>

<template>
  <ul
    class="m-0 flex list-none flex-col gap-0.5 p-0"
    :class="nested && 'ms-[18px] border-s border-sidebar-border ps-2'"
  >
    <li
      v-for="item in items"
      :key="item.key"
    >
      <Collapsible
        v-if="item.children"
        v-model:open="open[item.key]"
      >
        <CollapsibleTrigger :class="linkClass">
          <MdiIcon
            :path="item.icon"
            class="size-[19px] opacity-80"
          />
          <span class="min-w-0 flex-1 truncate text-start">{{ item.title }}</span>
          <ChevronRightIcon
            class="size-4 opacity-60 transition-transform duration-150 rtl:rotate-180"
            :class="open[item.key] && 'rotate-90 rtl:rotate-90'"
          />
        </CollapsibleTrigger>
        <CollapsibleContent class="pt-0.5">
          <AppShellNavList
            :items="item.children"
            nested
          />
        </CollapsibleContent>
      </Collapsible>
      <NuxtLink
        v-else
        :to="item.to"
        :class="linkClass"
        :aria-current="isActive(item) ? 'page' : undefined"
      >
        <MdiIcon
          :path="item.icon"
          class="size-[19px] opacity-80 group-aria-[current=page]/nav:opacity-100"
        />
        <span class="min-w-0 flex-1 truncate">{{ item.title }}</span>
      </NuxtLink>
    </li>
  </ul>
</template>
