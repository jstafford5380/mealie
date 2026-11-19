<template>
  <div>
    <BaseDialog
      v-model="dialog"
      :title="$t('data-pages.manage-aliases')"
      :icon="$globals.icons.edit"
      :submit-icon="$globals.icons.check"
      :submit-text="$t('general.confirm')"
      can-submit
      @submit="saveAliases"
      @cancel="$emit('cancel')"
    >
      <div class="flex flex-col gap-2 px-6 pb-2">
        <p class="m-0 text-sm text-muted-foreground">
          {{ $t('data-pages.aliases-help', { name: data.name }) }}
        </p>
        <div
          v-for="alias, i in aliases"
          :key="i"
          class="flex items-end gap-2"
        >
          <div class="min-w-0 flex-1">
            <TextField
              v-model="alias.name"
              :label="i === 0 ? $t('general.name') : undefined"
              :aria-label="$t('general.name')"
              :autofocus="i === aliases.length - 1 && i > 0"
              :rules="[validators.required]"
            />
          </div>
          <button
            type="button"
            class="mb-1.5 inline-flex size-10 shrink-0 items-center justify-center rounded-full text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
            :aria-label="$t('general.delete')"
            :title="$t('general.delete')"
            @click="deleteAlias(i)"
          >
            <Trash2Icon class="size-4" />
          </button>
        </div>
        <Button
          variant="outline"
          class="self-start"
          @click="createAlias"
        >
          <PlusIcon class="size-4" />
          {{ $t('data-pages.create-alias') }}
        </Button>
      </div>
    </BaseDialog>
  </div>
</template>

<script setup lang="ts">
import { PlusIcon, Trash2Icon } from "@lucide/vue";
import { Button } from "~/components/ui/button";
import TextField from "~/components/ui/field/TextField.vue";
import { whenever } from "@vueuse/core";
import { validators } from "~/composables/use-validators";
import type { IngredientFoodOut, IngredientUnitOut } from "~/lib/api/types/recipe";

export interface GenericAlias {
  name: string;
}

interface Props {
  data: IngredientFoodOut | IngredientUnitOut;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  submit: [aliases: GenericAlias[]];
  cancel: [];
}>();

// V-Model Support
const dialog = defineModel<boolean>({ default: false });

function createAlias() {
  aliases.value.push({
    name: "",
  });
}

function deleteAlias(index: number) {
  aliases.value.splice(index, 1);
}

const aliases = ref<GenericAlias[]>([]);
function initAliases() {
  aliases.value = (props.data.aliases || []).map(alias => ({ ...alias }));
  if (!aliases.value.length) {
    createAlias();
  }
}

initAliases();
whenever(
  () => dialog.value,
  () => {
    initAliases();
  },
);

function saveAliases() {
  const seenAliasNames: string[] = [];
  const keepAliases: GenericAlias[] = [];
  aliases.value.forEach((alias) => {
    const abbreviation = "abbreviation" in props.data ? props.data.abbreviation : undefined;
    const pluralAbbreviation = "pluralAbbreviation" in props.data ? props.data.pluralAbbreviation : undefined;
    if (
      !alias.name
      || alias.name === props.data.name
      || alias.name === props.data.pluralName
      || alias.name === abbreviation
      || alias.name === pluralAbbreviation
      || seenAliasNames.includes(alias.name)
    ) {
      return;
    }

    keepAliases.push(alias);
    seenAliasNames.push(alias.name);
  });

  aliases.value = keepAliases;
  emit("submit", keepAliases);
}
</script>
