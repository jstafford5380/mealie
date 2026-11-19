<template>
  <div
    v-if="shoppingListChoices && ready"
    class="mx-auto w-full max-w-[760px] px-4 pb-24 pt-3 font-sans sm:px-6 lg:pt-8"
  >
    <BaseDialog
      v-model="state.createDialog"
      :title="$t('shopping-list.create-shopping-list')"
      :icon="$globals.icons.formatListCheck"
      can-submit
      :submit-disabled="!isCreateNameValid"
      @submit="createOne"
    >
      <div class="px-6 pb-2">
        <TextField
          v-model.trim="state.createName"
          autofocus
          :label="$t('shopping-list.new-list')"
        />
      </div>
    </BaseDialog>

    <BaseDialog
      v-model="state.ownerDialog"
      :icon="$globals.icons.user"
      :title="$t('general.change-owner')"
      can-confirm
      @confirm="updateOwner"
    >
      <div class="px-6 pb-2">
        <SelectField
          v-model="updateUserId"
          :items="allUsers"
          item-title="fullName"
          item-value="id"
          :label="$t('general.owner')"
        />
      </div>
    </BaseDialog>

    <BaseDialog
      v-model="state.deleteDialog"
      :title="$t('general.confirm')"
      :icon="$globals.icons.alertCircle"
      color="error"
      can-confirm
      @confirm="deleteOne"
    >
      <p class="m-0 px-6 pb-2 text-[15px]">
        {{ $t('shopping-list.delete-list-confirm', { name: deleteTargetName }) }}
      </p>
    </BaseDialog>

    <header class="mb-5 flex flex-wrap items-end gap-3">
      <h1 class="m-0 flex-1 text-[26px] font-bold tracking-tight sm:text-[32px]">
        {{ $t('shopping-list.shopping-lists') }}
      </h1>
      <Button @click="state.createDialog = true">
        <PlusIcon class="size-4" />
        {{ $t('shopping-list.new-list') }}
      </Button>
    </header>

    <label class="mb-4 flex w-fit cursor-pointer items-center gap-3 text-sm text-muted-foreground">
      <Switch v-model="preferences.viewAllLists" />
      {{ $t('shopping-list.show-household-lists') }}
    </label>

    <div
      v-if="!shoppingListChoices.length"
      class="flex flex-col items-center gap-3 rounded-card border border-dashed px-6 py-12 text-center"
    >
      <MdiIcon
        :path="$globals.icons.cartCheck"
        class="size-8 text-muted-foreground"
      />
      <p class="m-0 text-[15px] text-muted-foreground">
        {{ $t('shopping-list.no-lists-yet') }}
      </p>
      <Button
        variant="outline"
        @click="state.createDialog = true"
      >
        <PlusIcon class="size-4" />
        {{ $t('shopping-list.new-list') }}
      </Button>
    </div>

    <ul
      v-else
      class="m-0 flex list-none flex-col gap-2 p-0"
    >
      <li
        v-for="list in shoppingListChoices"
        :key="list.id"
        class="group flex min-w-0 items-center gap-1 rounded-card border bg-card pe-1 transition-colors hover:border-primary/40"
      >
        <NuxtLink
          :to="`/shopping-lists/${list.id}`"
          class="flex min-h-16 min-w-0 flex-1 items-center gap-3 px-4 py-3 text-foreground no-underline"
        >
          <span class="inline-flex size-10 shrink-0 items-center justify-center rounded-full bg-subtle text-subtle-foreground">
            <MdiIcon
              :path="$globals.icons.cartCheck"
              class="size-5"
            />
          </span>
          <span class="min-w-0 flex-1">
            <span class="block truncate text-base font-semibold">{{ list.name }}</span>
            <span
              v-if="list.userId !== auth.user.value?.id"
              class="block truncate text-[13px] text-muted-foreground"
            >{{ $t('shopping-list.someone-elses-list') }}</span>
          </span>
          <ChevronRightIcon class="size-5 shrink-0 text-muted-foreground" />
        </NuxtLink>
        <DropdownMenu :modal="false">
          <DropdownMenuTrigger as-child>
            <button
              type="button"
              class="inline-flex size-10 shrink-0 items-center justify-center rounded-full text-muted-foreground hover:bg-highlight hover:text-foreground"
              :aria-label="$t('shopping-list.list-options', { name: list.name })"
            >
              <EllipsisVerticalIcon class="size-5" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            align="end"
            class="min-w-48"
          >
            <DropdownMenuItem @select="toggleOwnerDialog(list)">
              <MdiIcon
                :path="$globals.icons.user"
                class="size-4"
              />
              {{ $t('general.change-owner') }}
            </DropdownMenuItem>
            <DropdownMenuItem
              variant="destructive"
              @select="openDelete(list)"
            >
              <MdiIcon
                :path="$globals.icons.delete"
                class="size-4"
              />
              {{ $t('general.delete') }}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { ChevronRightIcon, EllipsisVerticalIcon, PlusIcon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "~/components/ui/dropdown-menu";
import SelectField from "~/components/ui/field/SelectField.vue";
import TextField from "~/components/ui/field/TextField.vue";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { Switch } from "~/components/ui/switch";
import type { ShoppingListOut } from "~/lib/api/types/household";
import { useUserApi } from "~/composables/api";
import { useAsyncKey } from "~/composables/use-utils";
import { useShoppingListPreferences } from "~/composables/use-users/preferences";
import type { UserOut } from "~/lib/api/types/user";

definePageMeta({
  middleware: ["auth"],
});

const auth = useMealieAuth();
const i18n = useI18n();
const ready = ref(false);
const userApi = useUserApi();
const route = useRoute();

useSeoMeta({
  title: i18n.t("shopping-list.shopping-list"),
});

const overrideDisableRedirect = ref(false);
const disableRedirect = computed(() => route.query.disableRedirect === "true" || overrideDisableRedirect.value);
const preferences = useShoppingListPreferences();

const state = reactive({
  createName: "",
  createDialog: false,
  deleteDialog: false,
  deleteTarget: null as ShoppingListOut | null,
  ownerDialog: false,
  ownerTarget: ref<ShoppingListOut | null>(null),
});
const isCreateNameValid = computed(() => state.createName.trim().length > 0);

const { data: shoppingLists } = useAsyncData(useAsyncKey(), async () => {
  return await fetchShoppingLists();
});

const shoppingListChoices = computed(() => {
  if (!shoppingLists.value) {
    return [];
  }

  return shoppingLists.value.filter(list => preferences.value.viewAllLists || list.userId === auth.user.value?.id);
});

// This has to appear before the shoppingListChoices watcher, otherwise that runs first and the redirect is not disabled
watch(
  () => preferences.value.viewAllLists,
  () => {
    overrideDisableRedirect.value = true;
  },
);

watch(
  () => shoppingListChoices,
  () => {
    if (!disableRedirect.value && shoppingListChoices.value.length === 1) {
      navigateTo(`/shopping-lists/${shoppingListChoices.value[0].id}`);
    }
    else {
      ready.value = true;
    }
  },
  {
    deep: true,
  },
);

async function fetchShoppingLists() {
  const { data } = await userApi.shopping.lists.getAll(1, -1, { orderBy: "name", orderDirection: "asc" });

  if (!data) {
    return [];
  }

  return data.items;
}

async function refresh() {
  shoppingLists.value = await fetchShoppingLists();
}

async function createOne() {
  if (!isCreateNameValid.value) return;
  const { data } = await userApi.shopping.lists.createOne({ name: state.createName.trim() });

  if (data) {
    refresh();
    state.createName = "";
  }
}

async function toggleOwnerDialog(list: ShoppingListOut) {
  if (!state.ownerDialog) {
    state.ownerTarget = list;
    await fetchAllUsers();
  }
  state.ownerDialog = !state.ownerDialog;
}

// ===============================================================
// Shopping List Edit User/Owner

const allUsers = ref<UserOut[]>([]);
const updateUserId = ref<string | undefined>();
async function fetchAllUsers() {
  const { data } = await userApi.households.fetchMembers();
  if (!data) {
    return;
  }

  // update current user
  allUsers.value = data.items.sort((a, b) => ((a.fullName || "") < (b.fullName || "") ? -1 : 1));
  updateUserId.value = state.ownerTarget?.userId;
}

async function updateOwner() {
  if (!state.ownerTarget || !updateUserId.value) {
    return;
  }
  // user has not changed, so we should not update
  if (state.ownerTarget.userId === updateUserId.value) {
    return;
  }
  // get full list, so the move does not delete shopping list items
  const { data: fullList } = await userApi.shopping.lists.getOne(state.ownerTarget.id);
  if (!fullList) {
    return;
  }
  const { data } = await userApi.shopping.lists.updateOne(
    state.ownerTarget.id,
    { ...fullList, userId: updateUserId.value },
  );

  if (data) {
    refresh();
  }
}

const deleteTargetName = computed(() => state.deleteTarget?.name ?? "");

function openDelete(list: ShoppingListOut) {
  state.deleteDialog = true;
  state.deleteTarget = list;
}

async function deleteOne() {
  if (!state.deleteTarget) {
    return;
  }
  const { data } = await userApi.shopping.lists.deleteOne(state.deleteTarget.id);
  if (data) {
    refresh();
  }
}
</script>
