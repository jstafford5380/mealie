<template>
  <div class="mx-auto flex w-full max-w-[760px] flex-col px-4 pb-16 pt-3 font-sans sm:px-6 lg:pt-8">
    <BaseDialog
      v-model="state.deleteDialog"
      color="error"
      :title="$t('general.confirm')"
      :icon="$globals.icons.alertCircle"
      can-confirm
      @confirm="deleteNotifier(state.deleteTargetId)"
    >
      <p class="m-0 px-6 pb-2 text-[15px]">
        {{ $t("general.confirm-delete-generic") }}
      </p>
    </BaseDialog>
    <BaseDialog
      v-model="state.createDialog"
      :title="$t('events.new-notification')"
      :icon="$globals.icons.bellPlus"
      can-submit
      @submit="createNewNotifier"
    >
      <div class="px-6 pb-2">
        <TextField
          v-model="createNotifierData.name"
          autofocus
          :label="$t('general.name')"
        />
        <TextField
          v-model="createNotifierData.appriseUrl"
          :label="$t('events.apprise-url')"
        />
      </div>
    </BaseDialog>

    <header class="mb-6 flex flex-wrap items-end gap-3">
      <div class="min-w-0 flex-1">
        <h1 class="m-0 text-[26px] font-bold tracking-tight sm:text-[32px]">
          {{ $t("events.event-notifiers") }}
        </h1>
        <p class="m-0 mt-1 max-w-[65ch] text-[15px] text-muted-foreground">
          {{ $t("events.new-notification-form-description") }}
        </p>
        <p class="m-0 mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm">
          <a
            v-for="link in APPRISE_LINKS"
            :key="link.href"
            :href="link.href"
            target="_blank"
            rel="noopener"
            class="font-semibold text-primary no-underline hover:underline"
          >{{ link.text }}</a>
        </p>
      </div>
      <Button @click="state.createDialog = true">
        <PlusIcon class="size-4" />
        {{ $t('events.new-notification') }}
      </Button>
    </header>

    <Accordion
      v-if="notifiers && notifiers.length"
      type="single"
      collapsible
      class="rounded-card border bg-card"
    >
      <AccordionItem
        v-for="(notifier, index) in notifiers"
        :key="notifier.id"
        :value="notifier.id"
        class="px-4 last:border-b-0"
      >
        <AccordionTrigger class="py-3.5">
          <span class="flex min-w-0 items-center gap-3">
            <MdiIcon
              :path="$globals.icons.bellPlus"
              class="size-5 shrink-0"
              :class="notifier.enabled ? 'text-primary' : 'text-muted-foreground'"
            />
            <span class="min-w-0">
              <span class="block truncate">{{ notifier.name }}</span>
              <span
                v-if="!notifier.enabled"
                class="block text-sm font-normal text-muted-foreground"
              >{{ $t('general.disabled') }}</span>
            </span>
          </span>
        </AccordionTrigger>
        <AccordionContent>
          <div class="flex flex-col gap-1">
            <label class="mb-2 flex w-fit cursor-pointer items-center gap-3 text-[15px] font-semibold">
              <Switch v-model="notifiers[index]!.enabled" />
              {{ $t('events.enable-notifier') }}
            </label>
            <TextField
              v-model="notifiers[index]!.name"
              :label="$t('general.name')"
            />
            <TextField
              v-model="notifiers[index]!.appriseUrl"
              :label="$t('events.apprise-url-skipped-if-blank')"
              :hint="$t('events.apprise-url-is-left-intentionally-blank')"
            />

            <h3 class="m-0 mt-4 border-t pt-4 text-base font-semibold">
              {{ $t("events.what-events") }}
            </h3>
            <div class="mt-2 grid gap-x-6 gap-y-4 sm:grid-cols-2">
              <section
                v-for="sec in optionsSections"
                :key="sec.id"
                class="flex flex-col gap-1.5"
              >
                <h4 class="m-0 text-sm font-semibold text-muted-foreground">
                  {{ sec.text }}
                </h4>
                <label
                  v-for="opt in sec.options"
                  :key="opt.key"
                  class="flex cursor-pointer items-center gap-2 text-[15px]"
                >
                  <Checkbox
                    :model-value="!!(notifiers[index]!.options as Record<string, unknown>)[opt.key]"
                    @update:model-value="(notifiers[index]!.options as Record<string, unknown>)[opt.key] = !!$event"
                  />
                  {{ opt.text }}
                </label>
              </section>
            </div>

            <div class="mt-4 flex flex-wrap items-center gap-2 border-t pt-4">
              <Button
                variant="ghost"
                class="text-destructive hover:text-destructive"
                @click="openDelete(notifier)"
              >
                <Trash2Icon class="size-4" />
                {{ $t('general.delete') }}
              </Button>
              <Button
                variant="outline"
                class="ms-auto"
                @click="testNotifier(notifier)"
              >
                <MdiIcon
                  :path="$globals.icons.testTube"
                  class="size-4"
                />
                {{ $t('general.test') }}
              </Button>
              <Button @click="saveNotifier(notifier)">
                {{ $t('general.save') }}
              </Button>
            </div>
          </div>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
    <p
      v-else
      class="m-0 rounded-card border border-dashed px-4 py-8 text-center text-sm text-muted-foreground"
    >
      {{ $t('events.no-notifiers-yet') }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { PlusIcon, Trash2Icon } from "@lucide/vue";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "~/components/ui/accordion";
import { Button } from "~/components/ui/button";
import { Checkbox } from "~/components/ui/checkbox";
import TextField from "~/components/ui/field/TextField.vue";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { Switch } from "~/components/ui/switch";
import { useUserApi } from "~/composables/api";
import { useAsyncKey } from "~/composables/use-utils";
import type { GroupEventNotifierCreate, GroupEventNotifierOut } from "~/lib/api/types/household";

interface OptionKey {
  text: string;
  key: keyof GroupEventNotifierOut["options"];
}

interface OptionSection {
  id: number;
  text: string;
  options: OptionKey[];
}

definePageMeta({
  middleware: ["auth", "advanced-only", "can-manage-household-only"],
});

const api = useUserApi();
const i18n = useI18n();

useSeoMeta({
  title: i18n.t("profile.notifiers"),
});

const APPRISE_LINKS = [
  { text: "Apprise", href: "https://github.com/caronc/apprise/wiki" },
  { text: "Gotify", href: "https://github.com/caronc/apprise/wiki/Notify_gotify" },
  { text: "Discord", href: "https://github.com/caronc/apprise/wiki/Notify_discord" },
  { text: "Home Assistant", href: "https://github.com/caronc/apprise/wiki/Notify_homeassistant" },
  { text: "Matrix", href: "https://github.com/caronc/apprise/wiki/Notify_matrix" },
  { text: "Pushover", href: "https://github.com/caronc/apprise/wiki/Notify_pushover" },
];

const state = reactive({
  deleteDialog: false,
  createDialog: false,
  deleteTargetId: "",
});

const { data: notifiers } = useAsyncData(useAsyncKey(), async () => {
  const { data } = await api.groupEventNotifier.getAll();
  return data?.items;
}, { deep: true });

async function refreshNotifiers() {
  const { data } = await api.groupEventNotifier.getAll();
  notifiers.value = data?.items;
}

const createNotifierData: GroupEventNotifierCreate = reactive({
  name: "",
  enabled: true,
  appriseUrl: "",
});

async function createNewNotifier() {
  await api.groupEventNotifier.createOne(createNotifierData);
  refreshNotifiers();
}

function openDelete(notifier: GroupEventNotifierOut) {
  state.deleteDialog = true;
  state.deleteTargetId = notifier.id;
}

async function deleteNotifier(targetId: string) {
  await api.groupEventNotifier.deleteOne(targetId);
  refreshNotifiers();
  state.deleteTargetId = "";
}

async function saveNotifier(notifier: GroupEventNotifierOut) {
  await api.groupEventNotifier.updateOne(notifier.id, notifier);
  refreshNotifiers();
}

async function testNotifier(notifier: GroupEventNotifierOut) {
  await api.groupEventNotifier.test(notifier.id);
}

// ===============================================================
// Options Definitions

const optionsSections: OptionSection[] = [
  {
    id: 1,
    text: i18n.t("events.recipe-events"),
    options: [
      {
        text: i18n.t("general.create") as string,
        key: "recipeCreated",
      },
      {
        text: i18n.t("general.update") as string,
        key: "recipeUpdated",
      },
      {
        text: i18n.t("general.delete") as string,
        key: "recipeDeleted",
      },
    ],
  },
  {
    id: 2,
    text: i18n.t("events.user-events"),
    options: [
      {
        text: i18n.t("events.when-a-new-user-joins-your-group"),
        key: "userSignup",
      },
    ],
  },
  {
    id: 3,
    text: i18n.t("events.mealplan-events"),
    options: [
      {
        text: i18n.t("general.create") as string,
        key: "mealplanEntryCreated",
      },
      {
        text: i18n.t("general.update") as string,
        key: "mealplanEntryUpdated",
      },
      {
        text: i18n.t("general.delete") as string,
        key: "mealplanEntryDeleted",
      },
    ],
  },
  {
    id: 4,
    text: i18n.t("events.shopping-list-events"),
    options: [
      {
        text: i18n.t("general.create") as string,
        key: "shoppingListCreated",
      },
      {
        text: i18n.t("general.update") as string,
        key: "shoppingListUpdated",
      },
      {
        text: i18n.t("general.delete") as string,
        key: "shoppingListDeleted",
      },
    ],
  },
  {
    id: 5,
    text: i18n.t("events.cookbook-events"),
    options: [
      {
        text: i18n.t("general.create") as string,
        key: "cookbookCreated",
      },
      {
        text: i18n.t("general.update") as string,
        key: "cookbookUpdated",
      },
      {
        text: i18n.t("general.delete") as string,
        key: "cookbookDeleted",
      },
    ],
  },
  {
    id: 6,
    text: i18n.t("events.tag-events"),
    options: [
      {
        text: i18n.t("general.create") as string,
        key: "tagCreated",
      },
      {
        text: i18n.t("general.update") as string,
        key: "tagUpdated",
      },
      {
        text: i18n.t("general.delete") as string,
        key: "tagDeleted",
      },
    ],
  },
  {
    id: 7,
    text: i18n.t("events.category-events"),
    options: [
      {
        text: i18n.t("general.create") as string,
        key: "categoryCreated",
      },
      {
        text: i18n.t("general.update") as string,
        key: "categoryUpdated",
      },
      {
        text: i18n.t("general.delete") as string,
        key: "categoryDeleted",
      },
    ],
  },
  {
    id: 8,
    text: i18n.t("events.label-events"),
    options: [
      {
        text: i18n.t("general.create") as string,
        key: "labelCreated",
      },
      {
        text: i18n.t("general.update") as string,
        key: "labelUpdated",
      },
      {
        text: i18n.t("general.delete") as string,
        key: "labelDeleted",
      },
    ],
  },
];
</script>
