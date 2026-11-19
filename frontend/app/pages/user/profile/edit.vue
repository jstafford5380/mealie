<template>
  <div class="mx-auto flex w-full max-w-[760px] flex-col gap-8 px-4 pb-16 pt-3 font-sans sm:px-6 lg:pt-8">
    <NuxtLink
      to="/user/profile"
      class="-mb-4 inline-flex w-fit items-center gap-1 text-sm font-semibold text-muted-foreground no-underline hover:text-foreground"
    >
      <ChevronLeftIcon class="size-4 rtl:rotate-180" />
      {{ $t('profile.back-to-profile') }}
    </NuxtLink>

    <header class="flex flex-wrap items-center gap-4">
      <UserAvatar
        :tooltip="false"
        size="72"
        :user-id="userCopy.id!"
      />
      <div class="min-w-0 flex-1">
        <h1 class="m-0 text-[26px] font-bold tracking-tight sm:text-[32px]">
          {{ $t("profile.user-settings") }}
        </h1>
      </div>
      <AppButtonUpload
        file-name="profile"
        accept="image/*"
        :text="$t('profile.change-photo')"
        :url="`/api/users/${userCopy.id}/image`"
        @uploaded="auth.getSession()"
      />
    </header>

    <FieldScope ref="userUpdate">
      <form
        class="rounded-panel border bg-card p-5 sm:p-6"
        @submit.prevent="updateUser"
      >
        <h2 class="m-0 mb-3 text-xl font-bold tracking-tight">
          {{ $t('profile.personal-information') }}
        </h2>
        <TextField
          v-model="userCopy.username"
          autocomplete="username"
          validate-on="blur"
          :label="$t('user.username')"
        />
        <TextField
          v-model="userCopy.fullName"
          autocomplete="name"
          validate-on="blur"
          :label="$t('user.full-name')"
        />
        <TextField
          v-model="userCopy.email"
          type="email"
          autocomplete="email"
          validate-on="blur"
          :label="$t('user.email')"
          :rules="[validators.required, validators.email]"
        />
        <div class="mt-4 flex justify-end border-t pt-4">
          <Button type="submit">
            {{ $t("general.update") }}
          </Button>
        </div>
      </form>
    </FieldScope>

    <FieldScope v-if="$appInfo.allowPasswordLogin">
      <form
        class="rounded-panel border bg-card p-5 sm:p-6"
        @submit.prevent="updatePassword"
      >
        <h2 class="m-0 mb-3 text-xl font-bold tracking-tight">
          {{ $t("settings.change-password") }}
        </h2>
        <TextField
          v-model="password.current"
          type="password"
          autocomplete="current-password"
          validate-on="blur"
          :label="$t('user.current-password')"
          :rules="[validators.minLength(1)]"
        />
        <TextField
          v-model="password.newOne"
          type="password"
          autocomplete="new-password"
          :label="$t('user.new-password')"
          :rules="[validators.minLength(8)]"
        />
        <UserPasswordStrength v-model="password.newOne" />
        <TextField
          v-model="password.newTwo"
          type="password"
          autocomplete="new-password"
          validate-on="blur"
          :label="$t('user.confirm-password')"
          :rules="[password.newOne === password.newTwo || $t('user.password-must-match')]"
        />
        <div class="mt-4 flex justify-end border-t pt-4">
          <Button
            type="submit"
            :disabled="!passwordsMatch || !password.current"
          >
            {{ $t("settings.change-password") }}
          </Button>
        </div>
      </form>
    </FieldScope>

    <section class="rounded-panel border bg-card p-5 sm:p-6">
      <h2 class="m-0 mb-3 text-xl font-bold tracking-tight">
        {{ $t('profile.preferences') }}
      </h2>
      <div class="max-w-sm">
        <SelectField
          v-model="selectedDefaultActivity"
          :items="activityOptions"
          :label="$t('user.default-activity')"
          :hint="$t('user.default-activity-hint')"
        />
      </div>
      <div class="mt-2 flex flex-col gap-2">
        <CheckboxField
          v-model="userCopy.showAnnouncements"
          :label="$t('announcements.show-announcements-from-mealie')"
          @update:model-value="updateUser"
        />
        <CheckboxField
          v-model="userCopy.advanced"
          :label="$t('profile.show-advanced-description')"
          @update:model-value="updateUser"
        />
      </div>
      <p class="m-0 mt-5 border-t pt-4 text-sm">
        <NuxtLink
          to="/group"
          class="font-semibold text-primary no-underline hover:underline"
        >
          {{ $t('profile.looking-for-privacy-settings') }}
        </NuxtLink>
      </p>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ChevronLeftIcon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import CheckboxField from "~/components/ui/field/CheckboxField.vue";
import FieldScope from "~/components/ui/field/FieldScope.vue";
import SelectField from "~/components/ui/field/SelectField.vue";
import TextField from "~/components/ui/field/TextField.vue";
import { useUserApi } from "~/composables/api";
import UserAvatar from "~/components/Domain/User/UserAvatar.vue";
import UserPasswordStrength from "~/components/Domain/User/UserPasswordStrength.vue";
import { validators } from "~/composables/use-validators";
import { useUserActivityPreferences } from "~/composables/use-users/preferences";
import useDefaultActivity from "~/composables/use-default-activity";
import { ActivityKey } from "~/lib/api/types/activity";
import type { UserBase } from "~/lib/api/types/user";

definePageMeta({
  middleware: ["auth"],
});

const i18n = useI18n();
const auth = useMealieAuth();
const { getDefaultActivityLabels, getActivityLabel, getActivityKey } = useDefaultActivity();
const user = computed(() => auth.user.value);

useSeoMeta({
  title: i18n.t("settings.profile"),
});

const activityPreferences = useUserActivityPreferences();
const activityOptions = getDefaultActivityLabels(i18n);
const selectedDefaultActivity = ref(getActivityLabel(i18n, activityPreferences.value.defaultActivity));
watch(selectedDefaultActivity, () => {
  activityPreferences.value.defaultActivity = getActivityKey(i18n, selectedDefaultActivity.value) ?? ActivityKey.RECIPES;
});

const userCopy = ref({ ...user.value });
watch(user, () => {
  userCopy.value = { ...user.value };
});

const api = useUserApi();
const password = reactive({
  current: "",
  newOne: "",
  newTwo: "",
});

const passwordsMatch = computed(() => password.newOne === password.newTwo && password.newOne.length > 0);

const userUpdate = ref<{ validate: () => Promise<{ valid: boolean }> } | null>(null);

async function updateUser() {
  const { valid } = (await userUpdate.value?.validate()) ?? { valid: false };
  if (!valid) return;

  const userData = userCopy.value;
  if (!userData?.id || !userData.email) return;

  const updatePayload: UserBase = {
    id: userData.id,
    username: userData.username,
    fullName: userData.fullName,
    email: userData.email,
    authMethod: userData.authMethod,
    admin: userData.admin,
    group: userData.group,
    household: userData.household,
    showAnnouncements: userData.showAnnouncements,
    advanced: userData.advanced,
    canInvite: userData.canInvite,
    canManage: userData.canManage,
    canManageHousehold: userData.canManageHousehold,
    canOrganize: userData.canOrganize,
  };

  const { response } = await api.users.updateOne(userData.id, updatePayload);
  if (response?.status === 200) {
    auth.getSession();
  }
}

async function updatePassword() {
  if (!userCopy.value?.id) {
    return;
  }
  const { response } = await api.users.changePassword({
    currentPassword: password.current,
    newPassword: password.newOne,
  });

  if (response?.status === 200) {
    // The new password invalidates this session server-side, so end it here rather than letting the
    // next request fail its way to the login page.
    await auth.signOut();
  }
}
</script>
