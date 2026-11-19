import type { MaybeRefOrGetter, Ref } from "vue";
import type { FormValidationRule } from "~/types/auto-forms";

/**
 * Field validation for the new form controls, matching Vuetify's `rules` behaviour
 * (first failing rule's message, validate on input and blur, pristine until touched).
 *
 * While Vuetify is still in use the field registers with the nearest `<v-form>` through
 * Vuetify's public injection key, so `form.validate()`, `reset()`, `resetValidation()` and
 * `v-model` validity on legacy pages include the new controls. A future replacement form
 * only needs to provide the same shape under the same key.
 */
export const FORM_CONTEXT_KEY = Symbol.for("vuetify:form");

interface FormContext {
  register?: (item: {
    id: string;
    vm: unknown;
    validate: () => Promise<string[]>;
    reset: () => Promise<void>;
    resetValidation: () => Promise<void>;
  }) => void;
  unregister?: (id: string) => void;
  update?: (id: string, isValid: boolean | null, errorMessages: string[]) => void;
  isDisabled?: Ref<boolean>;
  isReadonly?: Ref<boolean>;
}

export interface FieldValidationOptions {
  rules: MaybeRefOrGetter<FormValidationRule[] | undefined>;
  errorMessages?: MaybeRefOrGetter<string | string[] | undefined>;
  name?: MaybeRefOrGetter<string | undefined>;
  /** "input" (default), "blur" or "submit"; mirrors Vuetify's validate-on. */
  validateOn?: MaybeRefOrGetter<string | undefined>;
  disabled?: MaybeRefOrGetter<boolean | undefined>;
  readonly?: MaybeRefOrGetter<boolean | undefined>;
}

export function useFieldValidation(model: Ref<unknown>, options: FieldValidationOptions) {
  const form = inject<FormContext | null>(FORM_CONTEXT_KEY, null);
  const fallbackId = useId();
  const id = computed(() => toValue(options.name) || `field-${fallbackId}`);

  const internalErrors = ref<string[]>([]);
  const isPristine = ref(true);
  let resetting = false;

  const rules = computed(() => toValue(options.rules) ?? []);
  const externalErrors = computed(() => {
    const value = toValue(options.errorMessages);
    if (!value) {
      return [];
    }
    return Array.isArray(value) ? value : [value];
  });
  const errorMessages = computed(() => [...externalErrors.value, ...internalErrors.value].slice(0, 1));

  const isValid = computed<boolean | null>(() => {
    if (externalErrors.value.length) {
      return false;
    }
    if (!rules.value.length) {
      return true;
    }
    if (isPristine.value) {
      // Untouched with failing rules is "unknown" (null), as in Vuetify; still blocks submit.
      return internalErrors.value.length ? null : true;
    }
    return !internalErrors.value.length;
  });

  const isDisabled = computed(() => !!(toValue(options.disabled) ?? form?.isDisabled?.value));
  const isReadonly = computed(() => !!(toValue(options.readonly) ?? form?.isReadonly?.value));
  /** Show an error only once the user has interacted with the field or a validate() ran. */
  const visibleError = computed(() => (isPristine.value ? externalErrors.value[0] : errorMessages.value[0]));

  async function validate(silent = false): Promise<string[]> {
    const results: string[] = [];
    for (const rule of rules.value) {
      const result = await (typeof rule === "function" ? rule(model.value) : rule);
      if (result === true) {
        continue;
      }
      if (result !== false && typeof result !== "string") {
        console.warn(`${result} is not a valid value. Rule functions must return boolean true or a string.`);
        continue;
      }
      results.push(result || "");
      break;
    }
    internalErrors.value = results;
    isPristine.value = silent;
    return results;
  }

  async function resetValidation() {
    isPristine.value = true;
    await validate(true);
  }

  async function reset() {
    resetting = true;
    model.value = null;
    await nextTick();
    resetting = false;
    await resetValidation();
  }

  const validateOn = computed(() => toValue(options.validateOn) || "input");

  watch(model, () => {
    if (!resetting && validateOn.value.includes("input")) {
      validate();
    }
  });

  function onBlur() {
    if (validateOn.value.includes("input") || validateOn.value.includes("blur")) {
      validate();
    }
  }

  const instance = getCurrentInstance();
  onBeforeMount(() => {
    form?.register?.({ id: id.value, vm: instance, validate: () => validate(), reset, resetValidation });
  });
  onBeforeUnmount(() => {
    form?.unregister?.(id.value);
  });
  onMounted(async () => {
    await validate(true);
    form?.update?.(id.value, isValid.value, errorMessages.value);
  });
  watch([isValid, errorMessages], () => {
    form?.update?.(id.value, isValid.value, errorMessages.value);
  });

  return {
    id,
    errorMessages,
    visibleError,
    isValid,
    isPristine,
    isDisabled,
    isReadonly,
    validate,
    reset,
    resetValidation,
    onBlur,
  };
}

interface RegisteredField {
  id: string;
  validate: () => Promise<string[]>;
  reset: () => Promise<void>;
  resetValidation: () => Promise<void>;
  isValid: boolean | null;
  errorMessages: string[];
}

/**
 * Provides a form context for the fields below it (the role `<v-form>` played) and reports
 * validity the same way: false if any field is invalid, true if all are valid, else null.
 * If there is an outer form (a legacy `<v-form>`), this group registers with it as one item,
 * so the outer form's validate() and validity include these fields too.
 */
export function provideFieldGroup(options: { disabled?: MaybeRefOrGetter<boolean | undefined>; readonly?: MaybeRefOrGetter<boolean | undefined> } = {}) {
  const parent = inject<FormContext | null>(FORM_CONTEXT_KEY, null);
  const items = ref<RegisteredField[]>([]);
  const isValid = ref<boolean | null>(null);

  async function validate() {
    const errors: string[] = [];
    for (const item of items.value) {
      errors.push(...await item.validate());
    }
    return { valid: errors.length === 0, errors };
  }
  async function reset() {
    await Promise.all(items.value.map(item => item.reset()));
  }
  async function resetValidation() {
    await Promise.all(items.value.map(item => item.resetValidation()));
  }

  watch(items, () => {
    let valid = 0;
    let invalid = 0;
    for (const item of items.value) {
      if (item.isValid === false) {
        invalid++;
      }
      else if (item.isValid === true) {
        valid++;
      }
    }
    isValid.value = invalid > 0 ? false : valid === items.value.length ? true : null;
  }, { deep: true, flush: "post" });

  provide<FormContext>(FORM_CONTEXT_KEY, {
    register: ({ id, validate: validateItem, reset: resetItem, resetValidation: resetItemValidation }) => {
      items.value.push({ id, validate: validateItem, reset: resetItem, resetValidation: resetItemValidation, isValid: null, errorMessages: [] });
    },
    unregister: (id) => {
      items.value = items.value.filter(item => item.id !== id);
    },
    update: (id, valid, errorMessages) => {
      const found = items.value.find(item => item.id === id);
      if (found) {
        found.isValid = valid;
        found.errorMessages = errorMessages;
      }
    },
    isDisabled: computed(() => !!(toValue(options.disabled) || parent?.isDisabled?.value)),
    isReadonly: computed(() => !!(toValue(options.readonly) || parent?.isReadonly?.value)),
  });

  if (parent?.register) {
    const groupId = `field-group-${useId()}`;
    const instance = getCurrentInstance();
    onBeforeMount(() => parent.register?.({
      id: groupId,
      vm: instance,
      validate: async () => (await validate()).errors,
      reset,
      resetValidation,
    }));
    onBeforeUnmount(() => parent.unregister?.(groupId));
    watch(isValid, value => parent.update?.(groupId, value, []), { immediate: true, flush: "post" });
  }

  return { isValid, validate, reset, resetValidation };
}
