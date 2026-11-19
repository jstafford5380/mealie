<template>
  <div class="mx-auto flex w-full max-w-[900px] flex-col gap-6 px-4 pb-16 pt-3 font-sans sm:px-6 lg:pt-8">
    <header>
      <h1 class="m-0 text-[26px] font-bold tracking-tight sm:text-[32px]">
        {{ $t('group.manage-members') }}
      </h1>
      <p class="m-0 mt-1 max-w-[65ch] text-[15px] text-muted-foreground">
        <i18n-t keypath="group.manage-members-description">
          <template #manage>
            <b>{{ $t('group.manage') }}</b>
          </template>
          <template #organize>
            <b>{{ $t('settings.organize') }}</b>
          </template>
          <template #invite>
            <b>{{ $t('group.invite') }}</b>
          </template>
        </i18n-t>
      </p>
      <NuxtLink
        to="/user/profile/edit"
        class="mt-2 inline-block text-sm font-semibold text-primary no-underline hover:underline"
      >
        {{ $t('group.looking-to-update-your-profile') }}
      </NuxtLink>
    </header>

    <!-- what each permission means, spelled out instead of hidden in header tooltips -->
    <dl class="m-0 grid gap-x-6 gap-y-2 rounded-card border bg-card p-4 text-sm sm:grid-cols-2">
      <div
        v-for="perm in PERMISSIONS"
        :key="perm.key"
      >
        <dt class="font-semibold">
          {{ perm.label }}
        </dt>
        <dd class="m-0 text-muted-foreground">
          {{ perm.hint }}
        </dd>
      </div>
    </dl>

    <ul class="m-0 flex list-none flex-col divide-y rounded-card border bg-card p-0">
      <template
        v-for="item in members"
        :key="item?.id"
      >
        <li
          v-if="item"
          class="flex flex-col gap-3 p-4 lg:flex-row lg:items-center"
        >
          <div class="flex min-w-0 flex-1 items-center gap-3">
            <UserAvatar
              :tooltip="false"
              size="40"
              :user-id="item.id"
            />
            <div class="min-w-0">
              <p class="m-0 truncate font-semibold">
                {{ item.fullName }}
                <span
                  v-if="item.admin"
                  class="ms-1 rounded-full bg-subtle px-2 py-0.5 align-middle text-xs font-semibold text-subtle-foreground"
                >{{ $t('user.admin') }}</span>
              </p>
              <p class="m-0 truncate text-sm text-muted-foreground">
                {{ item.username }}
              </p>
            </div>
          </div>
          <div class="flex flex-wrap gap-x-5 gap-y-2">
            <label
              v-for="perm in PERMISSIONS"
              :key="perm.key"
              class="flex items-center gap-2 text-sm"
              :class="isLocked(item) ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'"
              :title="isLocked(item) ? $t('group.permissions-locked') : perm.hint"
            >
              <Checkbox
                :model-value="!!item[perm.key]"
                :disabled="isLocked(item)"
                @update:model-value="item[perm.key] = !!$event; setPermissions(item)"
              />
              {{ perm.label }}
            </label>
          </div>
        </li>
      </template>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { Checkbox } from "~/components/ui/checkbox";
import { useUserApi } from "~/composables/api";
import type { UserOut } from "~/lib/api/types/user";
import UserAvatar from "~/components/Domain/User/UserAvatar.vue";

definePageMeta({
  middleware: ["auth"],
});

const api = useUserApi();
const i18n = useI18n();

useSeoMeta({
  title: i18n.t("profile.members"),
});

const members = ref<UserOut[] | null[]>([]);

const auth = useMealieAuth();
const sessionUser = computed(() => auth.user.value);

type PermissionKey = "canManage" | "canOrganize" | "canInvite" | "canManageHousehold";
const PERMISSIONS: { key: PermissionKey; label: string; hint: string }[] = [
  { key: "canManage", label: i18n.t("group.manage"), hint: i18n.t("user.user-can-manage-group-hint") },
  { key: "canOrganize", label: i18n.t("settings.organize"), hint: i18n.t("user.user-can-organize-group-data-hint") },
  { key: "canInvite", label: i18n.t("group.invite"), hint: i18n.t("user.user-can-invite-other-to-group-hint") },
  { key: "canManageHousehold", label: i18n.t("group.manage-household"), hint: i18n.t("user.user-can-manage-household-hint") },
];

// You can't change your own permissions, and admins always have all of them
function isLocked(user: UserOut) {
  return user.id === sessionUser.value?.id || user.admin;
}

async function refreshMembers() {
  const { data } = await api.households.fetchMembers();
  if (data) {
    members.value = data.items;
  }
}

async function setPermissions(user: UserOut) {
  const payload = {
    userId: user.id,
    canInvite: user.canInvite,
    canManageHousehold: user.canManageHousehold,
    canManage: user.canManage,
    canOrganize: user.canOrganize,
  };

  await api.households.setMemberPermissions(payload);
}

onMounted(async () => {
  await refreshMembers();
});
</script>
