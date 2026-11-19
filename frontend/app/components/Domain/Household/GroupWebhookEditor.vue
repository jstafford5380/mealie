<template>
  <div class="flex flex-col gap-1 font-sans">
    <label class="mb-2 flex w-fit cursor-pointer items-center gap-3 text-[15px] font-semibold">
      <Switch v-model="webhookCopy.enabled" />
      {{ $t('general.enabled') }}
    </label>
    <TextField
      v-model="webhookCopy.name"
      :label="$t('settings.webhooks.webhook-name')"
    />
    <TextField
      v-model="webhookCopy.url"
      type="url"
      :label="$t('settings.webhooks.webhook-url')"
    />
    <div class="max-w-48">
      <TextField
        v-model="scheduledTime"
        type="time"
        :label="$t('settings.webhooks.scheduled-time')"
      />
    </div>
    <div class="mt-3 flex flex-wrap items-center gap-2 border-t pt-4">
      <Button
        variant="ghost"
        class="text-destructive hover:text-destructive"
        @click="$emit('delete', webhookCopy.id)"
      >
        <Trash2Icon class="size-4" />
        {{ $t('general.delete') }}
      </Button>
      <Button
        variant="outline"
        class="ms-auto"
        @click="$emit('test', webhookCopy.id)"
      >
        <MdiIcon
          :path="$globals.icons.testTube"
          class="size-4"
        />
        {{ $t('general.test') }}
      </Button>
      <Button @click="handleSave">
        {{ $t('general.save') }}
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Trash2Icon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import TextField from "~/components/ui/field/TextField.vue";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { Switch } from "~/components/ui/switch";
import type { WebhookOut } from "~/lib/api/types/household";
import { timeLocalToUTC, timeUTCToLocal } from "~/composables/use-group-webhooks";

const props = defineProps<{
  webhook: WebhookOut;
}>();

const emit = defineEmits<{
  delete: [id: string];
  save: [webhook: WebhookOut];
  test: [id: string];
}>();

const i18n = useI18n();
const itemUTC = ref<string>(props.webhook.scheduledTime);
const itemLocal = ref<string>(timeUTCToLocal(props.webhook.scheduledTime));

const scheduledTime = computed({
  get() {
    return itemLocal.value;
  },
  set(v: string) {
    itemUTC.value = timeLocalToUTC(v);
    itemLocal.value = v;
  },
});

const webhookCopy = ref({ ...props.webhook });

function handleSave() {
  webhookCopy.value.scheduledTime = itemLocal.value;
  emit("save", webhookCopy.value);
}

// Set page title using useSeoMeta
useSeoMeta({
  title: i18n.t("settings.webhooks.webhooks"),
});
</script>
