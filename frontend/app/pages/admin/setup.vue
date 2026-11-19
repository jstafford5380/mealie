<template>
  <AuthFrame
    wide
    :links="false"
  >
    <!-- progress: numbered because it is a sequence -->
    <ol
      class="m-0 mb-6 flex list-none items-center gap-1.5 p-0"
      :aria-label="$t('admin.setup.first-time-setup')"
    >
      <li
        v-for="step in steps"
        :key="step.page"
        class="flex min-w-0 flex-1 flex-col gap-1.5"
        :aria-current="currentPage === step.page ? 'step' : undefined"
      >
        <span
          class="h-1.5 rounded-full transition-colors"
          :class="currentPage >= step.page ? 'bg-primary' : 'bg-muted'"
        />
        <span
          class="display-none truncate text-xs font-semibold sm:block"
          :class="currentPage === step.page ? 'text-foreground' : 'text-muted-foreground'"
        >{{ step.title }}</span>
      </li>
    </ol>
    <p class="m-0 mb-1 text-sm font-semibold text-muted-foreground sm:display-none">
      {{ $t("user-registration.step-of", { step: currentPage, total: steps.length }) }} · {{ currentStep?.title }}
    </p>

    <!-- LANDING -->
    <div
      v-if="currentPage === Pages.LANDING"
      class="flex flex-col gap-4"
    >
      <h1 class="m-0 text-[26px] font-bold tracking-tight sm:text-[30px]">
        {{ $t('admin.setup.welcome-to-mealie-get-started') }}
      </h1>
      <p class="m-0 text-[15px] text-muted-foreground">
        {{ $t('admin.setup.previous-mealie-instance') }}
      </p>
      <div class="flex flex-wrap gap-2">
        <Button
          variant="outline"
          @click="navigateTo('/admin/backups')"
        >
          <MdiIcon
            :path="$globals.icons.backupRestore"
            class="size-4"
          />
          {{ $t('settings.backup.restore-backup') }}
        </Button>
        <Button
          variant="ghost"
          @click="navigateTo(groupSlug ? `/g/${groupSlug}` : '/login')"
        >
          {{ $t('admin.setup.already-set-up-bring-to-homepage') }}
        </Button>
      </div>
      <Button
        variant="ghost"
        class="self-start"
        @click="langDialog = true"
      >
        <MdiIcon
          :path="$globals.icons.translate"
          class="size-4"
        />
        {{ $t('language-dialog.choose-language') }}
      </Button>
    </div>

    <!-- USER INFO: kept mounted so its fields keep their values when stepping back -->
    <div v-show="currentPage === Pages.USER_INFO">
      <h1 class="m-0 mb-5 text-[26px] font-bold tracking-tight">
        {{ $t('user-registration.account-details') }}
      </h1>
      <UserRegistrationForm />
    </div>

    <!-- COMMON SETTINGS -->
    <div v-if="currentPage === Pages.PAGE_2">
      <h1 class="m-0 mb-3 text-[26px] font-bold tracking-tight">
        {{ $t('admin.setup.common-settings-for-new-sites') }}
      </h1>
      <AutoForm
        v-model="commonSettings"
        :items="commonSettingsForm"
      />
    </div>

    <!-- AI PROVIDERS -->
    <div v-if="currentPage === Pages.AI_PROVIDERS">
      <h1 class="m-0 text-[26px] font-bold tracking-tight">
        {{ $t('group.ai-provider-settings.ai-providers') }}
      </h1>
      <p class="m-0 mt-1.5 mb-5 text-[15px] text-muted-foreground">
        {{ $t('group.ai-provider-settings.ai-providers-description') }}
      </p>
      <GroupAIProviderSettingsEditor
        v-if="group?.aiProviderSettings"
        v-model="group.aiProviderSettings"
        hide-header
        @create="handleCreateProvider"
        @update="handleUpdateProvider"
        @delete="handleDeleteProvider"
      />
    </div>

    <!-- CONFIRMATION -->
    <div v-if="currentPage === Pages.CONFIRM">
      <h1 class="m-0 mb-5 text-[26px] font-bold tracking-tight">
        {{ $t('general.confirm-how-does-everything-look') }}
      </h1>
      <dl class="m-0 divide-y rounded-card border">
        <template
          v-for="(item, idx) in confirmationData"
          :key="idx"
        >
          <div
            v-if="item.display"
            class="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-0.5 px-4 py-3"
          >
            <dt class="text-sm text-muted-foreground">
              {{ item.text }}
            </dt>
            <dd class="m-0 font-semibold">
              {{ item.value }}
            </dd>
          </div>
        </template>
      </dl>
    </div>

    <!-- END -->
    <div v-if="currentPage === Pages.END">
      <h1 class="m-0 text-[26px] font-bold tracking-tight">
        {{ $t('admin.setup.setup-complete') }}
      </h1>
      <p class="m-0 mt-1.5 mb-5 text-[15px] text-muted-foreground">
        {{ $t('admin.setup.here-are-a-few-things-to-help-you-get-started') }}
      </p>
      <EndPageContent />
    </div>

    <div class="mt-8 flex items-center justify-between gap-3 border-t pt-5">
      <Button
        v-if="currentPage > Pages.LANDING && currentPage < Pages.END"
        variant="ghost"
        :disabled="isSubmitting"
        @click="onPrev"
      >
        <ChevronLeftIcon class="size-4 rtl:rotate-180" />
        {{ $t('general.back') }}
      </Button>
      <span v-else />
      <Button
        v-if="currentPage === Pages.END"
        :disabled="isSubmitting"
        @click="onFinish"
      >
        <MdiIcon
          :path="$globals.icons.home"
          class="size-4"
        />
        {{ $t('general.home') }}
      </Button>
      <Button
        v-else
        :disabled="isSubmitting"
        @click="onNext"
      >
        <LoaderCircleIcon
          v-if="isSubmitting"
          class="size-4 animate-spin"
        />
        {{ currentPage === Pages.CONFIRM ? $t('admin.setup.finish-setup') : $t('general.next') }}
        <ChevronRightIcon
          v-if="currentPage !== Pages.CONFIRM"
          class="size-4 rtl:rotate-180"
        />
      </Button>
    </div>

    <template #below>
      <LanguageDialog v-model="langDialog" />
    </template>
  </AuthFrame>
</template>

<script setup lang="ts">
import { ChevronLeftIcon, ChevronRightIcon, LoaderCircleIcon } from "@lucide/vue";
import AuthFrame from "~/components/Layout/LayoutParts/AuthFrame.vue";
import EndPageContent from "~/components/Domain/Admin/Setup/EndPageContent.vue";
import { Button } from "~/components/ui/button";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { useAdminApi, useUserApi } from "~/composables/api";
import { useLocales } from "~/composables/use-locales";
import { alert } from "~/composables/use-toast";
import { useUserRegistrationForm } from "~/composables/use-users/user-registration-form";
import { useCommonSettingsForm } from "~/composables/use-setup/common-settings-form";
import { useGroupSelf } from "~/composables/use-groups";
import { useAIProviders } from "~/composables/use-ai-providers";
import UserRegistrationForm from "~/components/Domain/User/UserRegistrationForm.vue";
import GroupAIProviderSettingsEditor from "~/components/Domain/Group/GroupAIProviderSettingsEditor.vue";
import type { AIProviderCreate, AIProviderUpdate } from "~/lib/api/types/group";

definePageMeta({
  layout: "blank",
  middleware: ["admin-only"],
});

// ================================================================
// Setup
const i18n = useI18n();
const auth = useMealieAuth();
const userApi = useUserApi();
const adminApi = useAdminApi();

const groupSlug = computed(() => auth.user.value?.groupSlug);

const { group, actions: groupActions } = useGroupSelf();
const { createOne, updateOne, deleteOne } = useAIProviders();

async function handleCreateProvider(data: AIProviderCreate) {
  const result = await createOne(data);
  if (result.data) {
    await groupActions.refresh();
    alert.success(i18n.t("group.ai-provider-settings.provider-created"));
  }
  else {
    alert.error(i18n.t("group.ai-provider-settings.provider-create-failed"));
  }
}

async function handleUpdateProvider(id: string, data: AIProviderUpdate) {
  const result = await updateOne(id, data);
  if (result.data) {
    await groupActions.refresh();
    alert.success(i18n.t("group.ai-provider-settings.provider-updated"));
  }
  else {
    alert.error(i18n.t("group.ai-provider-settings.provider-update-failed"));
  }
}

async function handleDeleteProvider(id: string) {
  const result = await deleteOne(id);
  if (result.data) {
    await groupActions.refresh();
    alert.success(i18n.t("group.ai-provider-settings.provider-deleted"));
  }
  else {
    alert.error(i18n.t("group.ai-provider-settings.provider-delete-failed"));
  }
}
const { locale } = useLocales();
const router = useRouter();
const isSubmitting = ref(false);
const langDialog = ref(false);

useSeoMeta({
  title: i18n.t("admin.setup.first-time-setup"),
});

enum Pages {
  LANDING = 1,
  USER_INFO = 2,
  PAGE_2 = 3,
  AI_PROVIDERS = 4,
  CONFIRM = 5,
  END = 6,
}

const steps = computed(() => [
  { page: Pages.LANDING, title: i18n.t("general.start") },
  { page: Pages.USER_INFO, title: i18n.t("user-registration.account-details") },
  { page: Pages.PAGE_2, title: i18n.t("settings.site-settings") },
  { page: Pages.AI_PROVIDERS, title: i18n.t("group.ai-provider-settings.ai-providers") },
  { page: Pages.CONFIRM, title: i18n.t("admin.maintenance.summary-title") },
  { page: Pages.END, title: i18n.t("admin.setup.setup-complete") },
]);

// ================================================================
// Forms
const { accountDetails, credentials } = useUserRegistrationForm();
const { commonSettingsForm } = useCommonSettingsForm();
const commonSettings = ref({
  makeGroupRecipesPublic: false,
  useSeedData: true,
});

const confirmationData = computed(() => {
  return [
    {
      display: true,
      text: i18n.t("user.email"),
      value: accountDetails.email.value,
    },
    {
      display: true,
      text: i18n.t("user.username"),
      value: accountDetails.username.value,
    },
    {
      display: true,
      text: i18n.t("user.full-name"),
      value: accountDetails.fullName.value,
    },
    {
      display: true,
      text: i18n.t("user.enable-advanced-content"),
      value: accountDetails.advancedOptions.value ? i18n.t("general.yes") : i18n.t("general.no"),
    },
    {
      display: true,
      text: i18n.t("group.enable-public-access"),
      value: commonSettings.value.makeGroupRecipesPublic ? i18n.t("general.yes") : i18n.t("general.no"),
    },
    {
      display: true,
      text: i18n.t("user-registration.use-seed-data"),
      value: commonSettings.value.useSeedData ? i18n.t("general.yes") : i18n.t("general.no"),
    },
  ];
});

// ================================================================
// Page Navigation
const currentPage = ref(Pages.LANDING);
const currentStep = computed(() => steps.value.find(step => step.page === currentPage.value));

// ================================================================
// Page Submission

async function updateUser() {
  // Note: auth.user is now a ref
  const { response } = await userApi.users.updateOne(auth.user.value!.id, {
    ...auth.user.value,
    email: accountDetails.email.value,
    username: accountDetails.username.value,
    fullName: accountDetails.fullName.value,
    advanced: accountDetails.advancedOptions.value,
  });

  if (!response || response.status !== 200) {
    alert.error(i18n.t("events.something-went-wrong"));
  }
  else {
    auth.getSession();
  }
}

async function updatePassword() {
  // Read before updateUser can change it: the account is still identified by its current email at
  // the point we have to sign back in.
  const currentEmail = auth.user.value!.email;
  const newPassword = credentials.password1.value;

  const { response } = await userApi.users.changePassword({
    currentPassword: "MyPassword",
    newPassword,
  });

  if (!response || response.status !== 200) {
    alert.error(i18n.t("events.something-went-wrong"));
    return;
  }

  // Changing the password invalidates this session, and setup has several authenticated steps left,
  // so sign straight back in rather than letting the rest of the wizard 401.
  const formData = new FormData();
  formData.append("username", currentEmail);
  formData.append("password", newPassword);
  formData.append("remember_me", "true");

  try {
    await auth.signIn(formData);
  }
  catch {
    alert.error(i18n.t("events.something-went-wrong"));
  }
}

async function submitRegistration() {
  // we update the password first, then update the user's details
  await updatePassword().then(updateUser);
}

async function updateGroup() {
  // Note: auth.user is now a ref
  const { data } = await userApi.groups.getOne(auth.user.value!.groupId);
  if (!data || !data.preferences) {
    alert.error(i18n.t("events.something-went-wrong"));
    return;
  }

  const preferences = {
    ...data.preferences,
    privateGroup: !commonSettings.value.makeGroupRecipesPublic,
  };

  const payload = {
    ...data,
    preferences,
  };

  // Note: auth.user is now a ref
  const { response } = await userApi.groups.updateOne(auth.user.value!.groupId, payload);
  if (!response || response.status !== 200) {
    alert.error(i18n.t("events.something-went-wrong"));
  }
}

async function updateHousehold() {
  // Note: auth.user is now a ref
  const { data } = await adminApi.households.getOne(auth.user.value!.householdId);
  if (!data || !data.preferences) {
    alert.error(i18n.t("events.something-went-wrong"));
    return;
  }

  const preferences = {
    ...data.preferences,
    privateHousehold: !commonSettings.value.makeGroupRecipesPublic,
    recipePublic: commonSettings.value.makeGroupRecipesPublic,
  };

  const payload = {
    ...data,
    preferences,
  };

  // Note: auth.user is now a ref
  const { response } = await adminApi.households.updateOne(auth.user.value!.householdId, payload);
  if (!response || response.status !== 200) {
    alert.error(i18n.t("events.something-went-wrong"));
  }
}

async function seedFoods() {
  const { response } = await userApi.seeders.foods({ locale: locale.value });
  if (!response || response.status !== 200) {
    alert.error(i18n.t("events.something-went-wrong"));
  }
}

async function seedUnits() {
  const { response } = await userApi.seeders.units({ locale: locale.value });
  if (!response || response.status !== 200) {
    alert.error(i18n.t("events.something-went-wrong"));
  }
}

async function seedData() {
  if (!commonSettings.value.useSeedData) {
    return;
  }

  await Promise.all([seedFoods(), seedUnits()]);
}

async function submitCommonSettings() {
  const tasks = [
    updateGroup(),
    updateHousehold(),
    seedData(),
  ];

  await Promise.all(tasks);
}

async function submitAll() {
  // Not part of the parallel batch: changing the password invalidates the session and establishes a
  // new one, and any request landing in that window would 401 and bounce the admin out of setup.
  await submitRegistration();

  const tasks = [
    submitCommonSettings(),
    groupActions.updateAIProviderSettings(),
  ];

  await Promise.all(tasks);
}

async function handleSubmit(page: number) {
  if (isSubmitting.value) {
    return;
  }

  isSubmitting.value = true;
  switch (page) {
    case Pages.USER_INFO:
      if (await accountDetails.validate()) {
        currentPage.value += 1;
      }
      break;
    case Pages.CONFIRM:
      await submitAll();
      currentPage.value += 1;
      break;
    case Pages.END:
      router.push(groupSlug.value ? `/g/${groupSlug.value}` : "/login");
      break;
  }
  isSubmitting.value = false;
}

// ================================================================
// Stepper Navigation Handlers
function onPrev() {
  if (isSubmitting.value) return;
  if (currentPage.value > Pages.LANDING) currentPage.value -= 1;
}

async function onNext() {
  if (isSubmitting.value) return;
  if (currentPage.value === Pages.USER_INFO) {
    await handleSubmit(Pages.USER_INFO);
    return;
  }
  if (currentPage.value === Pages.CONFIRM) {
    await handleSubmit(Pages.CONFIRM);
    return;
  }
  currentPage.value += 1;
}

async function onFinish() {
  if (isSubmitting.value) return;
  await handleSubmit(Pages.END);
}
</script>
