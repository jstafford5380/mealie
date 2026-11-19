<template>
  <div class="mx-auto flex w-full max-w-[760px] flex-col gap-6 px-4 pb-16 pt-3 font-sans sm:px-6 lg:pt-8">
    <header class="flex flex-wrap items-end gap-3">
      <div class="min-w-0 flex-1">
        <h1 class="m-0 text-[26px] font-bold tracking-tight sm:text-[32px]">
          {{ $t('settings.webhooks.webhooks') }}
        </h1>
        <p class="m-0 mt-1 max-w-[65ch] text-[15px] text-muted-foreground">
          {{ $t('settings.webhooks.description') }}
        </p>
      </div>
      <Button @click="actions.createOne()">
        <PlusIcon class="size-4" />
        {{ $t('settings.webhooks.new-webhook') }}
      </Button>
    </header>

    <Accordion
      v-if="webhooks && webhooks.length"
      type="single"
      collapsible
      class="rounded-card border bg-card"
    >
      <AccordionItem
        v-for="webhook in webhooks"
        :key="webhook.id"
        :value="webhook.id"
        class="px-4 last:border-b-0"
      >
        <AccordionTrigger class="py-3.5">
          <span class="flex min-w-0 items-center gap-3">
            <MdiIcon
              :path="$globals.icons.webhook"
              class="size-5 shrink-0"
              :class="webhook.enabled ? 'text-primary' : 'text-muted-foreground'"
            />
            <span class="min-w-0">
              <span class="block truncate">{{ webhook.name }}</span>
              <span class="block text-sm font-normal text-muted-foreground">
                {{ $d(timeUTC(webhook.scheduledTime), "time") }}
                <template v-if="!webhook.enabled"> · {{ $t('general.disabled') }}</template>
              </span>
            </span>
          </span>
        </AccordionTrigger>
        <AccordionContent>
          <GroupWebhookEditor
            :key="webhook.id"
            :webhook="webhook"
            @save="actions.updateOne($event)"
            @delete="actions.deleteOne($event)"
            @test="actions.testOne($event).then(() => alert.success($t('events.test-message-sent')))"
          />
        </AccordionContent>
      </AccordionItem>
    </Accordion>
    <p
      v-else
      class="m-0 rounded-card border border-dashed px-4 py-8 text-center text-sm text-muted-foreground"
    >
      {{ $t('settings.webhooks.no-webhooks-yet') }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { PlusIcon } from "@lucide/vue";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "~/components/ui/accordion";
import { Button } from "~/components/ui/button";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { useGroupWebhooks, timeUTC } from "~/composables/use-group-webhooks";
import GroupWebhookEditor from "~/components/Domain/Household/GroupWebhookEditor.vue";
import { alert } from "~/composables/use-toast";

definePageMeta({
  middleware: ["auth", "advanced-only", "can-manage-household-only"],
});

const i18n = useI18n();
const { actions, webhooks } = useGroupWebhooks();

useSeoMeta({
  title: i18n.t("settings.webhooks.webhooks"),
});
</script>
