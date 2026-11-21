<template>
  <BaseDialog
    v-model="open"
    :title="$t('meal-plan.import-saved-plan')"
    :submit-text="$t('general.import')"
    :submit-disabled="busy || !selectedPlan || !selectedWeek"
    disable-submit-on-enter
    can-submit
    keep-open
    @submit="importPlan"
  >
    <div class="grid gap-4 px-6 pb-2">
      <p v-if="error" role="alert" class="text-sm text-destructive">
        {{ error }}
      </p>
      <template v-if="plans.length">
        <SelectField
          v-model="selectedPlan"
          :items="plans.map(({ id, name }) => ({ value: id, title: name }))"
          :label="$t('meal-plan.saved-plan-select')"
          :disabled="busy"
        />
        <SelectField
          v-model="selectedWeek"
          :items="weeks"
          :label="$t('meal-plan.import-saved-week')"
          :disabled="busy"
        />
        <p class="text-sm text-muted-foreground">
          {{ $t("meal-plan.import-saved-hint") }}
        </p>
      </template>
      <div v-else-if="!busy && !error" class="grid gap-3">
        <p class="text-sm text-muted-foreground">
          {{ $t("meal-plan.import-saved-empty") }}
        </p>
        <NuxtLink to="/household/mealplan/configurator" class="font-medium text-primary underline">
          {{ $t("meal-plan.configurator") }}
        </NuxtLink>
      </div>
    </div>
  </BaseDialog>
</template>

<script setup lang="ts">
import SelectField from "~/components/ui/field/SelectField.vue";
import { useUserApi } from "~/composables/api";
import type { SavedMealPlanSummary } from "~/lib/api/types/meal-plan";

const props = defineProps<{ weeks: { value: string; title: string }[] }>();
const emit = defineEmits<{ imported: [] }>();
const open = defineModel<boolean>({ required: true });
const { mealplans: api } = useUserApi();
const i18n = useI18n();
const busy = ref(false);
const error = ref("");
const plans = ref<SavedMealPlanSummary[]>([]);
const selectedPlan = ref<string | null>(null);
const selectedWeek = ref<string | null>(null);

watch(open, async (visible) => {
  if (!visible || busy.value) return;
  busy.value = true;
  error.value = "";
  plans.value = [];
  selectedPlan.value = null;
  selectedWeek.value = props.weeks[0]?.value ?? null;
  try {
    const { data } = await api.getSavedPlans();
    if (data) plans.value = data;
    else error.value = i18n.t("meal-plan.saved-plan-load-error");
  }
  finally {
    busy.value = false;
  }
});

async function importPlan() {
  if (busy.value || !selectedPlan.value || !props.weeks.some(week => week.value === selectedWeek.value)) return;
  busy.value = true;
  error.value = "";
  try {
    const { data } = await api.importSavedPlan(selectedPlan.value, { weekStart: selectedWeek.value! });
    if (data) {
      emit("imported");
      open.value = false;
    }
    else {
      error.value = i18n.t("meal-plan.import-saved-error");
    }
  }
  finally {
    busy.value = false;
  }
}
</script>
