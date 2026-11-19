<template>
  <AuthFrame
    wide
    :links="false"
  >
    <!-- Step 1: how are you joining? -->
    <template v-if="state.ctx.state === States.Initial">
      <h1 class="m-0 text-[26px] font-bold tracking-tight">
        {{ $t("user-registration.user-registration") }}
      </h1>
      <p class="m-0 mt-1.5 text-[15px] text-muted-foreground">
        {{ $t("user-registration.how-are-you-joining") }}
      </p>
      <div class="mt-6 grid gap-3 sm:grid-cols-2">
        <button
          v-for="option in startOptions"
          :key="option.key"
          type="button"
          class="group flex flex-col items-start gap-3 rounded-card border bg-card p-5 text-start transition-colors hover:border-primary/50 hover:bg-primary/5 focus-visible:outline-2 focus-visible:outline-ring"
          @click="option.action"
        >
          <span class="inline-flex size-11 items-center justify-center rounded-full bg-subtle text-subtle-foreground group-hover:bg-primary group-hover:text-primary-foreground">
            <MdiIcon
              :path="$globals.icons[option.icon]"
              class="size-5"
            />
          </span>
          <span class="text-[17px] font-semibold">{{ option.title }}</span>
          <span class="text-sm text-muted-foreground">{{ option.description }}</span>
        </button>
      </div>
    </template>

    <template v-else>
      <p class="m-0 mb-1 text-sm font-semibold text-muted-foreground">
        {{ $t("user-registration.step-of", { step: stepNumber, total: stepTotal }) }}
      </p>
      <h1 class="m-0 text-[26px] font-bold tracking-tight">
        {{ stepTitle }}
      </h1>
      <p
        v-if="stepDescription"
        class="m-0 mt-1.5 text-[15px] text-muted-foreground"
      >
        {{ stepDescription }}
      </p>

      <form
        class="mt-6"
        @submit.prevent="onNext"
      >
        <!-- Invite code -->
        <TextField
          v-if="state.ctx.state === States.ProvideToken"
          v-model="token"
          autofocus
          validate-on="blur"
          :label="$t('group.group-token')"
          :rules="[validators.required]"
        />

        <!-- New group -->
        <div
          v-else-if="state.ctx.state === States.ProvideGroupDetails"
          class="flex flex-col gap-2"
        >
          <TextField
            v-model="groupDetails.groupName.value"
            autofocus
            validate-on="blur"
            :label="$t('group.group-name')"
            :rules="[validators.required]"
            :error-messages="groupErrorMessages"
            @blur="validGroupName"
          />
          <CheckboxField
            v-model="groupDetails.groupPrivate.value"
            :label="$t('group.settings.keep-my-recipes-private')"
            :hint="$t('group.settings.keep-my-recipes-private-description')"
          />
          <CheckboxField
            v-model="groupDetails.groupSeed.value"
            :label="$t('data-pages.seed-data')"
            :hint="$t('user-registration.use-seed-data-description')"
          />
        </div>

        <!-- Account -->
        <UserRegistrationForm
          v-else-if="state.ctx.state === States.ProvideAccountDetails"
          v-model="isAccountFormValid"
        />

        <!-- Review -->
        <dl
          v-else-if="state.ctx.state === States.Confirmation"
          class="m-0 divide-y rounded-card border"
        >
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

        <div class="mt-8 flex items-center justify-between gap-3 border-t pt-5">
          <Button
            type="button"
            variant="ghost"
            @click="state.back"
          >
            <ChevronLeftIcon class="size-4 rtl:rotate-180" />
            {{ $t("general.back") }}
          </Button>
          <Button
            type="submit"
            :disabled="!canContinue"
          >
            {{ state.ctx.state === States.Confirmation ? $t("user-registration.create-account") : $t("general.next") }}
            <ChevronRightIcon
              v-if="state.ctx.state !== States.Confirmation"
              class="size-4 rtl:rotate-180"
            />
          </Button>
        </div>
      </form>
    </template>

    <template #below>
      <div class="flex flex-wrap items-center justify-between gap-3 text-[15px] text-muted-foreground">
        <span>
          {{ $t("user-registration.already-have-account") }}
          <NuxtLink
            to="/login"
            class="font-semibold text-primary no-underline hover:underline"
          >
            {{ $t("user.sign-in") }}
          </NuxtLink>
        </span>
        <Button
          variant="ghost"
          @click="langDialog = true"
        >
          <MdiIcon
            :path="$globals.icons.translate"
            class="size-4"
          />
          {{ $t("language-dialog.choose-language") }}
        </Button>
      </div>
      <LanguageDialog v-model="langDialog" />
    </template>
  </AuthFrame>
</template>

<script setup lang="ts">
import { ChevronLeftIcon, ChevronRightIcon } from "@lucide/vue";
import AuthFrame from "~/components/Layout/LayoutParts/AuthFrame.vue";
import { Button } from "~/components/ui/button";
import CheckboxField from "~/components/ui/field/CheckboxField.vue";
import TextField from "~/components/ui/field/TextField.vue";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { provideFieldGroup } from "~/composables/forms/use-field-validation";
import { States, RegistrationType, useRegistration } from "./states";
import { useUserRegistrationForm } from "~/composables/use-users/user-registration-form";
import { useRouteQuery } from "~/composables/use-router";
import { validators, useAsyncValidator } from "~/composables/use-validators";
import { useUserApi } from "~/composables/api";
import { alert } from "~/composables/use-toast";
import type { UserRegistrationCreate } from "~/lib/api/types/user";
import { usePublicApi } from "~/composables/api/api-client";
import { useLocales } from "~/composables/use-locales";
import UserRegistrationForm from "~/components/Domain/User/UserRegistrationForm.vue";

definePageMeta({
  layout: "blank",
});

const i18n = useI18n();
// Fields in every step register here; the account step adds its own group inside it
const pageForm = provideFieldGroup();

// Registration Context
const state = useRegistration();

// Handle Token URL / Initialization
const token = useRouteQuery("token");
function initialUser() {
  return false;
}
onMounted(() => {
  if (token.value) {
    state.setState(States.ProvideAccountDetails);
    state.setType(RegistrationType.JoinGroup);
  }
  if (initialUser()) {
    state.setState(States.ProvideGroupDetails);
    state.setType(RegistrationType.InitialGroup);
  }
});

// Initial
const initial = {
  createGroup: () => {
    state.setState(States.ProvideGroupDetails);
    state.setType(RegistrationType.CreateGroup);
    if (token.value != null) {
      token.value = null;
    }
  },
  joinGroup: () => {
    state.setState(States.ProvideToken);
    state.setType(RegistrationType.JoinGroup);
  },
};

// Provide Token
const domTokenForm = ref(pageForm);
function validateToken() {
  return Boolean(token.value && token.value.trim());
}
const isTokenValid = computed(() => validateToken());
const provideToken = {
  next: async () => {
    if (!await safeValidate(domTokenForm as any)) {
      return;
    }
    if (validateToken()) {
      state.setState(States.ProvideAccountDetails);
    }
  },
};

// Provide Group Details
const publicApi = usePublicApi();
const isGroupFormValid = computed(() => pageForm.isValid.value === true);
const groupName = ref("");
const groupSeed = ref(false);
const groupPrivate = ref(false);
const groupErrorMessages = ref<string[]>([]);
const { validate: validGroupName, valid: groupNameValid } = useAsyncValidator(
  groupName,
  (v: string) => publicApi.validators.group(v),
  i18n.t("validation.group-name-is-taken"),
  groupErrorMessages,
);
async function validateGroup() {
  if (!groupName.value || !groupName.value.trim()) {
    groupErrorMessages.value = [i18n.t("validators.required")];
    return false;
  }
  groupErrorMessages.value = [];
  await validGroupName();

  if (!groupNameValid.value) {
    return false;
  }

  return true;
}
const groupDetails = {
  groupName,
  groupSeed,
  groupPrivate,
  next: async () => {
    if (!await validateGroup()) {
      return;
    }
    state.setState(States.ProvideAccountDetails);
  },
};

const isAccountFormValid = ref(false);
const {
  accountDetails,
  credentials,
  safeValidate,
} = useUserRegistrationForm();
async function accountDetailsNext() {
  if (!await accountDetails.validate()) {
    return;
  }
  state.setState(States.Confirmation);
}

// Step layout
const startOptions = computed(() => [
  {
    key: "join",
    icon: "group",
    title: i18n.t("user-registration.join-a-group"),
    description: i18n.t("user-registration.join-a-group-description"),
    action: initial.joinGroup,
  },
  {
    key: "create",
    icon: "user",
    title: i18n.t("user-registration.create-a-new-group"),
    description: i18n.t("user-registration.create-a-new-group-description"),
    action: initial.createGroup,
  },
]);

const stepOrder = computed(() => (state.ctx.type === RegistrationType.CreateGroup
  ? [States.ProvideGroupDetails, States.ProvideAccountDetails, States.Confirmation]
  : [States.ProvideToken, States.ProvideAccountDetails, States.Confirmation]));
const stepNumber = computed(() => Math.max(1, stepOrder.value.indexOf(state.ctx.state) + 1));
const stepTotal = computed(() => stepOrder.value.length);

const stepTitle = computed(() => {
  switch (state.ctx.state) {
    case States.ProvideToken: return i18n.t("user-registration.join-a-group");
    case States.ProvideGroupDetails: return i18n.t("user-registration.group-details");
    case States.ProvideAccountDetails: return i18n.t("user-registration.account-details");
    default: return i18n.t("user-registration.review-and-create");
  }
});
const stepDescription = computed(() => {
  switch (state.ctx.state) {
    case States.ProvideToken: return i18n.t("user-registration.provide-registration-token-description");
    case States.ProvideGroupDetails: return i18n.t("user-registration.group-details-description");
    default: return "";
  }
});

const canContinue = computed(() => {
  switch (state.ctx.state) {
    case States.ProvideToken: return isTokenValid.value;
    case States.ProvideGroupDetails: return isGroupFormValid.value && groupNameValid.value;
    case States.ProvideAccountDetails: return isAccountFormValid.value;
    default: return true;
  }
});

function onNext() {
  if (!canContinue.value) {
    return;
  }
  switch (state.ctx.state) {
    case States.ProvideToken: return provideToken.next();
    case States.ProvideGroupDetails: return groupDetails.next();
    case States.ProvideAccountDetails: return accountDetailsNext();
    case States.Confirmation: return submitRegistration();
  }
}

// Locale
const { locale } = useLocales();
const langDialog = ref(false);

// Confirmation
const confirmationData = computed(() => {
  return [
    {
      display: state.ctx.type === RegistrationType.CreateGroup,
      text: i18n.t("group.group"),
      value: groupName.value,
    },
    {
      display: state.ctx.type === RegistrationType.CreateGroup,
      text: i18n.t("data-pages.seed-data"),
      value: groupSeed.value ? i18n.t("general.yes") : i18n.t("general.no"),
    },
    {
      display: state.ctx.type === RegistrationType.CreateGroup,
      text: i18n.t("group.settings.keep-my-recipes-private"),
      value: groupPrivate.value ? i18n.t("general.yes") : i18n.t("general.no"),
    },
    {
      display: true,
      text: i18n.t("user.email"),
      value: accountDetails.email.value,
    },
    {
      display: true,
      text: i18n.t("user.full-name"),
      value: accountDetails.fullName.value,
    },
    {
      display: true,
      text: i18n.t("user.username"),
      value: accountDetails.username.value,
    },
    {
      display: true,
      text: i18n.t("user.enable-advanced-content"),
      value: accountDetails.advancedOptions.value ? i18n.t("general.yes") : i18n.t("general.no"),
    },
  ];
});

const api = useUserApi();
const router = useRouter();
async function submitRegistration() {
  const payload: UserRegistrationCreate = {
    email: accountDetails.email.value,
    username: accountDetails.username.value,
    fullName: accountDetails.fullName.value,
    password: credentials.password1.value,
    passwordConfirm: credentials.password2.value,
    locale: locale.value,
    advanced: accountDetails.advancedOptions.value,
  };
  if (state.ctx.type === RegistrationType.CreateGroup) {
    payload.group = groupName.value;
    payload.private = groupPrivate.value;
    payload.seedData = groupSeed.value;
  }
  else {
    payload.groupToken = token.value;
  }
  const { response, error } = await api.register.register(payload);
  if (response?.status === 201) {
    accountDetails.reset();
    credentials.reset();
    alert.success(i18n.t("user-registration.registration-success"));
    router.push("/login");
  }
  // The Axios interceptor already shows detail.message errors.
  else if (!error?.response?.data?.detail?.message) {
    alert.error(i18n.t("events.something-went-wrong"));
  }
}
</script>
