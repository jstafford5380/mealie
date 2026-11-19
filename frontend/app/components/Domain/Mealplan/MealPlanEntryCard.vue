<script setup lang="ts">
import type { ContextMenuItem } from "~/components/Domain/Recipe/RecipeContextMenu/RecipeContextMenu.vue";
import type { useMealplans } from "~/composables/use-group-mealplan";
import type { PlanEntryOut } from "~/lib/api/types/meal-plan";
import { EllipsisVerticalIcon } from "@lucide/vue";
import RecipeContextMenu from "~/components/Domain/Recipe/RecipeContextMenu/RecipeContextMenu.vue";
import RecipeThumb from "~/components/Domain/Recipe/RecipeThumb.vue";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "~/components/ui/dropdown-menu";
import { MdiIcon } from "~/components/ui/mdi-icon";
import MealPlanScaleControl from "./MealPlanScaleControl.vue";

/**
 * One planned meal. "stacked" is the narrow board cell (photo above the name);
 * "row" is the wider agenda layout, which also shows the servings stepper.
 */
const props = withDefaults(defineProps<{
  meal: PlanEntryOut;
  actions: ReturnType<typeof useMealplans>["actions"];
  layout?: "stacked" | "row";
  /** Shows the meal type, for week entries that aren't grouped by type. */
  showType?: boolean;
}>(), {
  layout: "stacked",
  showType: false,
});
const emit = defineEmits<{ edit: [meal: PlanEntryOut]; randomize: [meal: PlanEntryOut]; cookToday: [meal: PlanEntryOut] }>();

const NuxtLink = resolveComponent("NuxtLink");
const i18n = useI18n();
const { $globals } = useNuxtApp();
const auth = useMealieAuth();
const route = useRoute();
const groupSlug = computed(() => route.params.groupSlug as string || auth.user.value?.groupSlug || "");
const recipeLink = computed(() => {
  const recipe = props.meal.recipe;
  if (!recipe?.slug) {
    return undefined;
  }
  const scale = props.meal.recipeScale ?? 1;
  return `/g/${groupSlug.value}/r/${recipe.slug}${scale !== 1 ? `?scale=${scale}` : ""}`;
});

const planItems = computed<ContextMenuItem[]>(() => [
  { title: i18n.t("meal-plan.edit-meal-plan"), icon: $globals.icons.calendarEdit, event: "mealplanEdit", isPublic: false },
  { title: i18n.t("meal-plan.randomize-recipe"), icon: $globals.icons.diceMultiple, event: "mealplanRandomize", isPublic: false },
  ...(props.meal.endDate ? [{ title: i18n.t("meal-plan.cooking-it-today"), icon: $globals.icons.potSteam, event: "mealplanCookToday", isPublic: false }] : []),
  { title: i18n.t("meal-plan.remove-from-plan"), icon: $globals.icons.calendarRemove, event: "mealplanRemove", isPublic: false },
]);

function run(event: string) {
  switch (event) {
    case "mealplanEdit":
      emit("edit", props.meal);
      break;
    case "mealplanRandomize":
      emit("randomize", props.meal);
      break;
    case "mealplanCookToday":
      emit("cookToday", props.meal);
      break;
    case "mealplanRemove":
      props.actions.deleteOne(props.meal.id);
      break;
  }
}

const typeLabel = computed(() => (props.meal.entryType ? i18n.t(`meal-plan.${props.meal.entryType}`) : ""));
const scale = computed(() => props.meal.recipeScale ?? 1);
</script>

<template>
  <div
    :data-id="meal.id"
    class="group/meal relative rounded-control border bg-background font-sans text-foreground transition-shadow hover:shadow-sm"
    :class="layout === 'stacked' ? 'flex flex-col gap-1.5 p-1.5' : 'flex items-center gap-3 p-2'"
  >
    <component
      :is="recipeLink ? NuxtLink : 'button'"
      :to="recipeLink"
      :type="recipeLink ? undefined : 'button'"
      class="min-w-0 text-left text-inherit no-underline focus-visible:outline-2 focus-visible:outline-ring"
      :class="layout === 'stacked' ? 'flex flex-col gap-1.5' : 'flex min-w-0 flex-1 items-center gap-3'"
      draggable="false"
      @click="!recipeLink && emit('edit', meal)"
    >
      <RecipeThumb
        v-if="meal.recipe"
        :recipe-id="meal.recipe.id"
        :image="meal.recipe.image"
        :size="layout === 'stacked' ? 'small' : 'tiny'"
        :class="layout === 'stacked' ? 'h-14 w-full rounded-item' : 'h-12 w-16 rounded-item'"
      />
      <span
        v-else
        class="flex shrink-0 items-center justify-center rounded-item bg-brand/15 text-brand-strong dark:text-brand"
        :class="layout === 'stacked' ? 'h-8 w-8' : 'h-12 w-16'"
      >
        <MdiIcon
          :path="$globals.icons.textBox"
          class="size-4"
        />
      </span>
      <span class="min-w-0 pe-6">
        <span
          v-if="showType && typeLabel"
          class="block text-[11px] font-semibold text-muted-foreground"
        >{{ typeLabel }}</span>
        <span
          class="block font-semibold leading-snug"
          :class="layout === 'stacked' ? 'line-clamp-2 text-[13.5px]' : 'truncate text-[15px]'"
        >{{ meal.recipe ? meal.recipe.name : meal.title }}</span>
        <span
          v-if="!meal.recipe && meal.text"
          class="block text-xs text-muted-foreground"
          :class="layout === 'stacked' ? 'line-clamp-2' : 'truncate'"
        >{{ meal.text }}</span>
        <span
          v-if="meal.recipe && scale !== 1 && layout === 'stacked'"
          class="mt-0.5 inline-flex rounded-full bg-subtle px-1.5 text-[11px] font-semibold text-subtle-foreground"
        >× {{ scale }}</span>
      </span>
    </component>

    <MealPlanScaleControl
      v-if="meal.recipe && layout === 'row'"
      class="shrink-0 max-sm:display-none"
      :meal="meal"
      :actions="actions"
    />

    <div
      class="absolute end-1 top-1 opacity-0 transition-opacity focus-within:opacity-100 group-hover/meal:opacity-100 [@media(hover:none)]:opacity-100"
      :class="layout === 'row' && 'static opacity-100'"
    >
      <RecipeContextMenu
        v-if="meal.recipe"
        :slug="meal.recipe.slug ?? ''"
        :name="meal.recipe.name ?? ''"
        :recipe-id="meal.recipe.id ?? ''"
        :recipe-scale="scale"
        :menu-top="false"
        :leading-items="planItems"
        :use-items="{ delete: false, edit: false, download: false, downloadPdf: false, duplicate: false, mealplanner: false, shoppingList: true, print: false, printPreferences: false, share: true, recipeActions: true }"
        @mealplan-edit="run('mealplanEdit')"
        @mealplan-remove="run('mealplanRemove')"
        @mealplan-randomize="run('mealplanRandomize')"
        @mealplan-cook-today="run('mealplanCookToday')"
      />
      <DropdownMenu
        v-else
        :modal="false"
      >
        <DropdownMenuTrigger as-child>
          <button
            type="button"
            class="inline-flex size-8 items-center justify-center rounded-full bg-background/80 text-muted-foreground hover:bg-highlight hover:text-foreground"
            :aria-label="$t('general.actions')"
          >
            <EllipsisVerticalIcon class="size-4" />
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent
          align="end"
          class="min-w-52"
        >
          <DropdownMenuItem
            v-for="item in planItems"
            :key="item.event"
            :variant="item.event === 'mealplanRemove' ? 'destructive' : 'default'"
            @select="run(item.event)"
          >
            <MdiIcon
              :path="item.icon"
              class="size-4"
            />
            {{ item.title }}
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  </div>
</template>
