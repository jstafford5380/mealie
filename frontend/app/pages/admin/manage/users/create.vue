<template>
  <div class="mx-auto flex w-full max-w-[760px] flex-col px-4 pb-16 pt-3 font-sans sm:px-6 lg:pt-8">
    <NuxtLink
      to="/admin/manage/users"
      class="mb-3 inline-flex w-fit items-center gap-1 text-sm font-semibold text-muted-foreground no-underline hover:text-foreground"
    >
      <ChevronLeftIcon class="size-4 rtl:rotate-180" />
      {{ $t('user.user-management') }}
    </NuxtLink>
    <header class="mb-6">
      <h1 class="m-0 text-[26px] font-bold tracking-tight sm:text-[32px]">
        {{ $t('user.admin-user-creation') }}
      </h1>
    </header>
    <FieldScope ref="refNewUserForm">
      <form
        class="rounded-panel border bg-card p-5 sm:p-6"
        @submit.prevent="handleSubmit"
      >
        <div class="grid gap-x-4 sm:grid-cols-2">
          <SelectField
            v-model="selectedGroupId"
            :items="groups || []"
            item-title="name"
            item-value="id"
            :label="$t('group.user-group')"
            :rules="[validators.required]"
          />
          <SelectField
            v-model="newUserData.household"
            :disabled="!selectedGroup"
            :items="households"
            item-title="name"
            item-value="name"
            :label="$t('household.user-household')"
            :hint="selectedGroup ? '' : $t('group.you-must-select-a-group-before-selecting-a-household')"
            :rules="[validators.required]"
          />
        </div>
        <AutoForm
          v-model="newUserData"
          class="px-0!"
          :items="userForm"
          :disabled-fields="disabledFields"
        />
        <div class="mt-4 flex justify-end border-t pt-4">
          <Button type="submit">
            {{ $t('user.create-user') }}
          </Button>
        </div>
      </form>
    </FieldScope>
  </div>
</template>

<script setup lang="ts">
import { ChevronLeftIcon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import FieldScope from "~/components/ui/field/FieldScope.vue";
import SelectField from "~/components/ui/field/SelectField.vue";
import { useAdminApi } from "~/composables/api";
import { useGroups } from "~/composables/use-groups";
import { useUserForm } from "~/composables/use-users";
import { validators } from "~/composables/use-validators";
import type { GroupOut, UserIn } from "~/lib/api/types/user";

definePageMeta({
  layout: "admin",
});
const { userForm } = useUserForm();
const { groups } = useGroups();
const router = useRouter();

const refNewUserForm = ref<{ validate: () => Promise<{ valid: boolean }> } | null>(null);
const adminApi = useAdminApi();

const selectedGroupId = ref<string | undefined>(undefined);
const selectedGroup = computed<GroupOut | undefined>(() => groups.value?.find(group => group.id === selectedGroupId.value));
const households = computed(() => selectedGroup.value?.households || []);

const newUserData = ref({
  username: "",
  fullName: "",
  email: "",
  admin: false,
  group: computed(() => selectedGroup.value?.name || ""),
  household: "",
  advanced: false,
  canInvite: false,
  canManage: false,
  canOrganize: false,
  password: "",
  authMethod: "Mealie",
});

const disabledFields = computed(() => {
  const fields: string[] = [];
  if (newUserData.value.admin) {
    fields.push("canManageHousehold", "canManage", "advanced");
  }
  if (newUserData.value.admin) {
    fields.push("canOrganize", "canInvite");
  }
  return fields;
});

watch(
  () => newUserData.value.admin,
  (isAdmin, wasAdmin) => {
    if (isAdmin && !wasAdmin) {
      newUserData.value.canManageHousehold = true;
      newUserData.value.canManage = true;
      newUserData.value.canOrganize = true;
      newUserData.value.canInvite = true;
      newUserData.value.advanced = true;
    }
    else if (!isAdmin && wasAdmin) {
      newUserData.value.canManageHousehold = false;
      newUserData.value.canManage = false;
      newUserData.value.canOrganize = false;
      newUserData.value.canInvite = false;
      newUserData.value.advanced = false;
    }
  },
);

async function handleSubmit() {
  const { valid } = (await refNewUserForm.value?.validate()) ?? {
    valid: false,
  };

  if (!valid) return;

  const { response } = await adminApi.users.createOne(
    newUserData.value as UserIn,
  );

  if (response?.status === 201) {
    router.push("/admin/manage/users");
  }
}
</script>

<style lang="scss" scoped></style>
