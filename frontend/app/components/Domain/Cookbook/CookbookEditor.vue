<template>
  <div
    v-if="cookbook"
    class="flex flex-col gap-1 font-sans"
  >
    <TextField
      v-model="cookbook.name"
      :label="$t('cookbook.cookbook-name')"
    />
    <TextareaField
      v-model="cookbook.description"
      auto-grow
      :rows="2"
      :label="$t('recipe.description')"
    />
    <div class="mt-2">
      <p class="m-0 mb-2 text-sm font-semibold">
        {{ $t('cookbook.which-recipes') }}
      </p>
      <QueryFilterBuilder
        :field-defs="fieldDefs"
        :initial-query-filter="cookbook.queryFilter"
        @input="handleInput"
      />
    </div>
    <label class="mt-3 flex cursor-pointer items-start gap-3">
      <Switch
        v-model="cookbook.public"
        class="mt-0.5"
      />
      <span>
        <span class="block text-[15px] font-semibold">{{ $t('cookbook.public-cookbook') }}</span>
        <span class="block text-sm text-muted-foreground">{{ $t('cookbook.public-cookbook-description') }}</span>
      </span>
    </label>
  </div>
</template>

<script setup lang="ts">
import TextareaField from "~/components/ui/field/TextareaField.vue";
import TextField from "~/components/ui/field/TextField.vue";
import { Switch } from "~/components/ui/switch";
import QueryFilterBuilder from "~/components/Domain/QueryFilterBuilder.vue";
import { useRecipeFilterFields } from "~/composables/use-recipe-filter-fields";
import type { CookBookOut } from "~/lib/api/types/cookbook";

const modelValue = defineModel<CookBookOut>({ required: true });
const cookbook = toRef(modelValue);
function handleInput(value: string | undefined) {
  cookbook.value.queryFilterString = value || "";
}

const fieldDefs = useRecipeFilterFields();
</script>
