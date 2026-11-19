<template>
  <div class="mx-auto w-full max-w-[960px] px-4 pb-16 pt-4 font-sans sm:px-6 lg:px-8 lg:pt-8">
    <header class="mb-8">
      <NuxtLink
        to="/household/mealplan/planner/view"
        class="mb-3 inline-flex items-center gap-1 text-sm font-medium text-primary no-underline hover:underline"
      >
        <ChevronLeftIcon class="size-4" />
        {{ $t('meal-plan.meal-planner') }}
      </NuxtLink>
      <h1 class="m-0 text-[28px] font-bold tracking-tight sm:text-[32px]">
        {{ $t('meal-plan.meal-plan-rules') }}
      </h1>
      <p class="m-0 mt-2 max-w-[65ch] text-[15.5px] leading-relaxed text-muted-foreground">
        {{ $t('meal-plan.meal-plan-rules-description') }}
      </p>
    </header>

    <section class="rounded-panel border bg-card p-5 sm:p-6">
      <h2 class="m-0 text-lg font-bold tracking-tight">
        {{ $t('meal-plan.new-rule') }}
      </h2>
      <p class="m-0 mb-4 mt-1 text-sm text-muted-foreground">
        {{ $t('meal-plan.new-rule-description') }}
      </p>
      <GroupMealPlanRuleForm
        :key="createDataFormKey"
        v-model:day="createData.day"
        v-model:entry-type="createData.entryType"
        v-model:query-filter-string="createData.queryFilterString"
      />
      <div class="mt-4 flex justify-end">
        <Button
          :disabled="!createData.queryFilterString"
          @click="createRule"
        >
          <PlusIcon class="size-4" />
          {{ $t('meal-plan.create-rule') }}
        </Button>
      </div>
    </section>

    <section class="mt-10">
      <h2 class="m-0 mb-3 text-xl font-bold tracking-tight">
        {{ $t('meal-plan.recipe-rules') }}
      </h2>
      <p
        v-if="!allRules.length"
        class="m-0 rounded-card border border-dashed px-4 py-6 text-center text-sm text-muted-foreground"
      >
        {{ $t('meal-plan.no-rules-yet') }}
      </p>
      <ul class="m-0 flex list-none flex-col gap-3 p-0">
        <li
          v-for="(rule, idx) in allRules"
          :key="rule.id"
          class="rounded-card border bg-card p-4"
        >
          <div class="mb-3 flex items-start gap-2">
            <h3 class="m-0 flex-1 text-[15px] font-semibold">
              {{ rule.day === "unset" ? $t('meal-plan.applies-to-all-days') : $t('meal-plan.applies-on-days', [rule.day]) }}
              {{ rule.entryType === "unset" ? $t('meal-plan.for-all-meal-types') : $t('meal-plan.for-type-meal-types', [rule.entryType]) }}
            </h3>
            <Button
              variant="ghost"
              size="sm"
              :aria-pressed="!!editState[rule.id]"
              @click="toggleEditState(rule.id)"
            >
              <MdiIcon
                :path="editState[rule.id] ? $globals.icons.close : $globals.icons.edit"
                class="size-4"
              />
              {{ editState[rule.id] ? $t('general.cancel') : $t('general.edit') }}
            </Button>
            <Button
              variant="ghost"
              size="icon"
              class="text-muted-foreground hover:text-destructive"
              :aria-label="$t('general.delete')"
              :title="$t('general.delete')"
              @click="deleteRule(rule.id)"
            >
              <Trash2Icon class="size-4" />
            </Button>
          </div>
          <GroupMealPlanRuleForm
            v-if="!editState[rule.id]"
            :query-filter="rule.queryFilter"
            readonly
          />
          <template v-else>
            <GroupMealPlanRuleForm
              v-model:day="allRules[idx]!.day"
              v-model:entry-type="allRules[idx]!.entryType"
              v-model:query-filter-string="allRules[idx]!.queryFilterString"
              :query-filter="allRules[idx]!.queryFilter"
            />
            <div class="mt-4 flex justify-end">
              <Button
                :disabled="!allRules[idx]!.queryFilterString"
                @click="updateRule(rule)"
              >
                {{ $t('general.update') }}
              </Button>
            </div>
          </template>
        </li>
      </ul>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ChevronLeftIcon, PlusIcon, Trash2Icon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { useUserApi } from "~/composables/api";
import type { PlanRulesCreate, PlanRulesOut } from "~/lib/api/types/meal-plan";
import GroupMealPlanRuleForm from "~/components/Domain/Household/GroupMealPlanRuleForm.vue";
import { useAsyncKey } from "~/composables/use-utils";

definePageMeta({
  middleware: ["auth"],
});

const api = useUserApi();
const i18n = useI18n();

useSeoMeta({
  title: i18n.t("meal-plan.meal-plan-settings"),
});

// ======================================================
// Manage All
const editState = ref<{ [key: string]: boolean }>({});
const allRules = ref<PlanRulesOut[]>([]);

function toggleEditState(id: string) {
  editState.value[id] = !editState.value[id];
  editState.value = { ...editState.value };
}

async function refreshAll() {
  const { data } = await api.mealplanRules.getAll();

  if (data) {
    allRules.value = data.items ?? [];
  }
}

useAsyncData(useAsyncKey(), async () => {
  await refreshAll();
});

// ======================================================
// Creating Rules

const createDataFormKey = ref(0);
const createData = ref<PlanRulesCreate>({
  entryType: "unset",
  day: "unset",
  queryFilterString: "",
});

async function createRule() {
  const { data } = await api.mealplanRules.createOne(createData.value);
  if (data) {
    refreshAll();
    createData.value = {
      entryType: "unset",
      day: "unset",
      queryFilterString: "",
    };
    createDataFormKey.value++;
  }
}

async function deleteRule(ruleId: string) {
  const { data } = await api.mealplanRules.deleteOne(ruleId);
  if (data) {
    refreshAll();
  }
}

async function updateRule(rule: PlanRulesOut) {
  const { data } = await api.mealplanRules.updateOne(rule.id, rule);
  if (data) {
    refreshAll();
    toggleEditState(rule.id);
  }
}
</script>
