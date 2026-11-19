<template>
  <div
    v-if="reverseProxyLoggingIn"
    class="flex min-h-dvh items-center justify-center bg-background"
    role="status"
    :aria-label="$t('general.loading')"
  >
    <LoaderCircleIcon class="size-12 animate-spin text-primary" />
  </div>
  <AuthFrame
    v-else
    :title="$t('user.sign-in')"
  >
    <template
      v-if="isFirstLogin"
      #above
    >
      <!-- the default admin account, shown until its email is changed -->
      <div class="rounded-card border border-primary/30 bg-primary/8 p-4 text-[15px]">
        <p class="m-0 mb-3">
          {{ $t('user.it-looks-like-this-is-your-first-time-logging-in') }}
        </p>
        <dl class="m-0 grid grid-cols-[auto_1fr_auto] items-center gap-x-3 gap-y-1">
          <dt class="font-semibold">
            {{ $t('user.username') }}
          </dt>
          <dd class="m-0 font-mono text-sm">
            changeme@example.com
          </dd>
          <dd class="m-0">
            <AppButtonCopy copy-text="changeme@example.com" />
          </dd>
          <dt class="font-semibold">
            {{ $t('user.password') }}
          </dt>
          <dd class="m-0 font-mono text-sm">
            MyPassword
          </dd>
          <dd class="m-0">
            <AppButtonCopy copy-text="MyPassword" />
          </dd>
        </dl>
        <p class="m-0 mt-3 text-sm text-muted-foreground">
          {{ $t('user.dont-want-to-see-this-anymore-be-sure-to-change-your-email') }}
        </p>
      </div>
    </template>

    <form
      class="flex flex-col gap-2"
      @submit.prevent="authenticate"
    >
      <template v-if="$appInfo.allowPasswordLogin">
        <TextField
          id="username"
          v-model="form.email"
          autofocus
          autocomplete="username"
          name="username"
          type="text"
          :label="$t('user.email-or-username')"
        />
        <TextField
          id="password"
          v-model="form.password"
          autocomplete="current-password"
          name="password"
          type="password"
          :label="$t('user.password')"
        />
        <div class="flex items-center justify-between gap-3">
          <CheckboxField
            v-model="form.remember"
            :label="$t('user.remember-me')"
          />
          <NuxtLink
            to="/forgot-password"
            class="shrink-0 text-sm font-semibold text-primary no-underline hover:underline"
          >
            {{ $t('user.forgot-password') }}
          </NuxtLink>
        </div>
        <Button
          type="submit"
          size="lg"
          class="mt-2 w-full"
          :disabled="loggingIn || oidcLoggingIn"
        >
          <LoaderCircleIcon
            v-if="loggingIn"
            class="size-4 animate-spin"
          />
          {{ $t("user.login") }}
        </Button>
      </template>

      <div
        v-if="$appInfo.enableOidc && $appInfo.allowPasswordLogin"
        class="my-3 flex items-center gap-3 text-sm text-muted-foreground"
      >
        <span class="h-px flex-1 bg-border" />
        {{ $t("user.or") }}
        <span class="h-px flex-1 bg-border" />
      </div>
      <Button
        v-if="$appInfo.enableOidc"
        type="button"
        size="lg"
        :variant="$appInfo.allowPasswordLogin ? 'outline' : 'default'"
        class="w-full"
        :disabled="oidcLoggingIn"
        @click="() => oidcAuthenticate()"
      >
        <LoaderCircleIcon
          v-if="oidcLoggingIn"
          class="size-4 animate-spin"
        />
        {{ $t("user.login-oidc") }} {{ $appInfo.oidcProviderName }}
      </Button>
    </form>

    <p
      v-if="$appInfo.allowPasswordLogin"
      class="m-0 mt-6 border-t pt-5 text-center text-[15px] text-muted-foreground"
    >
      <template v-if="$appInfo.allowSignup">
        {{ $t('user.new-here') }}
        <NuxtLink
          to="/register"
          class="font-semibold text-primary no-underline hover:underline"
        >
          {{ $t("user.register") }}
        </NuxtLink>
      </template>
      <template v-else>
        {{ $t("user.invite-only-explained") }}
      </template>
    </p>
  </AuthFrame>
</template>

<script setup lang="ts">
import { LoaderCircleIcon } from "@lucide/vue";
import { useSessionStorage, whenever } from "@vueuse/core";
import AuthFrame from "~/components/Layout/LayoutParts/AuthFrame.vue";
import { Button } from "~/components/ui/button";
import CheckboxField from "~/components/ui/field/CheckboxField.vue";
import TextField from "~/components/ui/field/TextField.vue";
import { useLoggedInState } from "~/composables/use-logged-in-state";
import { alert } from "~/composables/use-toast";
import { useAsyncKey } from "~/composables/use-utils";
import { isSafeRedirectTarget } from "~/lib/validators/redirect";
import type { AppStartupInfo } from "~/lib/api/types/admin";
import { useUserActivityPreferences } from "~/composables/use-users/preferences";

definePageMeta({
  layout: "blank",
});

const router = useRouter();
const route = useRoute();
const i18n = useI18n();
const auth = useMealieAuth();
const { $appInfo, $axios } = useNuxtApp();
const { loggedIn } = useLoggedInState();
const groupSlug = computed(() => auth.user.value?.groupSlug);
const isDemo = ref(false);
const isFirstLogin = ref(false);
const activityPreferences = useUserActivityPreferences();
const { getDefaultActivityRoute } = useDefaultActivity();

// Survives the page reload that happens during OIDC redirect
const pendingShareRedirect = useSessionStorage<string | null>("pwa_share_redirect", null);

useSeoMeta({
  title: i18n.t("user.login"),
});

const form = reactive({
  email: "",
  password: "",
  // Defaults on: this is a self-hosted app people mostly reach from their own devices, and an
  // unticked box now ends the session when the browser closes.
  // Ideally this is off by default, but we've trained users for years to ignore this checkbox,
  // so turning it off would cause a headache for the majority of users.
  // Maybe we can revisit this in the future.
  remember: true,
});

useAsyncData(useAsyncKey(), async () => {
  const data = await $axios.get<AppStartupInfo>("/api/app/about/startup-info");
  isDemo.value = data.data.isDemo;
  isFirstLogin.value = data.data.isFirstLogin;

  if (data.data.isFirstLogin) {
    form.email = "changeme@example.com";
    form.password = "MyPassword";
  }
});

whenever(
  () => loggedIn.value && groupSlug.value,
  () => {
    // First-login setup always takes priority
    if (!isDemo.value && isFirstLogin.value && auth.user.value?.admin) {
      router.push("/admin/setup");
      return;
    }

    // After login, honour a pending PWA share redirect.
    // The redirect param can arrive via the URL query string (password login)
    // or via sessionStorage (OIDC login, where the OIDC provider reload clears
    // the query string).
    const redirectFromQuery = route.query.redirect as string | undefined;
    const redirectTarget = redirectFromQuery ?? pendingShareRedirect.value;
    if (isSafeRedirectTarget(redirectTarget)) {
      pendingShareRedirect.value = null;
      router.push(redirectTarget);
      return;
    }

    const defaultActivityRoute = getDefaultActivityRoute(
      activityPreferences.value.defaultActivity,
      groupSlug.value,
    );
    if (defaultActivityRoute) {
      router.push(defaultActivityRoute);
    }
    else {
      router.push(`/g/${groupSlug.value || ""}`);
    }
  },
  { immediate: true },
);

const loggingIn = ref(false);
const oidcLoggingIn = ref(false);
const reverseProxyLoggingIn = ref($appInfo.enableReverseProxyAuth && !isDirectLogin());

whenever(
  () => $appInfo.enableOidc && $appInfo.oidcRedirect && !isCallback() && !isDirectLogin() /* && !auth.check().valid */,
  () => oidcAuthenticate(),
  { immediate: true },
);

onBeforeMount(async () => {
  if (isCallback()) {
    await oidcAuthenticate(true);
    // Failed callback redirects to ?direct=1 without reloading, so clear the spinner ourselves
    reverseProxyLoggingIn.value = false;
    return;
  }

  if ($appInfo.enableReverseProxyAuth && !isDirectLogin() && !loggedIn.value) {
    try {
      await auth.reverseProxySignIn();
    }
    catch {
      // Header missing/invalid - fall back to the regular login form
    }
  }
  reverseProxyLoggingIn.value = false;
});

function isCallback() {
  const params = new URLSearchParams(window.location.search);
  return params.has("code") || params.has("error");
}

function isDirectLogin() {
  const params = new URLSearchParams(window.location.search);
  return params.has("direct") && params.get("direct") === "1";
}

async function oidcAuthenticate(callback = false) {
  if (callback) {
    oidcLoggingIn.value = true;
    try {
      await auth.oauthSignIn();
    }
    catch (error) {
      await router.replace("/login?direct=1");
      alertOnError(error);
    }
    oidcLoggingIn.value = false;
  }
  else {
    // Save any pending PWA share redirect before leaving for the OIDC provider.
    // The OIDC callback reloads the page, which clears the query string, so we
    // persist the target in sessionStorage and restore it after login.
    const redirectTarget = route.query.redirect as string | undefined;
    if (isSafeRedirectTarget(redirectTarget)) {
      pendingShareRedirect.value = redirectTarget;
    }
    navigateTo("/api/auth/oauth", { external: true }); // start the redirect process
  }
}

async function authenticate() {
  if (form.email.length === 0 || form.password.length === 0) {
    alert.error(i18n.t("user.please-enter-your-email-and-password"));
    return;
  }

  loggingIn.value = true;
  const formData = new FormData();
  formData.append("username", form.email);
  formData.append("password", form.password);
  formData.append("remember_me", String(form.remember));

  try {
    await auth.signIn(formData);
  }
  catch (error) {
    alertOnError(error);
  }
  loggingIn.value = false;
}

function alertOnError(error: any) {
  // TODO Check if error is an AxiosError, but isAxiosError is not working right now
  // See https://github.com/nuxt-community/axios-module/issues/550
  // Import $axios from useContext()
  // if ($axios.isAxiosError(error) && error.response?.status === 401) {
  if (error.response?.status === 401) {
    alert.error(i18n.t("user.invalid-credentials"));
  }
  else if (error.response?.status === 423) {
    alert.error(i18n.t("user.account-locked-please-try-again-later"));
  }
  else {
    alert.error(i18n.t("events.something-went-wrong"));
  }
}
</script>
