<template>
  <div
    v-if="ready"
    class="flex min-h-dvh flex-col items-center justify-center gap-6 bg-background px-4 text-center font-sans text-foreground"
  >
    <div
      class="flex items-center gap-4 text-[96px] leading-none font-bold text-primary sm:text-[140px]"
      aria-hidden="true"
    >
      <span>4</span>
      <AppLogo :size="104" />
      <span>4</span>
    </div>
    <slot>
      <h1 class="m-0 text-[26px] font-bold tracking-tight">
        {{ $t("page.404-page-not-found") }}
      </h1>
    </slot>
    <div class="flex flex-wrap justify-center gap-2">
      <slot name="actions">
        <Button
          v-for="(button, index) in buttons"
          :key="index"
          @click="clearError({ redirect: button.to })"
        >
          <MdiIcon
            :path="button.icon"
            class="size-4"
          />
          {{ button.text }}
        </Button>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Button } from "~/components/ui/button";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { useGlobalI18n } from "~/composables/use-global-i18n";

const props = defineProps({
  error: {
    type: Object,
    default: null,
  },
});

const i18n = useGlobalI18n();
const auth = useMealieAuth();
const { $globals } = useNuxtApp();
const ready = ref(false);

const route = useRoute();
const router = useRouter();

async function insertGroupSlugIntoRoute() {
  const groupSlug = ref(auth.user.value?.groupSlug);
  if (!groupSlug.value) {
    return;
  }

  let replaceRoute = false;
  let routeVal = route.fullPath || "/";
  if (routeVal[0] !== "/") {
    routeVal = `/${routeVal}`;
  }

  // replace "recipe" in URL with "r"
  if (routeVal.includes("/recipe/")) {
    replaceRoute = true;
    routeVal = routeVal.replace("/recipe/", "/r/");
  }

  // insert groupSlug into URL
  const routeComponents = routeVal.split("/");
  if (routeComponents.length < 2 || routeComponents[1].toLowerCase() !== "g") {
    replaceRoute = true;
    routeVal = `/g/${groupSlug.value}${routeVal}`;
  }

  // Only leave the error page for a path that exists: an unknown path under
  // /g/<groupSlug> matches only the group page and would show an empty page
  if (replaceRoute && router.resolve(routeVal).name) {
    await clearError({ redirect: routeVal });
  }
}

async function handle404() {
  const normalizedRoute = route.fullPath.replace(/\/$/, "");
  const newRoute = normalizedRoute.replace(/^\/group\/(mealplan|members|notifiers|webhooks)(\/.*)?$/, "/household/$1$2");

  if (newRoute !== normalizedRoute) {
    await clearError({ redirect: newRoute });
  }
  else {
    await insertGroupSlugIntoRoute();
  }

  ready.value = true;
}

if (props.error.statusCode === 404) {
  handle404();
}
else {
  ready.value = true;
}

useSeoMeta({
  title:
        props.error.statusCode === 404
          ? (i18n.t("page.404-not-found") as string)
          : (i18n.t("page.an-error-occurred") as string),
});

const buttons = [
  { icon: $globals.icons.home, to: "/", text: i18n.t("general.home") },
];
</script>

<style scoped>
h1 {
  font-size: 20px;
}

p {
  padding-bottom: 0 !important;
  margin-bottom: 0 !important;
  font-size: 200px;
}
</style>
