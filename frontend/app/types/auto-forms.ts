type FormFieldType
  = | "text"
    | "textarea"
    | "number"
    | "list"
    | "select"
    | "object"
    | "boolean"
    | "color"
    | "password";

export type FormValidationRule = (value: any) => boolean | string;

export interface FormSelectOption {
  text: string;
  value?: string;
}

export interface FormFieldNumberInputConfig {
  min?: number;
  max?: number;
  precision?: number;
  controlVariant?: "split" | "default" | "hidden" | "stacked";
}

export interface FormField {
  section?: string;
  sectionDetails?: string;
  cols?: number | "auto";
  label?: string;
  hint?: string;
  tooltip?: string;
  varName: string;
  type: FormFieldType;
  rules?: FormValidationRule[];
  disableUpdate?: boolean;
  disableCreate?: boolean;
  numberInputConfig?: FormFieldNumberInputConfig;
  options?: FormSelectOption[];
  selectReturnValue?: "text" | "value";
}

export type AutoFormItems = FormField[];

/** What a validation scope exposes (FieldScope, provideFieldGroup), in place of Vuetify's form. */
export interface VForm {
  validate: () => Promise<{ valid: boolean; errors?: unknown[] }>;
  reset?: () => void | Promise<void>;
  resetValidation?: () => void | Promise<void>;
}
