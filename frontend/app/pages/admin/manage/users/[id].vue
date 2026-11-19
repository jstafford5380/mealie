<template>
  <div
    v-if="user"
    class="mx-auto flex w-full max-w-[760px] flex-col px-4 pb-16 pt-3 font-sans sm:px-6 lg:pt-8"
  >
    <NuxtLink
      to="/admin/manage/users"
      class="mb-3 inline-flex w-fit items-center gap-1 text-sm font-semibold text-muted-foreground no-underline hover:text-foreground"
    >
      <ChevronLeftIcon class="size-4 rtl:rotate-180" />
      {{ $t('user.user-management') }}
    </NuxtLink>
    <header class="mb-6">
      <h1 class="m-0 text-[26px] font-bold tracking-tight sm:text-[32px]">
        {{ user.fullName || $t('user.admin-user-management') }}
      </h1>
      <p class="m-0 mt-1 text-[15px] text-muted-foreground">
        {{ $t('user.changes-reflected-immediately') }}
      </p>
    </header>
    <FieldScope
      v-if="!userError"
      ref="refNewUserForm"
    >
      <form
        class="flex flex-col gap-6"
        @submit.prevent="handleSubmit"
      >
        <section class="rounded-panel border bg-card p-5 sm:p-6">
          <p class="m-0 mb-3 font-mono text-xs text-muted-foreground">
            {{ $t("user.user-id-with-value", { id: user.id }) }}
          </p>
          <!-- Group can't be changed here: moving a user between groups isn't handled safely -->
          <div class="grid gap-x-4 sm:grid-cols-2">
            <SelectField
              v-if="groups"
              v-model="user.group"
              disabled
              :items="groups"
              item-title="name"
              item-value="name"
              :label="$t('group.user-group')"
            />
            <SelectField
              v-if="households"
              v-model="user.household"
              :items="households"
              item-title="name"
              item-value="name"
              :label="$t('household.user-household')"
              :rules="[validators.required]"
            />
          </div>
          <AutoForm
            v-model="user"
            class="px-0!"
            :items="userForm"
            update-mode
            :disabled-fields="disabledFields"
          />
          <div class="mt-4 flex justify-end border-t pt-4">
            <Button type="submit">
              {{ $t("general.update") }}
            </Button>
          </div>
        </section>

        <section class="rounded-panel border bg-card p-5 sm:p-6">
          <h2 class="m-0 mb-1 text-xl font-bold tracking-tight">
            {{ $t("user.reset-password") }}
          </h2>
          <p class="m-0 mb-4 text-sm text-muted-foreground">
            {{ $t("user.reset-link-explained") }}
          </p>
          <Button
            v-if="!resetUrl"
            type="button"
            variant="outline"
            :disabled="generatingToken"
            @click.prevent="handlePasswordReset"
          >
            <LoaderCircleIcon
              v-if="generatingToken"
              class="size-4 animate-spin"
            />
            {{ $t("user.generate-password-reset-link") }}
          </Button>
          <div
            v-else
            class="flex flex-col gap-3"
          >
            <input
              :value="resetUrl"
              readonly
              :aria-label="$t('user.reset-password')"
              class="h-10 w-full rounded-control border border-input bg-muted px-3 font-mono text-[13px] outline-none"
              @focus="($event.target as HTMLInputElement).select()"
            >
            <div class="flex flex-wrap justify-end gap-2">
              <Button
                type="button"
                variant="ghost"
                @click="resetUrl = ''"
              >
                {{ $t("general.done") }}
              </Button>
              <Button
                v-if="user.email"
                type="button"
                variant="outline"
                @click="sendResetEmail"
              >
                <MdiIcon
                  :path="$globals.icons.email"
                  class="size-4"
                />
                {{ $t("user.email") }}
              </Button>
              <AppButtonCopy
                :icon="false"
                :copy-text="resetUrl"
              />
            </div>
          </div>
        </section>
      </form>
    </FieldScope>
  </div>
</template>

<script setup lang="ts">
import { LoaderCircleIcon, ChevronLeftIcon } from "@lucide/vue";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { Button } from "~/components/ui/button";
import FieldScope from "~/components/ui/field/FieldScope.vue";
import SelectField from "~/components/ui/field/SelectField.vue";
import { useAdminApi, useUserApi } from "~/composables/api";
import { useGroups } from "~/composables/use-groups";
import { useAdminHouseholds } from "~/composables/use-households";
import { alert } from "~/composables/use-toast";
import { useUserForm } from "~/composables/use-users";
import { validators } from "~/composables/use-validators";
import type { UserOut } from "~/lib/api/types/user";

definePageMeta({
  layout: "admin",
});

const { userForm } = useUserForm();
const { groups } = useGroups();
const { useHouseholdsInGroup } = useAdminHouseholds();
const i18n = useI18n();
const route = useRoute();

const userId = route.params.id as string;

// ==============================================
// New User Form

const refNewUserForm = ref<{ validate: () => Promise<{ valid: boolean }> } | null>(null);

const adminApi = useAdminApi();

const user = ref<UserOut | null>(null);
const households = useHouseholdsInGroup(computed(() => user.value?.groupId || ""));

const disabledFields = computed(() => {
  const fields: string[] = [];
  if (user.value?.authMethod !== "Mealie") {
    fields.push("admin");
  }
  if (user.value?.admin) {
    fields.push("canManageHousehold", "canManage", "advanced");
  }
  if (user.value?.admin) {
    fields.push("canOrganize", "canInvite");
  }
  return fields;
});

watch(
  () => user.value?.admin,
  (isAdmin, wasAdmin) => {
    if (!user.value) {
      return;
    }
    if (isAdmin && !wasAdmin) {
      user.value.canManageHousehold = true;
      user.value.canManage = true;
      user.value.canOrganize = true;
      user.value.canInvite = true;
      user.value.advanced = true;
    }
    else if (!isAdmin && wasAdmin) {
      user.value.canManageHousehold = false;
      user.value.canManage = false;
      user.value.canOrganize = false;
      user.value.canInvite = false;
      user.value.advanced = false;
    }
  },
);

const userError = ref(false);

const resetUrl = ref<string | null>(null);
const generatingToken = ref(false);

onMounted(async () => {
  const { data, error } = await adminApi.users.getOne(userId);

  if (error?.response?.status === 404) {
    alert.error(i18n.t("user.user-not-found"));
    userError.value = true;
  }

  if (data) {
    user.value = data;
  }
});

async function handleSubmit() {
  if (!refNewUserForm.value?.validate() || user.value === null) return;

  const { response, data } = await adminApi.users.updateOne(user.value.id, user.value);

  if (response?.status === 200 && data) {
    user.value = data;
  }
}

async function handlePasswordReset() {
  if (user.value === null) return;
  generatingToken.value = true;

  const { response, data } = await adminApi.users.generatePasswordResetToken({ email: user.value.email });

  if (response?.status === 201 && data) {
    const token: string = data.token;
    resetUrl.value = `${window.location.origin}/reset-password/?token=${token}`;
  }

  generatingToken.value = false;
}

const userApi = useUserApi();
async function sendResetEmail() {
  if (!user.value?.email) return;
  const { response } = await userApi.email.sendForgotPassword({ email: user.value.email });
  if (response && response.status === 200) {
    alert.success(i18n.t("profile.email-sent"));
  }
  else {
    alert.error(i18n.t("profile.error-sending-email"));
  }
}
</script>
