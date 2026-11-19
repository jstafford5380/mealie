<template>
  <AuthFrame
    :title="$t('user.reset-password')"
    :description="$t('user.please-enter-password')"
    :links="false"
  >
    <p
      v-if="token === ''"
      class="m-0 mb-4 rounded-control border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
    >
      {{ $t("user.reset-link-missing-token") }}
    </p>
    <form
      class="flex flex-col gap-2"
      @submit.prevent="requestLink()"
    >
      <TextField
        v-model="state.email"
        autofocus
        name="login"
        type="email"
        autocomplete="email"
        :label="$t('user.email')"
      />
      <TextField
        v-model="state.password"
        name="password"
        type="password"
        autocomplete="new-password"
        :label="$t('user.password')"
        :rules="[validators.required]"
      />
      <TextField
        v-model="state.passwordConfirm"
        name="password-confirm"
        type="password"
        autocomplete="new-password"
        validate-on="blur"
        :label="$t('user.confirm-password')"
        :rules="[validators.required, passwordMatch]"
      />
      <Button
        type="submit"
        size="lg"
        class="mt-2 w-full"
        :disabled="state.loading || token === ''"
      >
        <LoaderCircleIcon
          v-if="state.loading"
          class="size-4 animate-spin"
        />
        {{ $t("user.reset-password") }}
      </Button>
    </form>
    <p class="m-0 mt-6 flex flex-wrap justify-center gap-x-6 gap-y-1 border-t pt-5 text-[15px]">
      <NuxtLink
        v-if="state.linkInvalid || token === ''"
        to="/forgot-password"
        class="font-semibold text-primary no-underline hover:underline"
      >
        {{ $t("user.request-new-link") }}
      </NuxtLink>
      <NuxtLink
        to="/login"
        class="font-semibold text-primary no-underline hover:underline"
      >
        {{ $t("user.back-to-sign-in") }}
      </NuxtLink>
    </p>
  </AuthFrame>
</template>

<script setup lang="ts">
import { LoaderCircleIcon } from "@lucide/vue";
import AuthFrame from "~/components/Layout/LayoutParts/AuthFrame.vue";
import { Button } from "~/components/ui/button";
import TextField from "~/components/ui/field/TextField.vue";
import { provideFieldGroup } from "~/composables/forms/use-field-validation";
import { useUserApi } from "~/composables/api";
import { alert } from "~/composables/use-toast";
import { validators } from "@/composables/use-validators";
import { useRouteQuery } from "~/composables/use-router";

definePageMeta({
  layout: "blank",
});

const state = reactive({
  email: "",
  password: "",
  passwordConfirm: "",
  loading: false,
  error: false,
  linkInvalid: false,
});

const form = provideFieldGroup();

const i18n = useI18n();
const passwordMatch = () => state.password === state.passwordConfirm || i18n.t("user.password-must-match");

// Set page title
useSeoMeta({
  title: i18n.t("user.login"),
});

// ===================
// Token Getter
const token = useRouteQuery("token", "");

// ===================
// API
const api = useUserApi();
async function requestLink() {
  const { valid } = await form.validate();
  if (!valid) {
    return;
  };

  state.loading = true;
  const { response, error } = await api.users.resetPassword({
    token: token.value,
    email: state.email,
    password: state.password,
    passwordConfirm: state.passwordConfirm,
  });

  state.loading = false;

  if (response?.status === 200) {
    state.error = false;
    alert.success(i18n.t("user.password-updated"));
    await navigateTo("/login");
  }
  else if (error?.response?.status === 400) {
    state.error = true;
    state.linkInvalid = true;
    alert.error(i18n.t("user.reset-link-invalid"));
  }
  else {
    state.error = true;
    alert.error(i18n.t("events.something-went-wrong"));
  }
}
</script>

<style lang="css">
.max-button {
  width: 300px;
}
</style>
