<template>
  <div class="mx-auto flex w-full max-w-[860px] flex-col gap-8 px-4 pb-16 pt-3 font-sans sm:px-6 lg:pt-8">
    <!-- Bug Report -->
    <BaseDialog
      v-model="bugReportDialog"
      :title="$t('settings.bug-report')"
      :width="800"
      :icon="$globals.icons.github"
    >
      <div class="flex flex-col gap-3 px-6 pb-2">
        <p class="m-0 text-[15px] text-muted-foreground">
          {{ $t('settings.bug-report-information') }}
        </p>
        <textarea
          :value="bugReportText"
          readonly
          rows="16"
          :aria-label="$t('settings.bug-report')"
          class="w-full resize-y rounded-control border border-input bg-muted px-3 py-2 font-mono text-[12.5px] outline-none"
        />
        <div class="flex justify-end gap-2">
          <Button
            variant="ghost"
            @click="openTracker"
          >
            <MdiIcon
              :path="$globals.icons.github"
              class="size-4"
            />
            {{ $t('settings.tracker') }}
          </Button>
          <AppButtonCopy
            :copy-text="bugReportText"
            :icon="false"
          />
        </div>
      </div>
    </BaseDialog>

    <header class="-mb-2 flex flex-wrap items-end gap-3">
      <h1 class="m-0 flex-1 text-[26px] font-bold tracking-tight sm:text-[32px]">
        {{ $t("settings.site-settings") }}
      </h1>
      <Button
        variant="outline"
        @click="bugReportDialog = true"
      >
        <MdiIcon
          :path="$globals.icons.github"
          class="size-4"
        />
        {{ $t('settings.bug-report') }}
      </Button>
    </header>

    <!-- Site Statistics -->
    <section>
      <h2 class="m-0 mb-3 text-base font-semibold">
        {{ $t('settings.site-statistics') }}
      </h2>
      <div class="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
        <NuxtLink
          v-for="(value, key) in adminStats"
          :key="key"
          :to="getAdminStatsTo(key)"
          class="flex flex-col gap-1 rounded-card border bg-card px-4 py-3 text-foreground no-underline transition-colors hover:border-primary/50"
        >
          <span class="flex items-center gap-1.5 text-sm text-muted-foreground">
            <MdiIcon
              :path="getAdminStatsIcon(key)"
              class="size-4"
            />
            {{ getAdminStatsTitle(key) }}
          </span>
          <span class="text-[26px] font-bold tabular-nums">{{ value }}</span>
        </NuxtLink>
      </div>
    </section>

    <!-- Configuration -->
    <section>
      <h2 class="m-0 mb-3 text-base font-semibold">
        {{ $t('settings.configuration') }}
      </h2>
      <ul class="m-0 flex list-none flex-col divide-y rounded-card border bg-card p-0">
        <li
          v-for="(check, idx) in simpleChecks"
          :key="idx"
          class="flex items-start gap-3 px-4 py-3"
        >
          <MdiIcon
            :path="check.icon"
            class="mt-0.5 size-5 shrink-0"
            :class="STATUS_TEXT[check.color] || 'text-muted-foreground'"
          />
          <span class="min-w-0">
            <span class="block font-semibold">{{ check.text }}</span>
            <span class="block text-sm break-words text-muted-foreground">{{ check.status ? check.successText : check.errorText }}</span>
          </span>
        </li>
      </ul>
    </section>

    <!-- Email -->
    <section class="rounded-panel border bg-card p-5 sm:p-6">
      <div class="mb-3 flex items-center gap-3">
        <MdiIcon
          :path="appConfig.emailReady ? $globals.icons.checkboxMarkedCircle : $globals.icons.alertCircle"
          class="size-5 shrink-0"
          :class="appConfig.emailReady ? 'text-primary' : 'text-brand-strong'"
        />
        <h2 class="m-0 flex-1 text-xl font-bold tracking-tight">
          {{ $t('settings.email-configuration-status') }}
        </h2>
        <span
          class="rounded-full px-2.5 py-0.5 text-xs font-semibold"
          :class="appConfig.emailReady ? 'bg-primary/15 text-primary' : 'bg-brand/20 text-brand-strong'"
        >{{ appConfig.emailReady ? $t('settings.ready') : $t('settings.not-ready') }}</span>
      </div>
      <form
        class="flex flex-wrap items-end gap-3"
        @submit.prevent="testEmail"
      >
        <div class="min-w-0 flex-1 basis-60">
          <TextField
            v-model="state.address"
            type="email"
            :label="$t('settings.send-test-email-to')"
            :rules="[validators.email]"
          />
        </div>
        <Button
          type="submit"
          variant="outline"
          class="mb-1.5"
          :disabled="!appConfig.emailReady || !validEmail || state.loading"
        >
          <LoaderCircleIcon
            v-if="state.loading"
            class="size-4 animate-spin"
          />
          <MdiIcon
            v-else
            :path="$globals.icons.email"
            class="size-4"
          />
          {{ $t("general.test") }}
        </Button>
      </form>
      <p
        v-if="state.tested"
        class="m-0 mt-2 text-sm"
        :class="state.success ? 'text-primary' : 'text-destructive'"
        role="status"
      >
        {{ $t("settings.email-test-results") }}: {{ state.success ? $t('settings.succeeded') : $t('settings.failed') }}
      </p>
    </section>

    <!-- General App Info -->
    <section>
      <h2 class="m-0 mb-3 text-base font-semibold">
        {{ $t('settings.general-about') }}
      </h2>
      <dl
        v-if="appInfo && appInfo.length"
        class="m-0 divide-y rounded-card border bg-card"
      >
        <div
          v-for="property in appInfo"
          :key="property.name"
          class="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-0.5 px-4 py-3"
        >
          <dt class="flex items-center gap-2 text-sm text-muted-foreground">
            <MdiIcon
              :path="property.icon || $globals.icons.user"
              class="size-4"
            />
            {{ property.name }}
          </dt>
          <dd class="m-0 font-semibold break-all">
            <a
              v-if="propertyLink(property)"
              :href="propertyLink(property)"
              target="_blank"
              rel="noopener"
              class="text-primary no-underline hover:underline"
            >{{ property.value }}</a>
            <template v-else>
              {{ property.value }}
            </template>
          </dd>
        </div>
      </dl>
      <AppLoader v-else />
    </section>
  </div>
</template>

<script setup lang="ts">
import { LoaderCircleIcon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import TextField from "~/components/ui/field/TextField.vue";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { useAdminApi, useUserApi } from "~/composables/api";
import { validators } from "~/composables/use-validators";
import { useAsyncKey } from "~/composables/use-utils";
import type { AppStatistics, CheckAppConfig } from "~/lib/api/types/admin";
import AppLoader from "~/components/global/AppLoader.vue";

interface SimpleCheck {
  id: string;
  text: string;
  status: boolean | undefined;
  successText: string;
  errorText: string;
  color: string;
  icon: string;
}

interface CheckApp extends CheckAppConfig {
  isSiteSecure?: boolean;
}

definePageMeta({
  layout: "admin",
});

// For some reason the layout is not set automatically, so we set it here,
// even though it's defined above in the page meta.
onMounted(() => {
  setPageLayout("admin");
});

const { $globals } = useNuxtApp();
const i18n = useI18n();

const state = reactive({
  loading: false,
  address: "",
  success: false,
  error: "",
  tested: false,
});

// Set page title
useSeoMeta({
  title: i18n.t("settings.site-settings"),
});

const appConfig = ref<CheckApp>({
  emailReady: true,
  baseUrlSet: true,
  isSiteSecure: true,
  isUpToDate: false,
  ldapReady: false,
  ldapDisabled: false,
  oidcReady: false,
  oidcDisabled: false,
  reverseProxyAuthReady: false,
  reverseProxyAuthDisabled: false,
});
const adminStats = ref<AppStatistics>({
  totalRecipes: 0,
  totalUsers: 0,
  totalHouseholds: 0,
  totalGroups: 0,
  uncategorizedRecipes: 0,
  untaggedRecipes: 0,
});
function isLocalHostOrHttps() {
  return window.location.hostname === "localhost" || window.location.protocol === "https:";
}
const api = useUserApi();
const adminApi = useAdminApi();

const adminStatsText: { [key: string]: string } = {
  totalRecipes: i18n.t("general.recipes"),
  totalUsers: i18n.t("user.users"),
  totalHouseholds: i18n.t("household.households"),
  totalGroups: i18n.t("group.groups"),
  uncategorizedRecipes: i18n.t("settings.uncategorized-recipes"),
  untaggedRecipes: i18n.t("settings.untagged-recipes"),
};

function getAdminStatsTitle(key: string) {
  return adminStatsText[key] ?? key;
}

const adminStatsIcon: { [key: string]: string } = {
  totalRecipes: $globals.icons.primary,
  totalUsers: $globals.icons.user,
  totalHouseholds: $globals.icons.household,
  totalGroups: $globals.icons.group,
  uncategorizedRecipes: $globals.icons.categories,
  untaggedRecipes: $globals.icons.tags,
};

function getAdminStatsIcon(key: string) {
  return adminStatsIcon[key] ?? $globals.icons.primary;
}

const adminStatsTo = computed<{ [key: string]: string }>(() => {
  return {
    totalUsers: "/admin/manage/users",
    totalHouseholds: "/admin/manage/households",
    totalGroups: "/admin/manage/groups",
  };
});

function getAdminStatsTo(key: string) {
  return adminStatsTo.value[key] ?? undefined;
}

onMounted(async () => {
  const { data } = await adminApi.about.checkApp();
  if (data) {
    appConfig.value = { ...data, isSiteSecure: false };
  }
  appConfig.value.isSiteSecure = isLocalHostOrHttps();
  const { data: adminData } = await adminApi.about.statistics();
  if (adminData) {
    adminStats.value = adminData;
  }
});
const goodIcon = $globals.icons.checkboxMarkedCircle;
const badIcon = $globals.icons.alert;
const warningIcon = $globals.icons.alertCircle;
const disabledIcon = $globals.icons.minusCircle;
const goodColor = "success";
const badColor = "error";
const warningColor = "warning";
const disabledColor = "grey";

// Auth providers (LDAP, OIDC) have three states rather than two: turned off
// entirely, enabled and fully configured, or enabled but missing configuration.
// When a provider is disabled its incomplete configuration isn't a problem, so
// it's reported neutrally instead of as a warning.
interface AuthProvider {
  id: string;
  // Shown as-is rather than translated, since these are acronyms
  name: string;
  // The environment variable that turns the provider on
  envVar: string;
  ready: boolean;
  disabled: boolean;
}

function authCheckText({ name, ready, disabled }: AuthProvider): string {
  if (disabled) {
    return i18n.t("settings.auth-provider-disabled", { provider: name });
  }
  return ready
    ? i18n.t("settings.auth-provider-ready", { provider: name })
    : i18n.t("settings.auth-provider-not-ready", { provider: name });
}

function authCheckColor({ ready, disabled }: AuthProvider): string {
  if (disabled) {
    return disabledColor;
  }
  return ready ? goodColor : warningColor;
}

function authCheckIcon({ ready, disabled }: AuthProvider): string {
  if (disabled) {
    return disabledIcon;
  }
  return ready ? goodIcon : warningIcon;
}

function authProviderCheck(provider: AuthProvider): SimpleCheck {
  return {
    id: provider.id,
    text: authCheckText(provider),
    status: provider.ready,
    errorText: provider.disabled
      ? i18n.t("settings.auth-provider-disabled-text", { envVar: provider.envVar })
      : i18n.t("settings.auth-provider-error-text", { provider: provider.name }),
    successText: i18n.t("settings.auth-provider-success-text", { provider: provider.name }),
    color: authCheckColor(provider),
    icon: authCheckIcon(provider),
  };
}

const simpleChecks = computed<SimpleCheck[]>(() => {
  const data: SimpleCheck[] = [
    {
      id: "application-version",
      text: i18n.t("settings.application-version"),
      status: appConfig.value.isUpToDate,
      errorText: i18n.t("settings.application-version-error-text", [rawAppInfo.value.version, rawAppInfo.value.versionLatest]),
      successText: i18n.t("settings.mealie-is-up-to-date"),
      color: appConfig.value.isUpToDate ? goodColor : warningColor,
      icon: appConfig.value.isUpToDate ? goodIcon : warningIcon,
    },
    {
      id: "secure-site",
      text: i18n.t("settings.secure-site"),
      status: appConfig.value.isSiteSecure,
      errorText: i18n.t("settings.secure-site-error-text"),
      successText: i18n.t("settings.secure-site-success-text"),
      color: appConfig.value.isSiteSecure ? goodColor : badColor,
      icon: appConfig.value.isSiteSecure ? goodIcon : badIcon,
    },
    {
      id: "server-side-base-url",
      text: i18n.t("settings.server-side-base-url"),
      status: appConfig.value.baseUrlSet,
      errorText: i18n.t("settings.server-side-base-url-error-text"),
      successText: i18n.t("settings.server-side-base-url-success-text"),
      color: appConfig.value.baseUrlSet ? goodColor : badColor,
      icon: appConfig.value.baseUrlSet ? goodIcon : badIcon,
    },
    authProviderCheck({
      id: "ldap-ready",
      name: "LDAP",
      envVar: "LDAP_AUTH_ENABLED",
      ready: appConfig.value.ldapReady,
      disabled: appConfig.value.ldapDisabled,
    }),
    authProviderCheck({
      id: "oidc-ready",
      name: "OIDC",
      envVar: "OIDC_AUTH_ENABLED",
      ready: appConfig.value.oidcReady,
      disabled: appConfig.value.oidcDisabled,
    }),
    authProviderCheck({
      id: "reverse-proxy-auth-ready",
      name: "Reverse Proxy",
      envVar: "REVERSE_PROXY_AUTH_ENABLED",
      ready: appConfig.value.reverseProxyAuthReady,
      disabled: appConfig.value.reverseProxyAuthDisabled,
    }),
  ];
  return data;
});
async function testEmail() {
  state.loading = true;
  state.tested = false;
  const { data } = await api.email.test({ email: state.address });
  if (data) {
    if (data.success) {
      state.success = true;
    }
    else {
      state.error = data.error ?? "";
      state.success = false;
    }
  }
  state.loading = false;
  state.tested = true;
}
const validEmail = computed(() => {
  if (state.address === "") {
    return false;
  }
  const valid = validators.email(state.address);
  // Explicit bool check because validators.email sometimes returns a string
  if (valid === true) {
    return true;
  }
  return false;
});
// ============================================================
// General About Info
const rawAppInfo = ref({
  version: "null",
  versionLatest: "null",
});
function getAppInfo() {
  const { data: statistics } = useAsyncData(useAsyncKey(), async () => {
    const { data } = await adminApi.about.about();
    if (data) {
      rawAppInfo.value.version = data.version;
      rawAppInfo.value.versionLatest = data.versionLatest;
      const prettyInfo = [
        {
          slot: "version",
          name: i18n.t("about.version"),
          icon: $globals.icons.information,
          value: data.version,
        },
        {
          slot: "build",
          name: i18n.t("settings.build"),
          icon: $globals.icons.information,
          value: data.buildId,
        },
        {
          name: i18n.t("about.application-mode"),
          icon: $globals.icons.devTo,
          value: data.production ? i18n.t("about.production") : i18n.t("about.development"),
        },
        {
          name: i18n.t("about.demo-status"),
          icon: $globals.icons.testTube,
          value: data.demoStatus ? i18n.t("about.demo") : i18n.t("about.not-demo"),
        },
        {
          name: i18n.t("about.api-port"),
          icon: $globals.icons.api,
          value: data.apiPort,
        },
        {
          name: i18n.t("about.api-docs"),
          icon: $globals.icons.file,
          value: data.apiDocs ? i18n.t("general.enabled") : i18n.t("general.disabled"),
        },
        {
          name: i18n.t("about.database-type"),
          icon: $globals.icons.database,
          value: data.dbType,
        },
        {
          name: i18n.t("about.database-url"),
          icon: $globals.icons.database,
          value: data.dbUrl,
        },
        {
          name: i18n.t("about.default-group"),
          icon: $globals.icons.group,
          value: data.defaultGroup,
        },
        {
          name: i18n.t("about.default-household"),
          icon: $globals.icons.household,
          value: data.defaultHousehold,
        },
        {
          slot: "recipe-scraper",
          name: i18n.t("settings.recipe-scraper-version"),
          icon: $globals.icons.primary,
          value: data.recipeScraperVersion,
        },
      ];
      return prettyInfo;
    }
    return data;
  });
  return statistics;
}
const appInfo = getAppInfo();
const bugReportDialog = ref(false);
const bugReportText = computed(() => {
  const ignore = {
    [i18n.t("about.database-url")]: true,
    [i18n.t("about.default-group")]: true,
  };
  let text = "**Details**\n";
  appInfo.value?.forEach((item) => {
    if (ignore[item.name as string]) {
      return;
    }
    text += `${item.name as string}: ${item.value as string}\n`;
  });
  const ignoreChecks: {
    [key: string]: boolean;
  } = {
    "application-version": true,
  };
  text += "\n**Checks**\n";
  simpleChecks.value.forEach((item) => {
    if (ignoreChecks[item.id]) {
      return;
    }
    const status = item.status ? i18n.t("general.yes") : i18n.t("general.no");
    text += `${item.text.toString()}: ${status}\n`;
  });
  text += `${i18n.t("settings.email-configured")}: ${appConfig.value.emailReady ? i18n.t("general.yes") : i18n.t("general.no")}\n`;
  return text;
});

const STATUS_TEXT: Record<string, string> = {
  success: "text-primary",
  error: "text-destructive",
  warning: "text-brand-strong",
  grey: "text-muted-foreground",
};

function propertyLink(property: { slot?: string; value?: string | number | null }) {
  const value = String(property.value ?? "");
  if (property.slot === "recipe-scraper") {
    return `https://github.com/hhursev/recipe-scrapers/releases/tag/${value}`;
  }
  if (property.slot === "build") {
    return `https://github.com/mealie-recipes/mealie/commit/${value}`;
  }
  if (property.slot === "version" && value !== "develop" && value !== "nightly") {
    return `https://github.com/mealie-recipes/mealie/releases/tag/${value}`;
  }
  return undefined;
}

function openTracker() {
  window.open("https://github.com/mealie-recipes/mealie/issues/new/choose", "_blank", "noopener");
}
</script>
