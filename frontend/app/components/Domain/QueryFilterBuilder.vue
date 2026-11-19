<template>
  <div class="flex flex-col gap-3 font-sans">
    <VueDraggable
      v-model="fields"
      handle=".handle"
      :delay="250"
      :delay-on-touch-only="true"
      class="flex flex-col gap-2"
      v-bind="{
        animation: 200,
        group: 'query-filter-fields',
        ghostClass: 'opacity-50',
      }"
      @start="drag = true"
      @end="onDragEnd"
    >
      <div
        v-for="(field, index) in fields"
        :key="field.id"
        class="flex flex-wrap items-center gap-2 rounded-card border bg-background p-2"
      >
        <button
          type="button"
          class="handle inline-flex h-10 w-6 shrink-0 cursor-grab touch-none items-center justify-center rounded-item text-muted-foreground hover:bg-highlight hover:text-foreground"
          :aria-label="$t('general.drag-to-reorder')"
          :title="$t('general.drag-to-reorder')"
        >
          <GripVerticalIcon class="size-4" />
        </button>

        <!-- and / or -->
        <select
          v-if="index"
          :value="field.logicalOperator?.value"
          :aria-label="$t('query-filter.logical-operator')"
          class="h-10 min-w-0 rounded-control border border-input bg-card px-2.5 text-[15px] outline-none focus:border-ring focus:ring-3 focus:ring-ring/25 w-20"
          @change="setLogicalOperatorValue(field, index, ($event.target as HTMLSelectElement).value as unknown as LogicalOperator)"
        >
          <option
            v-for="op in [logOps.AND, logOps.OR]"
            :key="op.value"
            :value="op.value"
          >
            {{ op.label }}
          </option>
        </select>
        <span
          v-else
          class="w-20 px-1 text-sm font-semibold text-muted-foreground"
        >{{ $t('query-filter.where') }}</span>

        <select
          v-if="showAdvanced"
          :value="field.leftParenthesis ?? ''"
          :aria-label="$t('query-filter.open-parenthesis')"
          class="h-10 min-w-0 rounded-control border border-input bg-card px-2.5 text-[15px] outline-none focus:border-ring focus:ring-3 focus:ring-ring/25 w-16 font-mono"
          @change="setLeftParenthesisValue(field, index, ($event.target as HTMLSelectElement).value)"
        >
          <option
            v-for="p in ['', '(', '((', '(((']"
            :key="p"
            :value="p"
          >
            {{ p || '–' }}
          </option>
        </select>

        <!-- field name -->
        <select
          :value="field.label"
          :aria-label="$t('query-filter.field')"
          class="h-10 min-w-0 rounded-control border border-input bg-card px-2.5 text-[15px] outline-none focus:border-ring focus:ring-3 focus:ring-ring/25 w-44 grow sm:grow-0"
          @change="setField(index, ($event.target as HTMLSelectElement).value)"
        >
          <option
            v-for="def in fieldDefs"
            :key="def.label"
            :value="def.label"
          >
            {{ def.label }}
          </option>
        </select>

        <!-- relational operator -->
        <select
          v-if="field.type !== 'boolean'"
          :value="field.relationalOperatorValue?.value"
          :aria-label="$t('query-filter.operator')"
          class="h-10 min-w-0 rounded-control border border-input bg-card px-2.5 text-[15px] outline-none focus:border-ring focus:ring-3 focus:ring-ring/25 w-40 grow sm:grow-0"
          @change="updateRelationalOperator(field, ($event.target as HTMLSelectElement).value as unknown as RelationalKeyword | RelationalOperator)"
        >
          <option
            v-for="op in field.relationalOperatorChoices"
            :key="op.value"
            :value="op.value"
          >
            {{ op.label }}
          </option>
        </select>

        <!-- value -->
        <div
          v-if="!isNullOperator(field.relationalOperatorValue)"
          class="min-w-48 flex-1"
        >
          <Popover v-if="field.fieldChoices">
            <PopoverTrigger as-child>
              <button
                type="button"
                class="h-10 min-w-0 rounded-control border border-input bg-card px-2.5 text-[15px] outline-none focus:border-ring focus:ring-3 focus:ring-ring/25 flex w-full items-center justify-between gap-2 text-left"
                :aria-label="$t('query-filter.value')"
              >
                <span class="truncate">{{ choiceSummary(field) || $t('query-filter.choose-values') }}</span>
                <ChevronDownIcon class="size-4 shrink-0 opacity-60" />
              </button>
            </PopoverTrigger>
            <PopoverContent
              align="start"
              class="max-h-72 w-64 overflow-y-auto p-1"
            >
              <label
                v-for="choice in field.fieldChoices"
                :key="String(choice.value)"
                class="flex cursor-pointer items-center gap-2.5 rounded-item px-2 py-1.5 text-[15px] hover:bg-highlight"
              >
                <Checkbox
                  :model-value="(field.values || []).includes(choice.value)"
                  @update:model-value="toggleChoice(field, index, choice.value, !!$event)"
                />
                {{ choice.label }}
              </label>
            </PopoverContent>
          </Popover>
          <input
            v-else-if="field.type === 'string'"
            :value="field.value"
            type="text"
            :aria-label="$t('query-filter.value')"
            class="h-10 min-w-0 rounded-control border border-input bg-card px-2.5 text-[15px] outline-none focus:border-ring focus:ring-3 focus:ring-ring/25 w-full"
            @input="setFieldValue(field, index, ($event.target as HTMLInputElement).value)"
          >
          <input
            v-else-if="field.type === 'number'"
            :value="field.value as number || 0"
            type="number"
            min="0"
            max="5"
            step="any"
            :aria-label="$t('query-filter.value')"
            class="h-10 min-w-0 rounded-control border border-input bg-card px-2.5 text-[15px] outline-none focus:border-ring focus:ring-3 focus:ring-ring/25 w-28"
            @input="setFieldValue(field, index, Number(($event.target as HTMLInputElement).value) || 0)"
          >
          <label
            v-else-if="field.type === 'boolean'"
            class="flex h-10 items-center gap-2"
          >
            <Checkbox
              :model-value="!!field.value"
              @update:model-value="setFieldValue(field, index, !!$event)"
            />
          </label>
          <input
            v-else-if="field.type === 'date'"
            :value="field.value"
            type="date"
            :aria-label="$t('query-filter.value')"
            class="h-10 min-w-0 rounded-control border border-input bg-card px-2.5 text-[15px] outline-none focus:border-ring focus:ring-3 focus:ring-ring/25 w-44 [color-scheme:light] dark:[color-scheme:dark]"
            @change="setFieldValue(field, index, ($event.target as HTMLInputElement).value)"
          >
          <!--
            Relative dates are assumed to be negative intervals with a unit of days.
            The input is a *positive*, interpreted internally as a *negative* offset.
          -->
          <label
            v-else-if="field.type === 'relativeDate'"
            class="flex h-10 w-48 items-center gap-2 rounded-control border border-input bg-card pe-3 focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/25"
          >
            <input
              :value="parseRelativeDateOffset(field.value)"
              type="number"
              min="0"
              step="1"
              :aria-label="$t('query-filter.value')"
              class="h-full w-0 min-w-0 flex-1 bg-transparent px-2.5 text-[15px] outline-none"
              @input="setFieldValue(field, index, Math.max(0, Math.floor(Number(($event.target as HTMLInputElement).value) || 0)))"
            >
            <span class="text-sm text-muted-foreground">{{ $t('query-filter.dates.days-ago', parseRelativeDateOffset(field.value)) }}</span>
          </label>
          <RecipeTimeInput
            v-else-if="field.type === 'duration'"
            :seconds="field.value as number || null"
            hide-text
            @update:seconds="setFieldValue(field, index, $event ?? '')"
          />
          <RecipeOrganizerSelector
            v-else-if="organizerTypes.includes(field.type as Organizer)"
            v-model="field.organizers"
            :selector-type="field.type as Organizer"
            :show-add="false"
            :show-label="false"
            :show-icon="false"
            @update:model-value="val => setFieldOrganizers(field, index, (val || []) as OrganizerBase[])"
          />
        </div>

        <select
          v-if="showAdvanced"
          :value="field.rightParenthesis ?? ''"
          :aria-label="$t('query-filter.close-parenthesis')"
          class="h-10 min-w-0 rounded-control border border-input bg-card px-2.5 text-[15px] outline-none focus:border-ring focus:ring-3 focus:ring-ring/25 w-16 font-mono"
          @change="setRightParenthesisValue(field, index, ($event.target as HTMLSelectElement).value)"
        >
          <option
            v-for="p in ['', ')', '))', ')))']"
            :key="p"
            :value="p"
          >
            {{ p || '–' }}
          </option>
        </select>

        <Button
          variant="ghost"
          size="icon"
          class="ms-auto text-muted-foreground hover:text-destructive"
          :disabled="fields.length === 1"
          :aria-label="$t('general.delete')"
          :title="$t('general.delete')"
          @click="removeField(index)"
        >
          <Trash2Icon class="size-4" />
        </Button>
      </div>
    </VueDraggable>
    <div class="flex flex-wrap items-center justify-end gap-3">
      <label class="flex cursor-pointer items-center gap-2 text-sm">
        <Checkbox v-model="showAdvanced" />
        {{ $t('general.show-advanced') }}
      </label>
      <Button
        variant="outline"
        @click="addField(fieldDefs[0]!)"
      >
        <PlusIcon class="size-4" />
        {{ $t('general.add-field') }}
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ChevronDownIcon, GripVerticalIcon, PlusIcon, Trash2Icon } from "@lucide/vue";
import { VueDraggable } from "vue-draggable-plus";
import { Button } from "~/components/ui/button";
import { Checkbox } from "~/components/ui/checkbox";
import { Popover, PopoverContent, PopoverTrigger } from "~/components/ui/popover";
import { useDebounceFn } from "@vueuse/core";
import RecipeOrganizerSelector from "~/components/Domain/Recipe/RecipeOrganizerSelector.vue";
import RecipeTimeInput from "~/components/Domain/Recipe/RecipeTimeInput.vue";
import { Organizer } from "~/lib/api/types/non-generated";
import type {
  LogicalOperator,
  QueryFilterJSON,
  QueryFilterJSONPart,
  RelationalKeyword,
  RelationalOperator,
} from "~/lib/api/types/non-generated";
import { useCategoryStore, useFoodStore, useHouseholdStore, useLabelStore, useTagStore, useToolStore } from "~/composables/store";
import { useUserStore } from "~/composables/store/use-user-store";
import { type Field, type FieldDefinition, type FieldValue, type OrganizerBase, useQueryFilterBuilder } from "~/composables/use-query-filter-builder";

const props = defineProps({
  fieldDefs: {
    type: Array as () => FieldDefinition[],
    required: true,
  },
  initialQueryFilter: {
    type: Object as () => QueryFilterJSON | null,
    default: null,
  },
});

const emit = defineEmits<{
  (event: "input", value: string | undefined): void;
  (event: "inputJSON", value: QueryFilterJSON | undefined): void;
}>();

const {
  logOps,
  placeholderKeywords,
  getRelOps,
  buildQueryFilterString,
  getFieldFromFieldDef,
  isOrganizerType,
  isNullOperator,
  updateRelationalOperator,
} = useQueryFilterBuilder();

const state = reactive({
  showAdvanced: false,
  qfValid: false,
  datePickers: [] as boolean[],
  drag: false,
});
const { showAdvanced, drag } = toRefs(state);

const storeMap = {
  [Organizer.Category]: useCategoryStore(),
  [Organizer.Tag]: useTagStore(),
  [Organizer.Tool]: useToolStore(),
  [Organizer.Food]: useFoodStore(),
  [Organizer.Label]: useLabelStore(),
  [Organizer.Household]: useHouseholdStore(),
  [Organizer.User]: useUserStore(),
};

function onDragEnd(event: any) {
  state.drag = false;

  const oldIndex: number = event.oldIndex;
  const newIndex: number = event.newIndex;
  state.datePickers[oldIndex] = false;
  state.datePickers[newIndex] = false;
}

// add id to fields to prevent reactivity issues
type FieldWithId = Field & { id: number };
const fields = ref<FieldWithId[]>([]);

const uid = ref(1); // init uid to pass to fields
function useUid() {
  return uid.value++;
}
function addField(field: FieldDefinition) {
  fields.value.push({
    ...getFieldFromFieldDef(field),
    id: useUid(),
  });
  state.datePickers.push(false);
}

function setField(index: number, fieldLabel: string) {
  state.datePickers[index] = false;
  const fieldDef = props.fieldDefs.find(fieldDef => fieldDef.label === fieldLabel);
  if (!fieldDef) {
    return;
  }

  const resetValue = (fieldDef.type !== fields.value[index]!.type) || (fieldDef.fieldChoices !== fields.value[index]!.fieldChoices);
  const updatedField = { ...fields.value[index], ...fieldDef };

  // we have to set this explicitly since it might be undefined
  updatedField.fieldChoices = fieldDef.fieldChoices;

  fields.value[index] = {
    ...getFieldFromFieldDef(updatedField, resetValue),
    id: fields.value[index]!.id, // keep the id
  };

  // Defaults
  switch (fields.value[index].type) {
    case "date":
      fields.value[index].value = safeNewDate("");
      break;
    case "relativeDate":
      fields.value[index].value = "$NOW-30d";
      break;
    case "duration":
      fields.value[index].value = 30 * 60;
      break;

    default:
      break;
  }
}

function setLeftParenthesisValue(field: FieldWithId, index: number, value: string) {
  fields.value[index]!.leftParenthesis = value;
}

function setRightParenthesisValue(field: FieldWithId, index: number, value: string) {
  fields.value[index]!.rightParenthesis = value;
}

function setLogicalOperatorValue(field: FieldWithId, index: number, value: LogicalOperator | undefined) {
  if (!value) {
    value = logOps.value.AND.value;
  }

  fields.value[index]!.logicalOperator = value ? logOps.value[value] : undefined;
}

function setFieldValue(field: FieldWithId, index: number, value: FieldValue) {
  state.datePickers[index] = false;

  if (field.type === "relativeDate") {
    // Value is set to an int representing the offset from $NOW
    // Values are assumed to be negative offsets ('-') with a unit of days ('d')
    fields.value[index]!.value = `$NOW-${Math.abs(value)}d`;
  }
  else {
    fields.value[index]!.value = value;
  }
}

function setFieldValues(field: FieldWithId, index: number, values: FieldValue[]) {
  fields.value[index]!.values = values;
}

function toggleChoice(field: FieldWithId, index: number, value: FieldValue, on: boolean) {
  const current = field.values || [];
  setFieldValues(field, index, on ? [...current, value] : current.filter(v => v !== value));
}

function choiceSummary(field: FieldWithId) {
  const chosen = (field.fieldChoices || []).filter(c => (field.values || []).includes(c.value)).map(c => c.label);
  return chosen.join(", ");
}

const organizerTypes = [Organizer.Category, Organizer.Tag, Organizer.Tool, Organizer.Food, Organizer.Household, Organizer.User, Organizer.Label];

function setFieldOrganizers(field: FieldWithId, index: number, organizers: OrganizerBase[]) {
  fields.value[index]!.organizers = organizers;
  // Sync the values array with the organizers array
  fields.value[index]!.values = organizers.map(org => org.id?.toString() || "").filter(id => id);
}

function removeField(index: number) {
  fields.value.splice(index, 1);
  state.datePickers.splice(index, 1);
}

const fieldsUpdater = useDebounceFn(() => {
  const qf = buildQueryFilterString(fields.value, state.showAdvanced);
  if (qf) {
    console.debug(`Set query filter: ${qf}`);
  }
  state.qfValid = !!qf;

  emit("input", qf || undefined);
  emit("inputJSON", qf ? buildQueryFilterJSON() : undefined);
}, 500);

watch(fields, fieldsUpdater, { deep: true });

async function hydrateOrganizers(field: FieldWithId, _index: number) {
  if (!field.values?.length || !isOrganizerType(field.type)) {
    return;
  }

  const { store, actions } = storeMap[field.type];
  if (!store.value.length) {
    await actions.refresh();
  }

  const organizers = field.values.map((value) => {
    const organizer = store.value.find(item => item?.id?.toString() === value);
    if (!organizer) {
      console.error(`Could not find organizer with id ${value}`);
      return undefined;
    }
    return organizer;
  });

  field.organizers = organizers.filter(organizer => organizer !== undefined) as OrganizerBase[];
  return field;
}

function initFieldsError(error = "") {
  if (error) {
    console.error(error);
  }

  fields.value = [];
  if (props.fieldDefs.length) {
    addField(props.fieldDefs[0]!);
  }
}

async function initializeFields() {
  if (!props.initialQueryFilter?.parts?.length) {
    return initFieldsError();
  }

  const initFields: FieldWithId[] = [];
  let error = false;

  for (const [index, part] of props.initialQueryFilter.parts.entries()) {
    const fieldDef = props.fieldDefs.find(fieldDef => fieldDef.name === part.attributeName);
    if (!fieldDef) {
      error = true;
      return initFieldsError(`Invalid query filter; unknown attribute name "${part.attributeName || ""}"`);
    }

    const field: FieldWithId = {
      ...getFieldFromFieldDef(fieldDef),
      id: useUid(),
    };

    const relOps = getRelOps(field.type);

    field.leftParenthesis = part.leftParenthesis || field.leftParenthesis;
    field.rightParenthesis = part.rightParenthesis || field.rightParenthesis;
    field.logicalOperator = part.logicalOperator
      ? logOps.value[part.logicalOperator]
      : field.logicalOperator;
    field.relationalOperatorValue = part.relationalOperator
      ? relOps.value[part.relationalOperator]
      : field.relationalOperatorValue;
    field.relationalOperatorValue = part.relationalOperator
      ? relOps.value[part.relationalOperator]
      : field.relationalOperatorValue;

    if (field.leftParenthesis || field.rightParenthesis) {
      state.showAdvanced = true;
    }

    if (isNullOperator(field.relationalOperatorValue)) {
      field.value = "";
    }
    else if (field.fieldChoices?.length || isOrganizerType(field.type)) {
      if (typeof part.value === "string") {
        field.values = part.value ? [part.value] : [];
      }
      else {
        field.values = part.value || [];
      }

      if (isOrganizerType(field.type)) {
        await hydrateOrganizers(field, index);
      }
    }
    else if (field.type === "boolean") {
      const boolString = part.value || "false";
      field.value = (
        boolString[0].toLowerCase() === "t"
        || boolString[0].toLowerCase() === "y"
        || boolString[0] === "1"
      );
    }
    else if (field.type === "number" || field.type === "duration") {
      field.value = Number(part.value as string || "0");
      if (isNaN(field.value)) {
        error = true;
        return initFieldsError(`Invalid query filter; invalid number value "${(part.value || "").toString()}"`);
      }
    }
    else if (field.type === "date") {
      field.value = part.value as string || "";
      const date = new Date(field.value);
      if (isNaN(date.getTime())) {
        error = true;
        return initFieldsError(`Invalid query filter; invalid date value "${(part.value || "").toString()}"`);
      }
    }
    else {
      field.value = part.value as string || "";
    }

    initFields.push(field);
  }

  if (initFields.length && !error) {
    fields.value = initFields;
  }
  else {
    initFieldsError();
  }
}

onMounted(async () => {
  try {
    await initializeFields();
  }
  catch (error) {
    initFieldsError(`Error initializing fields: ${(error || "").toString()}`);
  }
});

function buildQueryFilterJSON(): QueryFilterJSON {
  const parts = fields.value.map((field) => {
    const part: QueryFilterJSONPart = {
      attributeName: field.name,
      leftParenthesis: field.leftParenthesis,
      rightParenthesis: field.rightParenthesis,
      logicalOperator: field.logicalOperator?.value,
      relationalOperator: field.relationalOperatorValue?.value,
    };

    if (isNullOperator(field.relationalOperatorValue)) {
      part.value = null;
    }
    else if (field.fieldChoices?.length || isOrganizerType(field.type)) {
      part.value = field.values.map(value => value.toString());
    }
    else if (field.type === "boolean") {
      part.value = field.value ? "true" : "false";
    }
    else {
      part.value = (field.value || "").toString();
    }

    return part;
  });

  const qfJSON = { parts } as QueryFilterJSON;
  console.debug(`Built query filter JSON: ${JSON.stringify(qfJSON)}`);
  return qfJSON;
}

function safeNewDate(input: string): Date {
  const date = new Date(input);
  if (isNaN(date.getTime())) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return today;
  }
  return date;
}

/**
 * Parse a relative date string offset (e.g. $NOW-30d --> 30)
 *
 * Currently only values with a negative offset ('-') and a unit of days ('d') are supported
 */
function parseRelativeDateOffset(value: string): number {
  const defaultVal = 30;
  if (!value) {
    return defaultVal;
  }

  try {
    if (!value.startsWith(placeholderKeywords.value["$NOW"].value)) {
      return defaultVal;
    }

    const remainder = value.slice(placeholderKeywords.value["$NOW"].value.length);
    if (!remainder.startsWith("-")) {
      throw new Error("Invalid operator (not '-')");
    }

    if (remainder.slice(-1) !== "d") {
      throw new Error("Invalid unit (not 'd')");
    }

    // Slice off sign and unit
    return parseInt(remainder.slice(1, -1));
  }
  catch (error) {
    console.warn(`Unable to parse relative date offset from '${value}': ${error}`);
    return defaultVal;
  }
}
</script>
