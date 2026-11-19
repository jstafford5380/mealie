<template>
  <div
    data-slot="auto-form"
    class="my-2 w-full px-2 font-sans"
    :style="width && width !== 'max' ? { maxWidth: typeof width === 'number' ? `${width}px` : width } : undefined"
  >
    <div class="grid grid-cols-12 gap-x-4">
      <template
        v-for="(inputField, index) in items"
        :key="index"
      >
        <div
          v-if="inputField.section"
          class="col-span-12 mt-2"
        >
          <Separator class="mb-4" />
          <h3 class="m-0 text-lg font-semibold tracking-tight">
            {{ inputField.section }}
          </h3>
          <p
            v-if="inputField.sectionDetails"
            class="m-0 mt-1 text-sm text-muted-foreground"
          >
            {{ inputField.sectionDetails }}
          </p>
        </div>
        <div
          class="col-span-12"
          :class="colClass(inputField.cols)"
        >
          <!-- Check Box -->
          <CheckboxField
            v-if="inputField.type === fieldTypes.BOOLEAN"
            v-model="model[inputField.varName]"
            :name="inputField.varName"
            :label="inputField.label"
            :hint="inputField.hint"
            :readonly="fieldState[inputField.varName]?.readonly"
            :disabled="fieldState[inputField.varName]?.disabled"
          >
            <template
              v-if="inputField.tooltip"
              #append-label
            >
              <TooltipProvider :delay-duration="150">
                <Tooltip>
                  <TooltipTrigger as-child>
                    <button
                      type="button"
                      class="inline-flex size-6 items-center justify-center rounded-full text-muted-foreground hover:text-foreground"
                      :aria-label="inputField.tooltip"
                    >
                      <MdiIcon
                        :path="$globals.icons.informationOutline"
                        class="size-4"
                      />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent
                    side="bottom"
                    class="max-w-72"
                  >
                    {{ inputField.tooltip }}
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </template>
          </CheckboxField>

          <!-- Text Field -->
          <TextField
            v-else-if="inputField.type === fieldTypes.TEXT || inputField.type === fieldTypes.PASSWORD"
            v-model="model[inputField.varName]"
            :readonly="fieldState[inputField.varName]?.readonly"
            :disabled="fieldState[inputField.varName]?.disabled"
            :type="inputField.type === fieldTypes.PASSWORD ? 'password' : 'text'"
            :autocomplete="inputField.type === fieldTypes.PASSWORD ? 'new-password' : undefined"
            :label="inputField.label"
            :name="inputField.varName"
            :hint="inputField.hint || ''"
            :rules="activeRules(inputField)"
          />

          <!-- Text Area -->
          <TextareaField
            v-else-if="inputField.type === fieldTypes.TEXT_AREA"
            v-model="model[inputField.varName]"
            :readonly="fieldState[inputField.varName]?.readonly"
            :disabled="fieldState[inputField.varName]?.disabled"
            :rows="3"
            auto-grow
            :label="inputField.label"
            :name="inputField.varName"
            :hint="inputField.hint || ''"
            :rules="activeRules(inputField)"
          />

          <!-- Number Input -->
          <NumberInputField
            v-else-if="inputField.type === fieldTypes.NUMBER"
            v-model="model[inputField.varName]"
            :control-variant="inputField.numberInputConfig?.controlVariant"
            :label="inputField.label"
            :name="inputField.varName"
            :min="inputField.numberInputConfig?.min"
            :max="inputField.numberInputConfig?.max"
            :precision="inputField.numberInputConfig?.precision ?? 0"
            :hint="inputField.hint"
            :readonly="fieldState[inputField.varName]?.readonly"
            :disabled="fieldState[inputField.varName]?.disabled"
            :rules="activeRules(inputField)"
          />

          <!-- Option Select -->
          <SelectField
            v-else-if="inputField.type === fieldTypes.SELECT"
            v-model="model[inputField.varName]"
            :readonly="fieldState[inputField.varName]?.readonly"
            :disabled="fieldState[inputField.varName]?.disabled"
            :label="inputField.label"
            :name="inputField.varName"
            :items="inputField.options || []"
            item-title="text"
            :item-value="inputField.selectReturnValue || 'text'"
            :hint="inputField.hint"
            :rules="activeRules(inputField)"
          />

          <!-- Color Picker -->
          <div
            v-else-if="inputField.type === fieldTypes.COLOR"
            class="flex w-full"
          >
            <InputColor v-model="model[inputField.varName]" />
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { AutoFormItems, FormField } from "~/types/auto-forms";
import CheckboxField from "~/components/ui/field/CheckboxField.vue";
import NumberInputField from "~/components/ui/field/NumberInputField.vue";
import SelectField from "~/components/ui/field/SelectField.vue";
import TextareaField from "~/components/ui/field/TextareaField.vue";
import TextField from "~/components/ui/field/TextField.vue";
import { MdiIcon } from "~/components/ui/mdi-icon";
import { Separator } from "~/components/ui/separator";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "~/components/ui/tooltip";
import { fieldTypes } from "~/composables/forms";
import { provideFieldGroup } from "~/composables/forms/use-field-validation";

// Use defineModel for v-model
const model = defineModel<Record<string, any> | any[]>({
  type: [Object, Array],
  required: true,
});
const isValid = defineModel("isValid", { type: Boolean, default: false });

const props = defineProps({
  updateMode: {
    default: false,
    type: Boolean,
  },
  items: {
    default: null,
    type: Array as () => AutoFormItems,
  },
  width: {
    type: [Number, String],
    default: "max",
  },
  /** Legacy Vuetify card colour; no longer used. */
  color: {
    default: null,
    type: String,
  },
  /** Legacy Vuetify dark flag; no longer used. */
  dark: {
    default: false,
    type: Boolean,
  },
  disabledFields: {
    default: null,
    type: Array as () => string[],
  },
  readonlyFields: {
    default: null,
    type: Array as () => string[],
  },
});

const group = provideFieldGroup();
// v-form reported null (not yet known) as falsy, so the model stays a boolean.
watch(group.isValid, (value) => {
  isValid.value = value === true;
}, { immediate: true });

// Combined state map for readonly and disabled fields
const fieldState = computed<Record<string, { readonly: boolean; disabled: boolean }>>(() => {
  const map: Record<string, { readonly: boolean; disabled: boolean }> = {};
  (props.items || []).forEach((field: any) => {
    const base = (field.disableUpdate && props.updateMode) || (!props.updateMode && field.disableCreate);
    map[field.varName] = {
      readonly: base || !!props.readonlyFields?.includes(field.varName),
      disabled: base || !!props.disabledFields?.includes(field.varName),
    };
  });
  return map;
});

function activeRules(field: FormField) {
  return !(field.disableUpdate && props.updateMode) ? field.rules || [] : [];
}

const COLS: Record<string, string> = {
  1: "sm:col-span-1",
  2: "sm:col-span-2",
  3: "sm:col-span-3",
  4: "sm:col-span-4",
  5: "sm:col-span-5",
  6: "sm:col-span-6",
  7: "sm:col-span-7",
  8: "sm:col-span-8",
  9: "sm:col-span-9",
  10: "sm:col-span-10",
  11: "sm:col-span-11",
  12: "sm:col-span-12",
  auto: "sm:col-auto",
};
function colClass(cols: FormField["cols"]) {
  return COLS[String(cols ?? 12)];
}

defineExpose({ validate: group.validate, reset: group.reset, resetValidation: group.resetValidation });
</script>
