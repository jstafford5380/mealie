<template>
  <div class="mx-auto w-full max-w-[1000px] px-4 pb-16 pt-3 font-sans sm:px-6 lg:pt-8">
    <!-- Create Dialog -->
    <BaseDialog
      v-if="createTarget"
      v-model="dialogStates.create"
      width="100%"
      max-width="1100px"
      :icon="$globals.icons.pages"
      :title="$t('cookbook.create-a-cookbook')"
      :submit-icon="$globals.icons.save"
      :submit-text="$t('general.save')"
      :submit-disabled="!createTarget.queryFilterString"
      can-submit
      disable-submit-on-enter
      @submit="actions.updateOne(createTarget)"
      @cancel="deleteCreateTarget()"
    >
      <div class="px-6 pb-2">
        <CookbookEditor
          :key="createTargetKey"
          v-model="createTarget"
        />
      </div>
    </BaseDialog>

    <!-- Delete Dialog -->
    <BaseDialog
      v-model="dialogStates.delete"
      :title="$t('general.delete-with-name', { name: $t('cookbook.cookbook') })"
      :icon="$globals.icons.alertCircle"
      color="error"
      can-confirm
      @confirm="deleteCookbook()"
    >
      <div class="flex flex-col gap-3 px-6 pb-2 text-[15px]">
        <p class="m-0">
          {{ $t("general.confirm-delete-generic-with-name", { name: $t("cookbook.cookbook") }) }}
        </p>
        <p
          v-if="deleteTarget"
          class="m-0 rounded-control bg-muted px-3 py-2 font-semibold"
        >
          {{ deleteTarget.name }}
        </p>
      </div>
    </BaseDialog>

    <header class="mb-4 flex flex-wrap items-end gap-3">
      <div class="min-w-0 flex-1">
        <h1 class="m-0 text-[26px] font-bold tracking-tight sm:text-[32px]">
          {{ $t("cookbook.cookbooks") }}
        </h1>
        <p class="m-0 mt-1 max-w-[65ch] text-[15px] text-muted-foreground">
          {{ $t("cookbook.description") }}
        </p>
      </div>
      <Button @click="createCookbook">
        <PlusIcon class="size-4" />
        {{ $t('cookbook.create-a-cookbook') }}
      </Button>
    </header>

    <div class="mb-6">
      <CheckboxField
        v-model="cookbookPreferences.hideOtherHouseholds"
        :label="$t('cookbook.hide-cookbooks-from-other-households')"
        :hint="$t('cookbook.hide-cookbooks-from-other-households-description')"
      />
    </div>

    <Accordion
      v-if="myCookbooks.length"
      type="single"
      collapsible
      class="rounded-card border bg-card"
    >
      <VueDraggable
        v-model="myCookbooks"
        handle=".handle"
        :delay="250"
        :delay-on-touch-only="true"
        @end="updateAll(myCookbooks)"
      >
        <AccordionItem
          v-for="(cookbook, index) in myCookbooks"
          :key="cookbook.id"
          :value="cookbook.id"
          class="last:border-b-0"
        >
          <div class="flex items-center">
            <span
              class="handle ms-1 inline-flex size-9 shrink-0 cursor-grab touch-none items-center justify-center rounded-full text-muted-foreground hover:bg-highlight active:cursor-grabbing"
              :aria-label="$t('general.drag-to-reorder')"
              :title="$t('general.drag-to-reorder')"
            >
              <GripVerticalIcon class="size-4" />
            </span>
            <AccordionTrigger class="min-w-0 flex-1 py-3.5 pe-4">
              <span class="flex min-w-0 items-center gap-3">
                <MdiIcon
                  :path="$globals.icons.pages"
                  class="size-5 shrink-0 text-muted-foreground"
                />
                <span class="truncate">{{ cookbook.name }}</span>
                <span
                  v-if="cookbook.public"
                  class="rounded-full bg-subtle px-2 py-0.5 text-xs font-semibold text-subtle-foreground"
                >{{ $t('cookbook.public') }}</span>
              </span>
            </AccordionTrigger>
          </div>
          <AccordionContent class="px-4">
            <CookbookEditor
              v-model="myCookbooks[index]"
              :collapsable="false"
            />
            <div class="mt-4 flex flex-wrap items-center gap-2 border-t pt-4">
              <Button
                variant="ghost"
                class="text-destructive hover:text-destructive"
                @click="deleteEventHandler(myCookbooks[index]!)"
              >
                <Trash2Icon class="size-4" />
                {{ $t('general.delete') }}
              </Button>
              <Button
                class="ms-auto"
                :disabled="!cookbook.queryFilterString"
                @click="actions.updateOne(myCookbooks[index]!)"
              >
                {{ $t('general.save') }}
              </Button>
            </div>
          </AccordionContent>
        </AccordionItem>
      </VueDraggable>
    </Accordion>
    <p
      v-else
      class="m-0 rounded-card border border-dashed px-4 py-8 text-center text-sm text-muted-foreground"
    >
      {{ $t('cookbook.no-cookbooks-yet') }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { GripVerticalIcon, PlusIcon, Trash2Icon } from "@lucide/vue";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "~/components/ui/accordion";
import { Button } from "~/components/ui/button";
import CheckboxField from "~/components/ui/field/CheckboxField.vue";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { VueDraggable } from "vue-draggable-plus";
import { useCookbookStore } from "~/composables/store/use-cookbook-store";
import { useHouseholdSelf } from "@/composables/use-households";
import CookbookEditor from "~/components/Domain/Cookbook/CookbookEditor.vue";
import type { CookBookCreate, CookBookOut } from "~/lib/api/types/cookbook";
import { useCookbookPreferences } from "~/composables/use-users/preferences";

definePageMeta({
  middleware: ["auth", "group-only"],
});

const dialogStates = reactive({
  create: false,
  delete: false,
});

const i18n = useI18n();

// Set page title
useSeoMeta({
  title: i18n.t("cookbook.cookbooks"),
});

const auth = useMealieAuth();
const { store: allCookbooks, actions, updateAll } = useCookbookStore();

// Make a local reactive copy of myCookbooks
const myCookbooks = ref<CookBookOut[]>([]);
watch(
  allCookbooks,
  (cookbooks) => {
    myCookbooks.value
      = cookbooks?.filter(
        cookbook => cookbook.householdId === auth.user.value?.householdId,
      ).sort((a, b) => a.position > b.position) ?? [];
  },
  { immediate: true },
);

const { household } = useHouseholdSelf();
const cookbookPreferences = useCookbookPreferences();

// create
const createTargetKey = ref(0);
const createTarget = ref<CookBookOut | null>(null);
async function createCookbook() {
  const name = i18n.t("cookbook.household-cookbook-name", [
    household.value?.name || "",
    String((myCookbooks.value?.length ?? 0) + 1),
  ]) as string;

  const data = { name } as CookBookCreate;
  await actions.createOne(data).then((cookbook) => {
    if (!cookbook) {
      return;
    }

    myCookbooks.value.push(cookbook);
    createTarget.value = cookbook as CookBookOut;
    createTargetKey.value++;
  });
  dialogStates.create = true;
}

// delete
const deleteTarget = ref<CookBookOut | null>(null);
function deleteEventHandler(item: CookBookOut) {
  deleteTarget.value = item;
  dialogStates.delete = true;
}
async function deleteCookbook() {
  if (!deleteTarget.value) {
    return;
  }
  await actions.deleteOne(deleteTarget.value.id);
  myCookbooks.value = myCookbooks.value.filter(c => c.id !== deleteTarget.value?.id);
  dialogStates.delete = false;
  deleteTarget.value = null;
}

async function deleteCreateTarget() {
  if (!createTarget.value?.id) {
    return;
  }
  await actions.deleteOne(createTarget.value.id);
  myCookbooks.value = myCookbooks.value.filter(c => c.id !== createTarget.value?.id);
  dialogStates.create = false;
  createTarget.value = null;
}
function handleUnmount() {
  if (!createTarget.value?.id || createTarget.value.queryFilterString) {
    return;
  }
  deleteCreateTarget();
}
onMounted(() => {
  window.addEventListener("beforeunload", handleUnmount);
});
onBeforeUnmount(() => {
  handleUnmount();
  window.removeEventListener("beforeunload", handleUnmount);
});
</script>
