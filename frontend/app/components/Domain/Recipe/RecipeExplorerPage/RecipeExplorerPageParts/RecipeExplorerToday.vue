<script setup lang="ts">
import type { PlanEntryOut } from "~/lib/api/types/meal-plan";
import { format } from "date-fns";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { useUserApi, useStaticRoutes } from "~/composables/api";
import { usePlanTypeOptions } from "~/composables/use-group-mealplan";

/** Today's meal-plan entries at the top of the recipe list, for members of their own group. */
const props = defineProps<{ groupSlug: string }>();

const NuxtLink = resolveComponent("NuxtLink");
const api = useUserApi();
const { recipeTinyImage } = useStaticRoutes();
const typeOptions = usePlanTypeOptions();
const typeOrder = typeOptions.map(option => option.value as string);

const entries = ref<PlanEntryOut[] | null>(null);
onMounted(async () => {
  const today = format(new Date(), "yyyy-MM-dd");
  const { data } = await api.mealplans.getAll(1, -1, { start_date: today, end_date: today });
  entries.value = (data?.items ?? [])
    .filter(entry => entry.date === today)
    .sort((a, b) => typeOrder.indexOf(a.entryType) - typeOrder.indexOf(b.entryType));
});

function typeLabel(entry: PlanEntryOut) {
  return typeOptions.find(option => option.value === entry.entryType)?.text ?? entry.entryType;
}
function recipeLink(entry: PlanEntryOut) {
  if (!entry.recipe?.slug) {
    return undefined;
  }
  const scale = entry.recipeScale && entry.recipeScale !== 1 ? `?scale=${entry.recipeScale}` : "";
  return `/g/${props.groupSlug}/r/${entry.recipe.slug}${scale}`;
}
</script>

<template>
  <section
    v-if="entries && entries.length"
    :aria-label="$t('meal-plan.today')"
    class="flex flex-col gap-2"
  >
    <div class="flex items-center gap-2">
      <h2 class="m-0 text-sm font-semibold text-muted-foreground">
        {{ $t("meal-plan.today") }}
      </h2>
      <NuxtLink
        to="/household/mealplan/planner/view"
        class="ms-auto text-sm font-semibold text-primary no-underline hover:underline"
      >
        {{ $t("meal-plan.meal-planner") }}
      </NuxtLink>
    </div>
    <ul class="m-0 flex list-none gap-3 overflow-x-auto p-0 pb-1">
      <li
        v-for="entry in entries"
        :key="entry.id"
        class="w-[280px] shrink-0"
      >
        <component
          :is="recipeLink(entry) ? NuxtLink : 'div'"
          :to="recipeLink(entry)"
          class="flex h-full items-center gap-3 rounded-card border bg-card p-2.5 pe-3 text-foreground no-underline transition-colors"
          :class="recipeLink(entry) && 'hover:border-primary/40 hover:bg-highlight/40'"
        >
          <img
            v-if="entry.recipe?.image && entry.recipe?.id"
            :src="recipeTinyImage(entry.recipe.id, entry.recipe.image)"
            alt=""
            class="size-14 shrink-0 rounded-control bg-muted object-cover"
          >
          <span
            v-else
            class="flex size-14 shrink-0 items-center justify-center rounded-control bg-brand-soft text-brand-strong"
          >
            <MdiIcon
              :path="$globals.icons.calendarMultiselect"
              class="size-6"
            />
          </span>
          <span class="flex min-w-0 flex-col">
            <span class="text-xs font-semibold text-muted-foreground">{{ typeLabel(entry) }}</span>
            <span class="line-clamp-2 font-serif text-[15px] leading-snug">{{ entry.recipe?.name || entry.title }}</span>
          </span>
        </component>
      </li>
    </ul>
  </section>
</template>
