<template>
  <AuthFrame
    :title="$t('user.forgot-password')"
    :description="$t('user.forgot-password-text')"
    :links="false"
  >
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
        :rules="[validators.email]"
      />
      <Button
        type="submit"
        size="lg"
        class="mt-2 w-full"
        :disabled="state.loading"
      >
        <LoaderCircleIcon
          v-if="state.loading"
          class="size-4 animate-spin"
        />
        {{ $t("user.reset-password") }}
      </Button>
    </form>
    <p class="m-0 mt-6 border-t pt-5 text-center text-[15px]">
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
import { validators } from "~/composables/use-validators";

definePageMeta({
  layout: "blank",
});

const form = provideFieldGroup();

const state = reactive({
  email: "",
  loading: false,
  error: false,
});

const i18n = useI18n();

// Set page title
useSeoMeta({
  title: i18n.t("user.forgot-password"),
});

const api = useUserApi();

async function requestLink() {
  const { valid } = await form.validate();
  if (!valid) {
    return;
  };

  state.loading = true;
  // TODO: Fix Response to send meaningful error
  const { response } = await api.email.sendForgotPassword({ email: state.email });

  state.loading = false;

  if (response?.status === 200) {
    state.error = false;
    alert.success(i18n.t("profile.email-sent"));
    await navigateTo("/login");
  }
  else {
    state.error = true;
    alert.error(i18n.t("profile.error-sending-email"));
  }
}
</script>

<style lang="css">
.max-button {
  width: 300px;
}
</style>
