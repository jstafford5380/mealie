<template>
  <div
    v-if="preferences"
    class="flex flex-col gap-3 font-sans"
  >
    <div>
      <CheckboxField
        v-model="local.privateGroup"
        :label="$t('group.private-group')"
        :hint="$t('group.private-group-description')"
      />
      <DocLink
        class="ms-7"
        link="/documentation/getting-started/faq/#how-do-private-groups-households-and-recipes-work"
      />
    </div>
    <CheckboxField
      v-model="local.showAnnouncements"
      :label="$t('announcements.show-announcements-from-mealie')"
      :hint="$t('announcements.show-announcements-setting-description')"
    />
  </div>
</template>

<script setup lang="ts">
import CheckboxField from "~/components/ui/field/CheckboxField.vue";
import type { GroupPreferencesOut } from "~/lib/api/types/user";

const preferences = defineModel<GroupPreferencesOut>({ required: true });
const local = reactive({ ...preferences.value });
watch(local, (newVal) => { preferences.value = { ...newVal }; });
watch(preferences, (newVal) => { if (newVal) Object.assign(local, newVal); });
</script>
