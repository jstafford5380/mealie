<template>
  <div class="mx-auto flex w-full max-w-[1100px] flex-col px-4 pb-16 pt-3 font-sans sm:px-6 lg:pt-8">
    <UserInviteDialog v-model="inviteDialog" />
    <BaseDialog
      v-model="state.deleteDialog"
      :title="$t('general.confirm')"
      :icon="$globals.icons.alertCircle"
      color="error"
      can-confirm
      @confirm="deleteUser(state.deleteTargetId)"
    >
      <div class="flex flex-col gap-3 px-6 pb-2 text-[15px]">
        <p
          v-if="isUserOwnAccount"
          class="m-0 rounded-control border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
        >
          {{ $t('general.confirm-delete-own-admin-account') }}
        </p>
        <p class="m-0">
          {{ $t("general.confirm-delete-generic") }}
        </p>
      </div>
    </BaseDialog>

    <header class="mb-5 flex items-baseline gap-3">
      <h1 class="m-0 text-[26px] font-bold tracking-tight sm:text-[32px]">
        {{ $t('user.user-management') }}
      </h1>
      <span class="text-sm text-muted-foreground tabular-nums">{{ (users || []).length }}</span>
    </header>

    <CrudTable
      :headers="headers"
      :table-config="{ hideColumns: true, canExport: false }"
      :data="users || []"
      initial-sort="fullName"
      @edit-one="handleRowClick"
      @delete-one="openDelete"
    >
      <template #button-row>
        <Button
          variant="ghost"
          @click="unlockAllUsers"
        >
          <MdiIcon
            :path="$globals.icons.lock"
            class="size-4"
          />
          {{ $t('user.reset-locked-users') }}
        </Button>
        <Button
          v-if="$appInfo.allowPasswordLogin"
          variant="outline"
          @click="inviteDialog = true"
        >
          <MdiIcon
            :path="$globals.icons.link"
            class="size-4"
          />
          {{ $t("group.invite") }}
        </Button>
        <Button @click="navigateTo('/admin/manage/users/create')">
          <PlusIcon class="size-4" />
          {{ $t("user.create-user") }}
        </Button>
      </template>
      <template #[`item.fullName`]="{ item }">
        <NuxtLink
          :to="`/admin/manage/users/${item.id}`"
          class="font-medium text-foreground no-underline hover:text-primary hover:underline"
        >
          {{ item.fullName }}
        </NuxtLink>
      </template>
      <template #[`item.admin`]="{ item }">
        <span
          v-if="item.admin"
          class="rounded-full bg-primary/15 px-2 py-0.5 text-xs font-semibold text-primary"
        >{{ $t('user.admin') }}</span>
        <span
          v-else
          class="text-muted-foreground"
        >–</span>
      </template>
    </CrudTable>
  </div>
</template>

<script setup lang="ts">
import { PlusIcon } from "@lucide/vue";
import CrudTable from "~/components/global/CrudTable.vue";
import type { TableHeaders } from "~/components/global/CrudTable.vue";
import { Button } from "~/components/ui/button";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { useAdminApi } from "~/composables/api";
import { alert } from "~/composables/use-toast";
import { useUser, useAllUsers } from "~/composables/use-user";
import type { UserOut } from "~/lib/api/types/user";
import UserInviteDialog from "~/components/Domain/User/UserInviteDialog.vue";

definePageMeta({
  layout: "admin",
});
const i18n = useI18n();

useHead({
  title: i18n.t("sidebar.manage-users"),
});

const api = useAdminApi();
const inviteDialog = ref();
const auth = useMealieAuth();

const user = computed(() => auth.user.value);

const { $globals } = useNuxtApp();

const router = useRouter();

const isUserOwnAccount = computed(() => {
  return state.deleteTargetId === user.value?.id;
});

const state = reactive({
  deleteDialog: false,
  deleteTargetId: "",
  search: "",
  groups: [],
  households: [],
  sendTo: "",
});

const { users, refreshAllUsers } = useAllUsers();
const { deleteUser: deleteUserMixin } = useUser(refreshAllUsers);

function deleteUser(id: string) {
  deleteUserMixin(id);

  if (isUserOwnAccount.value) {
    auth.getSession();
  }
}

function handleRowClick(item: UserOut) {
  router.push(`/admin/manage/users/${item.id}`);
}

function openDelete(item: UserOut) {
  state.deleteTargetId = item.id;
  state.deleteDialog = true;
}

// ==========================================================
// Constants / Non-reactive

const headers: TableHeaders[] = [
  { text: i18n.t("user.full-name"), value: "fullName", show: true, sortable: true },
  { text: i18n.t("user.username"), value: "username", show: true, sortable: true },
  { text: i18n.t("user.email"), value: "email", show: true, sortable: true },
  { text: i18n.t("group.group"), value: "group", show: true, sortable: true },
  { text: i18n.t("household.household"), value: "household", show: true, sortable: true },
  { text: i18n.t("user.auth-method"), value: "authMethod", show: false, sortable: true },
  { text: i18n.t("user.admin"), value: "admin", show: true, sortable: true },
  { text: i18n.t("user.user-id"), value: "id", show: false },
];

async function unlockAllUsers(): Promise<void> {
  const { data } = await api.users.unlockAllUsers(true);

  if (data) {
    const unlocked = data.unlocked ?? 0;

    alert.success(`${unlocked} user(s) unlocked`);
    refreshAllUsers();
  }
}

useSeoMeta({
  title: i18n.t("sidebar.manage-users"),
});
</script>
