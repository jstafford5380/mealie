<template>
  <BaseDialog
    v-model="inviteDialog"
    :title="$t('profile.get-invite-link')"
    :icon="$globals.icons.accountPlusOutline"
    color="primary"
  >
    <div class="flex flex-col gap-1 px-6 pb-2">
      <SelectField
        v-if="groups && groups.length"
        v-model="selectedGroup"
        :items="groups"
        item-title="name"
        item-value="id"
        :label="$t('group.user-group')"
        :rules="[validators.required]"
      />
      <SelectField
        v-if="households && households.length"
        v-model="selectedHousehold"
        :items="filteredHouseholds"
        item-title="name"
        item-value="id"
        :label="$t('household.user-household')"
        :rules="[validators.required]"
      />
      <p class="m-0 mt-1 text-sm font-semibold">
        {{ $t('profile.invite-link') }}
      </p>
      <div class="flex items-center gap-2">
        <input
          :value="generatedSignupLink"
          readonly
          :aria-label="$t('profile.invite-link')"
          class="h-10 min-w-0 flex-1 rounded-control border border-input bg-muted px-3 font-mono text-[13px] outline-none"
          @focus="($event.target as HTMLInputElement).select()"
        >
        <AppButtonCopy
          :icon="false"
          :copy-text="generatedSignupLink"
        />
      </div>
      <div class="mt-3 border-t pt-3">
        <TextField
          v-model="sendTo"
          type="email"
          :label="$t('profile.or-email-the-invite')"
          :rules="[validators.email]"
          @keydown.enter.prevent="sendInvite"
        />
      </div>
    </div>
    <template #custom-card-action>
      <Button
        variant="outline"
        :disabled="!validEmail || loading"
        @click="sendInvite"
      >
        <MdiIcon
          :path="$globals.icons.email"
          class="size-4"
        />
        {{ $t("group.invite") }}
      </Button>
    </template>
  </BaseDialog>
</template>

<script setup lang="ts">
import { Button } from "~/components/ui/button";
import SelectField from "~/components/ui/field/SelectField.vue";
import TextField from "~/components/ui/field/TextField.vue";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { useUserApi } from "@/composables/api";
import BaseDialog from "~/components/global/BaseDialog.vue";
import AppButtonCopy from "~/components/global/AppButtonCopy.vue";
import { validators } from "~/composables/use-validators";
import { alert } from "~/composables/use-toast";
import type { GroupOut } from "~/lib/api/types/user";
import type { HouseholdOut } from "~/lib/api/types/household";
import { useGroups } from "~/composables/use-groups";
import { useAdminHouseholds } from "~/composables/use-households";

const inviteDialog = defineModel<boolean>("modelValue", { type: Boolean, default: false });

const i18n = useI18n();
const auth = useMealieAuth();

const isAdmin = computed(() => auth.user.value?.admin);
const token = ref("");
const selectedGroup = ref<string | null>(null);
const selectedHousehold = ref<string | null>(null);
const groups = ref<GroupOut[]>([]);
const households = ref<HouseholdOut[]>([]);
const api = useUserApi();

const fetchGroupsAndHouseholds = () => {
  if (isAdmin.value) {
    const groupsResponse = useGroups();
    const householdsResponse = useAdminHouseholds();
    watchEffect(() => {
      groups.value = groupsResponse.groups.value || [];
      households.value = householdsResponse.households.value || [];
    });
  }
};

async function getSignupLink(group: string | null = null, household: string | null = null) {
  const payload = (group && household) ? { uses: 1, group_id: group, household_id: household } : { uses: 1 };
  const { data } = await api.households.createInvitation(payload);
  if (data) {
    token.value = data.token;
  }
}

const filteredHouseholds = computed(() => {
  if (!selectedGroup.value) return [];
  return households.value?.filter(household => household.groupId === selectedGroup.value);
});

function constructLink(tokenVal: string) {
  return tokenVal ? `${window.location.origin}/register?token=${tokenVal}` : "";
}

const generatedSignupLink = computed(() => constructLink(token.value));

// Email Invitation
const state = reactive({
  loading: false,
  sendTo: "",
});
const { loading, sendTo } = toRefs(state);

async function sendInvite() {
  state.loading = true;
  if (!token.value) {
    getSignupLink(selectedGroup.value, selectedHousehold.value);
  }
  const { data } = await api.email.sendInvitation({
    email: state.sendTo,
    token: token.value,
  });

  if (data && data.success) {
    alert.success(i18n.t("profile.email-sent"));
  }
  else {
    alert.error(i18n.t("profile.error-sending-email"));
  }
  state.loading = false;
  inviteDialog.value = false;
}

const validEmail = computed(() => {
  if (sendTo.value === "") return false;
  const valid = validators.email(sendTo.value);
  return valid === true;
});

// Watchers (replacing options API watchers)
watch(inviteDialog, (val) => {
  if (val && !isAdmin.value) {
    getSignupLink();
  }
});

watch(selectedHousehold, (newVal) => {
  if (newVal && selectedGroup.value) {
    getSignupLink(selectedGroup.value, selectedHousehold.value);
  }
});

// initial fetch
fetchGroupsAndHouseholds();
</script>
