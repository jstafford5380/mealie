<template>
  <div
    v-if="shoppingList"
    class="mx-auto w-full max-w-[760px] px-4 pb-48 pt-3 font-sans sm:px-6 md:pb-16 lg:pt-8"
  >
    <BaseDialog
      v-model="state.checkAllDialog"
      :title="$t('general.confirm')"
      :icon="$globals.icons.checkboxMultipleMarkedOutline"
      can-confirm
      @confirm="checkAll"
    >
      <p class="m-0 px-6 pb-2 text-[15px]">
        {{ $t('shopping-list.are-you-sure-you-want-to-check-all-items') }}
      </p>
    </BaseDialog>
    <BaseDialog
      v-model="state.uncheckAllDialog"
      :title="$t('general.confirm')"
      :icon="$globals.icons.checkboxMultipleBlankOutline"
      can-confirm
      @confirm="uncheckAll"
    >
      <p class="m-0 px-6 pb-2 text-[15px]">
        {{ $t('shopping-list.are-you-sure-you-want-to-uncheck-all-items') }}
      </p>
    </BaseDialog>
    <BaseDialog
      v-model="state.deleteCheckedDialog"
      :title="$t('general.confirm')"
      color="error"
      :icon="$globals.icons.alertCircle"
      can-confirm
      @confirm="deleteChecked"
    >
      <p class="m-0 px-6 pb-2 text-[15px]">
        {{ $t('shopping-list.are-you-sure-you-want-to-delete-checked-items') }}
      </p>
    </BaseDialog>

    <!-- Reorder Labels -->
    <BaseDialog
      v-model="reorderLabelsDialog"
      :icon="$globals.icons.tagArrowUp"
      :title="$t('shopping-list.reorder-labels')"
      :submit-text="$t('general.save')"
      can-submit
      @submit="saveLabelOrder"
      @close="cancelLabelOrder"
    >
      <div class="max-h-[60vh] overflow-y-auto px-4 pb-2">
        <VueDraggable
          v-if="localLabels"
          v-model="localLabels"
          handle=".handle"
          :delay="250"
          :delay-on-touch-only="true"
          class="flex flex-col gap-1"
          @update:model-value="updateLabelOrder"
        >
          <MultiPurposeLabelSection
            v-for="(labelSetting, index) in localLabels"
            :key="labelSetting.id"
            v-model="localLabels[index]!"
            use-color
          />
        </VueDraggable>
      </div>
    </BaseDialog>

    <!-- header -->
    <header class="mb-4 flex items-center gap-1">
      <NuxtLink
        to="/shopping-lists?disableRedirect=true"
        class="-ms-2 inline-flex size-11 shrink-0 items-center justify-center rounded-full text-foreground hover:bg-highlight"
        :aria-label="$t('shopping-list.all-lists')"
        :title="$t('shopping-list.all-lists')"
      >
        <ChevronLeftIcon class="size-6" />
      </NuxtLink>
      <div class="min-w-0 flex-1">
        <h1 class="m-0 truncate text-[22px] font-bold tracking-tight sm:text-[28px]">
          {{ shoppingList.name }}
        </h1>
        <p class="m-0 text-[13.5px] text-muted-foreground">
          {{ $t('shopping-list.items-left', listItems.unchecked.length) }}
        </p>
      </div>
      <!-- The search toggle stays while the field is open, so a list that shrinks to the
           threshold mid-search can still close it. -->
      <button
        v-if="canSearch || isSearchOpen"
        type="button"
        class="inline-flex size-11 items-center justify-center rounded-full hover:bg-highlight"
        :class="isSearchOpen ? 'bg-highlight text-primary' : 'text-muted-foreground'"
        :aria-label="$t('search.search')"
        :aria-pressed="isSearchOpen"
        @click="toggleSearch"
      >
        <SearchIcon class="size-5" />
      </button>
      <DropdownMenu :modal="false">
        <DropdownMenuTrigger as-child>
          <button
            type="button"
            class="inline-flex size-11 items-center justify-center rounded-full text-muted-foreground hover:bg-highlight hover:text-foreground"
            :aria-label="$t('shopping-list.list-actions')"
          >
            <EllipsisIcon class="size-5" />
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent
          align="end"
          class="min-w-56"
        >
          <!-- "Check all" would also check items the search is hiding, so it waits for the search to close -->
          <DropdownMenuItem
            :disabled="isSearching"
            @select="openCheckAll"
          >
            <MdiIcon
              :path="$globals.icons.checkboxMultipleMarkedOutline"
              class="size-4"
            />
            {{ $t('shopping-list.check-all-items') }}
          </DropdownMenuItem>
          <DropdownMenuItem @select="copyListItems('plain')">
            <MdiIcon
              :path="$globals.icons.contentCopy"
              class="size-4"
            />
            {{ $t('shopping-list.copy-as-text') }}
          </DropdownMenuItem>
          <DropdownMenuItem @select="copyListItems('markdown')">
            <MdiIcon
              :path="$globals.icons.contentCopy"
              class="size-4"
            />
            {{ $t('shopping-list.copy-as-markdown') }}
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem @select="toggleReorderLabelsDialog()">
            <MdiIcon
              :path="$globals.icons.tagArrowUp"
              class="size-4"
            />
            {{ $t('shopping-list.reorder-labels') }}
          </DropdownMenuItem>
          <DropdownMenuItem @select="$router.push(`/group/data/labels`)">
            <MdiIcon
              :path="$globals.icons.tags"
              class="size-4"
            />
            {{ $t('shopping-list.manage-labels') }}
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </header>

    <BannerWarning
      v-if="isOffline"
      class="mb-4"
      :title="$t('shopping-list.you-are-offline')"
      :description="$t('shopping-list.you-are-offline-description')"
    />

    <div
      v-if="hasConflictedWrites"
      role="alert"
      class="mb-4 flex flex-wrap items-center gap-3 rounded-card border border-destructive/30 bg-card p-3"
    >
      <p class="m-0 flex-1 text-sm">
        {{ $t('shopping-list.merge-conflict') }}
      </p>
      <Button
        variant="outline"
        :disabled="isOffline"
        @click="discardConflictedChanges"
      >
        {{ $t('shopping-list.discard-conflicting-changes') }}
      </Button>
    </div>

    <section
      v-if="!edit"
      class="flex flex-col gap-5"
    >
      <!-- search, toggled from the header -->
      <label
        v-if="isSearchOpen"
        class="flex h-11 items-center gap-2 rounded-control border border-input bg-card px-3 focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/25"
      >
        <SearchIcon class="size-4 shrink-0 text-muted-foreground" />
        <input
          :value="search"
          type="search"
          autofocus
          :aria-label="$t('search.search')"
          :placeholder="$t('search.search')"
          class="h-full min-w-0 flex-1 bg-transparent text-[15px] outline-none"
          @input="search = ($event.target as HTMLInputElement).value"
          @keydown.escape="clearSearch"
        >
      </label>

      <!-- add an item: inline on wider screens, docked above the tab bar on phones -->
      <ShoppingListAddItemForm
        v-if="isPhone"
        v-model="createListItemData"
        :labels="allLabels || []"
        :units="allUnits || []"
        :foods="allFoods || []"
        @save="createListItem"
      />
      <ShoppingListQuickAdd
        v-else
        v-model="createListItemData"
        :foods="allFoods || []"
        :labels="allLabels || []"
        :units="allUnits || []"
        @save="createListItem"
      />

      <p
        v-if="!listItems.unchecked.length && !listItems.checked.length"
        class="m-0 rounded-card border border-dashed px-4 py-8 text-center text-sm text-muted-foreground"
      >
        {{ $t('shopping-list.list-is-empty') }}
      </p>

      <!-- items by label -->
      <template
        v-for="(value, key) in itemsByLabel"
        :key="key"
      >
        <section
          v-if="hasMatches(value)"
          class="flex flex-col"
        >
          <button
            type="button"
            class="mb-1.5 flex items-center gap-2 px-1 text-left text-sm font-semibold text-muted-foreground hover:text-foreground"
            :aria-expanded="!collapsed[key]"
            @click="collapsed[key] = !collapsed[key]"
          >
            <span
              class="size-2.5 shrink-0 rounded-full"
              :class="!getLabelColor(key) && 'bg-muted-foreground/40'"
              :style="getLabelColor(key) ? { backgroundColor: getLabelColor(key) } : undefined"
              aria-hidden="true"
            />
            <span class="flex-1">{{ key }}</span>
            <ChevronDownIcon
              class="size-4 transition-transform"
              :class="collapsed[key] && '-rotate-90'"
            />
          </button>
          <div
            v-show="!collapsed[key]"
            class="overflow-hidden rounded-card border bg-card"
          >
            <VueDraggable
              :model-value="value"
              handle=".handle"
              :delay="250"
              :delay-on-touch-only="true"
              :disabled="isSearching"
              class="divide-y divide-border/70"
              @start="loadingCounter += 1"
              @end="loadingCounter -= 1"
              @update:model-value="updateIndexUncheckedByLabel(key.toString(), $event)"
            >
              <template
                v-for="(item, index) in value"
                :key="item.id"
              >
                <ShoppingListItem
                  v-if="matchesSearch(item)"
                  v-model="value[index]"
                  :edit="editingItem === item.id"
                  :labels="allLabels || []"
                  :units="allUnits || []"
                  :foods="allFoods || []"
                  :recipes="recipeMap"
                  @checked="(item) => {
                    saveListItem(item);
                    itemCheckedToast(item);
                  }"
                  @save="(item) => {
                    editingItem = undefined;
                    saveListItem(item);
                  }"
                  @delete="deleteListItem(item)"
                  @view="editingItem = undefined"
                  @edit="editingItem = item.id"
                />
              </template>
            </VueDraggable>
          </div>
        </section>
      </template>

      <!-- checked items -->
      <section
        v-if="listItems.checked && hasMatches(listItems.checked)"
        class="flex flex-col"
      >
        <div class="mb-1.5 flex flex-wrap items-center gap-2 px-1">
          <button
            type="button"
            class="flex flex-1 items-center gap-2 text-left text-sm font-semibold text-muted-foreground hover:text-foreground"
            :aria-expanded="checkedOpen"
            @click="checkedOpen = !checkedOpen"
          >
            {{ $t('shopping-list.items-checked-count', visibleCheckedCount) }}
            <ChevronDownIcon
              class="size-4 transition-transform"
              :class="!checkedOpen && '-rotate-90'"
            />
          </button>
          <!-- both act on every checked item, including any the search is hiding -->
          <Button
            variant="ghost"
            size="sm"
            :disabled="isSearching"
            @click="openUncheckAll"
          >
            {{ $t('shopping-list.uncheck-all-items') }}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            class="text-destructive hover:text-destructive"
            :disabled="isSearching"
            @click="openDeleteChecked"
          >
            {{ $t('shopping-list.delete-checked') }}
          </Button>
        </div>
        <div
          v-show="checkedOpen"
          class="divide-y divide-border/70 overflow-hidden rounded-card border bg-card/60"
        >
          <template
            v-for="(item, idx) in listItems.checked"
            :key="item.id"
          >
            <ShoppingListItem
              v-show="matchesSearch(item)"
              v-model="listItems.checked[idx]!"
              :labels="allLabels || []"
              :units="allUnits || []"
              :foods="allFoods || []"
              @checked="saveListItem"
              @save="saveListItem"
              @delete="deleteListItem(item)"
            />
          </template>
        </div>
      </section>

      <p
        v-if="!hasSearchResults"
        class="m-0 rounded-card bg-muted px-4 py-3 text-sm text-muted-foreground"
      >
        {{ $t('search.no-results') }}
      </p>
    </section>

    <!-- Recipe References -->
    <section
      v-if="shoppingList.recipeReferences && shoppingList.recipeReferences.length > 0"
      class="mt-10"
    >
      <h2 class="m-0 mb-3 flex items-center gap-2 text-base font-semibold">
        <MdiIcon
          :path="$globals.icons.silverwareForkKnife"
          class="size-4"
        />
        {{ $t('shopping-list.linked-recipes-count', shoppingList.recipeReferences ? shoppingList.recipeReferences.length : 0) }}
      </h2>
      <RecipeList
        :recipes="recipeList"
        show-description
        :disabled="isOffline"
      >
        <template
          v-for="(recipe, index) in recipeList"
          #[`actions-${recipe.id}`]
          :key="'item-actions-decrease' + recipe.id"
        >
          <div
            class="flex items-center gap-1"
            @click.prevent.stop
          >
            <button
              type="button"
              class="inline-flex size-9 items-center justify-center rounded-full text-muted-foreground hover:bg-highlight disabled:opacity-40"
              :disabled="isOffline"
              :aria-label="$t('shopping-list.decrease-recipe', { recipe: recipe.name })"
              @click="removeRecipeReferenceToList(recipe.id)"
            >
              <MinusIcon class="size-4" />
            </button>
            <span class="min-w-6 text-center text-sm font-semibold tabular-nums">{{ shoppingList.recipeReferences[index]!.recipeQuantity }}</span>
            <button
              type="button"
              class="inline-flex size-9 items-center justify-center rounded-full text-muted-foreground hover:bg-highlight disabled:opacity-40"
              :disabled="isOffline"
              :aria-label="$t('shopping-list.increase-recipe', { recipe: recipe.name })"
              @click="addRecipeReferenceToList(recipe.id)"
            >
              <PlusIcon class="size-4" />
            </button>
          </div>
        </template>
      </RecipeList>
    </section>
    <WakelockSwitch class="mt-6" />
  </div>
</template>

<script setup lang="ts">
import { ChevronDownIcon, ChevronLeftIcon, EllipsisIcon, MinusIcon, PlusIcon, SearchIcon } from "@lucide/vue";
import { useMediaQuery } from "@vueuse/core";
import { VueDraggable } from "vue-draggable-plus";
import { Button } from "~/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "~/components/ui/dropdown-menu";
import { MdiIcon } from "~/components/ui/mdi-icon";
import RecipeList from "~/components/Domain/Recipe/RecipeList.vue";
import MultiPurposeLabelSection from "~/components/Domain/ShoppingList/MultiPurposeLabelSection.vue";
import ShoppingListAddItemForm from "~/components/Domain/ShoppingList/ShoppingListAddItemForm.vue";
import ShoppingListQuickAdd from "~/components/Domain/ShoppingList/ShoppingListQuickAdd.vue";
import ShoppingListItem from "~/components/Domain/ShoppingList/ShoppingListItem.vue";
import { useShoppingListPage } from "~/composables/shopping-list-page/use-shopping-list-page";
import { useLabelStore, useUnitStore, useFoodStore } from "~/composables/store";
import { alert } from "~/composables/use-toast";
import type { ShoppingListItemOut } from "~/lib/api/types/household";

definePageMeta({
  middleware: ["auth"],
});

// phones get the add field docked above the bottom tab bar
const isPhone = useMediaQuery("(max-width: 767.98px)");
const collapsed = reactive<Record<string, boolean>>({});
const i18n = useI18n();

useSeoMeta({
  title: i18n.t("shopping-list.shopping-list"),
});

const route = useRoute();
const id = route.params.id as string;

const editingItem = ref<string | undefined>(undefined);
const shoppingListPage = useShoppingListPage(id);
const { store: allLabels } = useLabelStore();
const { store: allUnits } = useUnitStore();
const { store: allFoods } = useFoodStore();

function itemCheckedToast(item: ShoppingListItemOut) {
  setTimeout(() => {
    alert.info(
      i18n.t("shopping-list.item-checked-off", { item: item.food?.name || item.note || i18n.t("recipe.ingredient") }),
      undefined,
      {
        timeout: 4000,
        action: {
          message: i18n.t("general.undo"),
          onClick: () => {
            item.checked = false;
            shoppingListPage.saveListItem(item);
          },
        },
      },
    );
  }, 500);
}

const {
  shoppingList,
  state,
  checkAll,
  uncheckAll,
  deleteChecked,
  reorderLabelsDialog,
  localLabels,
  saveLabelOrder,
  cancelLabelOrder,
  updateLabelOrder,
  edit,
  openCheckAll,
  copyListItems,
  toggleReorderLabelsDialog,
  isOffline,
  hasConflictedWrites,
  discardConflictedChanges,
  createListItemData,
  createListItem,
  itemsByLabel,
  getLabelColor,
  loadingCounter,
  updateIndexUncheckedByLabel,
  recipeMap,
  saveListItem,
  deleteListItem,
  listItems,
  openUncheckAll,
  openDeleteChecked,
  recipeList,
  removeRecipeReferenceToList,
  addRecipeReferenceToList,
  search,
  isSearching,
  isSearchOpen,
  canSearch,
  toggleSearch,
  matchesSearch,
  hasMatches,
  clearSearch,
  visibleCheckedCount,
  hasSearchResults,
} = shoppingListPage;

// Once per streak of failures: the items stay queued and look saved, so this is the only sign they aren't
watch(shoppingListPage.hasFailedWrites, (failed) => {
  if (failed) {
    alert.error(i18n.t("shopping-list.changes-not-saved"));
  }
});

// Expand the checked section while searching, so an item that has already been
// checked off can be found and unchecked without expanding the section by hand.
const checkedOpen = ref(false);
watch(isSearching, (searching) => {
  checkedOpen.value = searching;
});
</script>
