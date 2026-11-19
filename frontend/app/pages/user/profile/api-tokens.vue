<template>
  <div class="mx-auto flex w-full max-w-[760px] flex-col gap-8 px-4 pb-16 pt-3 font-sans sm:px-6 lg:pt-8">
    <NuxtLink
      to="/user/profile"
      class="-mb-4 inline-flex w-fit items-center gap-1 text-sm font-semibold text-muted-foreground no-underline hover:text-foreground"
    >
      <ChevronLeftIcon class="size-4 rtl:rotate-180" />
      {{ $t('profile.back-to-profile') }}
    </NuxtLink>
    <header>
      <h1 class="m-0 text-[26px] font-bold tracking-tight sm:text-[32px]">
        {{ $t("settings.token.api-tokens") }}
      </h1>
      <p class="m-0 mt-1 text-[15px] text-muted-foreground">
        {{ $t('settings.token.you-have-token-count', user.tokens!.length) }}
      </p>
    </header>

    <section class="rounded-panel border bg-card p-5 sm:p-6">
      <h2 class="m-0 mb-3 text-xl font-bold tracking-tight">
        {{ $t("settings.token.create-an-api-token") }}
      </h2>
      <form
        v-if="!createdToken"
        class="flex flex-wrap items-end gap-3"
        @submit.prevent="name && createToken(name)"
      >
        <div class="min-w-0 flex-1 basis-60">
          <TextField
            v-model="name"
            :label="$t('settings.token.token-name')"
          />
        </div>
        <Button
          type="submit"
          class="mb-1.5"
          :disabled="name == ''"
        >
          {{ $t('settings.token.generate') }}
        </Button>
      </form>
      <div
        v-else
        class="flex flex-col gap-3"
      >
        <p class="m-0 rounded-control border border-brand/50 bg-brand/10 px-3 py-2 text-sm">
          {{ $t("settings.token.copy-this-token-for-use-with-an-external-application-this-token-will-not-be-viewable-again") }}
        </p>
        <textarea
          :value="createdToken"
          readonly
          rows="3"
          :aria-label="$t('settings.token.api-token')"
          class="w-full resize-none rounded-control border border-input bg-muted px-3 py-2 font-mono text-[13px] break-all outline-none"
          @focus="($event.target as HTMLTextAreaElement).select()"
        />
        <div class="flex justify-end gap-2">
          <Button
            variant="ghost"
            @click="resetCreate()"
          >
            {{ $t('general.done') }}
          </Button>
          <AppButtonCopy
            :icon="false"
            :copy-text="createdToken"
          />
        </div>
      </div>
    </section>

    <section>
      <h2 class="m-0 mb-3 text-base font-semibold">
        {{ $t('settings.token.active-tokens') }}
      </h2>
      <ul
        v-if="user.tokens?.length"
        class="m-0 flex list-none flex-col divide-y rounded-card border bg-card p-0"
      >
        <li
          v-for="token in user.tokens"
          :key="token.id"
          class="flex items-center gap-3 py-2 ps-4 pe-1.5"
        >
          <MdiIcon
            :path="$globals.icons.api"
            class="size-5 shrink-0 text-muted-foreground"
          />
          <span class="min-w-0 flex-1">
            <span class="block truncate font-semibold">{{ token.name }}</span>
            <span class="block text-sm text-muted-foreground">{{ $t('general.created-on-date', [$d(new Date(token.createdAt!))]) }}</span>
          </span>
          <button
            type="button"
            class="inline-flex size-9 items-center justify-center rounded-full text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
            :aria-label="$t('data-pages.delete-item', { name: token.name })"
            :title="$t('general.delete')"
            @click="deleteToken(token.id)"
          >
            <Trash2Icon class="size-4" />
          </button>
        </li>
      </ul>
      <p
        v-else
        class="m-0 rounded-card border border-dashed px-4 py-6 text-center text-sm text-muted-foreground"
      >
        {{ $t('settings.token.no-tokens-yet') }}
      </p>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ChevronLeftIcon, Trash2Icon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import TextField from "~/components/ui/field/TextField.vue";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { useUserApi } from "~/composables/api";

definePageMeta({
  middleware: ["auth", "advanced-only"],
});

const i18n = useI18n();
const auth = useMealieAuth();

useSeoMeta({
  title: i18n.t("settings.token.api-tokens"),
});

const user = computed(() => {
  return auth.user.value;
});

const api = useUserApi();

const createdToken = ref("");
const name = ref("");
const loading = ref(false);

function resetCreate() {
  createdToken.value = "";
  loading.value = false;
  name.value = "";
  auth.getSession();
}

async function createToken(name: string) {
  if (loading.value) {
    resetCreate();
    return;
  }

  loading.value = true;

  const { data } = await api.users.createAPIToken({ name });

  if (data) {
    createdToken.value = data.token;
  }
}

async function deleteToken(id: number) {
  const { data } = await api.users.deleteAPIToken(id);
  auth.getSession();
  return data;
}
</script>
