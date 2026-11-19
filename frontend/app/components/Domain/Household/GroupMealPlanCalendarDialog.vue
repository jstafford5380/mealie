<template>
  <BaseDialog
    v-model="dialog"
    :title="$t('meal-plan.calendar-feed')"
    :icon="$globals.icons.calendar"
    width="600"
    disable-submit-on-enter
  >
    <div class="flex flex-col gap-4 px-6 pb-2 font-sans">
      <p class="m-0 text-[15px] leading-relaxed">
        {{ $t("meal-plan.calendar-feed-description") }}
      </p>

      <div
        v-if="loading"
        class="h-1 overflow-hidden rounded-full bg-muted"
      >
        <div class="h-full w-1/3 animate-pulse rounded-full bg-primary" />
      </div>
      <p
        v-else-if="!token"
        class="m-0 rounded-control bg-muted px-3 py-2 text-sm"
      >
        {{ $t("meal-plan.calendar-feed-off") }}
        <span v-if="!canManage">{{ $t("meal-plan.calendar-feed-ask-manager") }}</span>
      </p>
      <template v-else>
        <fieldset class="m-0 border-0 p-0">
          <legend class="mb-1.5 p-0 text-sm font-semibold">
            {{ $t('meal-plan.meal-type') }}
          </legend>
          <div class="flex flex-wrap gap-1.5">
            <button
              v-for="option in planTypeOptions"
              :key="option.value"
              type="button"
              :aria-pressed="selectedTypes.includes(option.value)"
              class="inline-flex h-8 items-center gap-1 rounded-full border px-3 text-sm font-medium transition-colors"
              :class="selectedTypes.includes(option.value) ? 'border-primary bg-primary text-primary-foreground' : 'border-input hover:bg-highlight'"
              @click="selectedTypes = selectedTypes.includes(option.value) ? selectedTypes.filter(t => t !== option.value) : [...selectedTypes, option.value]"
            >
              {{ option.text }}
            </button>
          </div>
        </fieldset>
        <CheckboxField
          v-model="includeNotes"
          :label="$t('meal-plan.calendar-feed-include-notes')"
        />

        <div>
          <p class="m-0 mb-2 text-sm text-muted-foreground">
            {{ $t("meal-plan.calendar-feed-times-hint") }}
          </p>
          <div class="grid grid-cols-2 gap-3 sm:grid-cols-3">
            <label
              v-for="option in selectedOptions"
              :key="option.value"
              class="flex flex-col gap-1 text-sm font-semibold"
            >
              {{ option.text }}
              <input
                v-model="times[option.value]"
                type="time"
                class="h-10 rounded-control border border-input bg-card px-3 text-[15px] outline-none focus:border-ring focus:ring-3 focus:ring-ring/25 font-normal [color-scheme:light] dark:[color-scheme:dark]"
              >
            </label>
          </div>
        </div>
        <NumberInputField
          v-if="hasTimes"
          v-model="duration"
          class="max-w-56"
          :label="$t('meal-plan.calendar-feed-duration')"
          :min="1"
          :max="24 * 60"
          control-variant="hidden"
        />

        <div class="flex flex-col gap-2 border-t pt-4">
          <h3 class="m-0 text-base font-semibold">
            {{ $t("meal-plan.calendar-feed-event-details") }}
          </h3>
          <p class="m-0 text-sm text-muted-foreground">
            {{ $t("meal-plan.calendar-feed-event-details-description") }}
          </p>
          <p class="m-0 text-sm">
            {{ $t("meal-plan.calendar-feed-event-details-change-warning") }}
          </p>
          <DocLink link="/documentation/getting-started/features/#calendar-feed" />
          <TextField
            v-model="summary"
            :label="$t('meal-plan.calendar-feed-event-title')"
          />
          <TextareaField
            v-model="description"
            :label="$t('meal-plan.calendar-feed-event-description')"
            :rows="2"
          />
        </div>

        <div class="flex flex-col gap-1.5 border-t pt-4">
          <span class="text-sm font-semibold">{{ $t('meal-plan.calendar-feed-url') }}</span>
          <div class="flex items-center gap-2">
            <input
              :value="feedUrl"
              readonly
              :aria-label="$t('meal-plan.calendar-feed-url')"
              class="h-10 rounded-control border border-input bg-card px-3 text-[15px] outline-none focus:border-ring focus:ring-3 focus:ring-ring/25 min-w-0 flex-1 font-mono text-sm"
              @focus="($event.target as HTMLInputElement).select()"
            >
            <AppButtonCopy
              :copy-text="feedUrl"
              icon
            />
          </div>
          <p
            v-if="canManage"
            class="m-0 text-xs text-muted-foreground"
          >
            {{ $t("meal-plan.calendar-feed-reset-hint") }}
          </p>
        </div>
      </template>
    </div>

    <template
      v-if="canManage && !loading"
      #custom-card-action
    >
      <template v-if="token">
        <BaseButton
          delete
          :icon="$globals.icons.close"
          :text="$t('meal-plan.calendar-feed-turn-off')"
          @click="disableFeed"
        />
        <BaseButton
          edit
          :icon="$globals.icons.refresh"
          :text="$t('general.reset')"
          @click="createToken"
        />
      </template>
      <BaseButton
        v-else
        create
        :text="$t('meal-plan.calendar-feed-turn-on')"
        @click="createToken"
      />
    </template>
  </BaseDialog>
</template>

<script setup lang="ts">
import CheckboxField from "~/components/ui/field/CheckboxField.vue";
import NumberInputField from "~/components/ui/field/NumberInputField.vue";
import TextareaField from "~/components/ui/field/TextareaField.vue";
import TextField from "~/components/ui/field/TextField.vue";
import { whenever } from "@vueuse/core";
import { useUserApi } from "~/composables/api";
import { useGlobalI18n } from "~/composables/use-global-i18n";
import { usePlanTypeOptions } from "~/composables/use-group-mealplan";
import type { PlanEntryType } from "~/lib/api/types/meal-plan";

const dialog = defineModel<boolean>({ default: false });

// must match the feed's defaults (mealplan_ical_service.py)
const EVENT_DURATION_MINUTES = 60;
const SUMMARY_TEMPLATE = "${type}: ${title}";
const DESCRIPTION_TEMPLATE = "${note}\n\n${url}";

const api = useUserApi();
const i18n = useGlobalI18n();
const auth = useMealieAuth();
const canManage = computed(() => !!auth.user.value?.canManageHousehold);
const planTypeOptions = usePlanTypeOptions();

const loading = ref(false);
const token = ref<string | null>(null);

const selectedTypes = ref<PlanEntryType[]>(planTypeOptions.map(option => option.value));
const includeNotes = ref(true);
const times = ref<Partial<Record<PlanEntryType, string | null>>>({});
const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
const duration = ref<number | null>(EVENT_DURATION_MINUTES);
const summary = ref(SUMMARY_TEMPLATE);
const description = ref(DESCRIPTION_TEMPLATE);

const selectedOptions = computed(() => planTypeOptions.filter(option => selectedTypes.value.includes(option.value)));
const hasTimes = computed(() => selectedOptions.value.some(option => times.value[option.value]));

const feedUrl = computed(() => {
  if (!token.value) {
    return "";
  }

  const params = new URLSearchParams({ lang: i18n.locale.value });
  if (selectedTypes.value.length && selectedTypes.value.length < planTypeOptions.length) {
    selectedTypes.value.forEach(type => params.append("types", type));
  }
  if (!includeNotes.value) {
    params.set("includeNotes", "false");
  }
  for (const option of selectedOptions.value) {
    const time = times.value[option.value];
    if (time) {
      params.set(option.value, time);
    }
  }
  if (hasTimes.value && timezone) {
    params.set("tz", timezone);
  }
  if (hasTimes.value && duration.value && duration.value !== EVENT_DURATION_MINUTES) {
    params.set("duration", duration.value.toString());
  }
  // blank templates fall back to the defaults
  if (summary.value?.trim() && summary.value !== SUMMARY_TEMPLATE) {
    params.set("summary", summary.value);
  }
  if (description.value?.trim() && description.value !== DESCRIPTION_TEMPLATE) {
    params.set("description", description.value);
  }

  const query = params.toString();
  return `${window.location.origin}/api/households/mealplans/ical/${token.value}${query ? `?${query}` : ""}`;
});

async function refreshToken() {
  loading.value = true;
  const { data } = await api.mealplans.getICalToken();
  token.value = data?.mealplanIcalToken ?? null;
  loading.value = false;
}

async function createToken() {
  const { data } = await api.mealplans.createICalToken();
  if (data) {
    token.value = data.mealplanIcalToken ?? null;
  }
}

async function disableFeed() {
  const { data } = await api.mealplans.deleteICalToken();
  if (data) {
    token.value = null;
  }
}

whenever(dialog, refreshToken);
</script>
