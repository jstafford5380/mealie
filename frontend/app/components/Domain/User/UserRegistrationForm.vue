<template>
  <div class="flex flex-col gap-1 font-sans">
    <TextField
      v-model="accountDetails.username.value"
      autofocus
      autocomplete="username"
      validate-on="blur"
      :label="$t('user.username')"
      :rules="[validators.required]"
      :error-messages="usernameErrorMessages"
      @blur="validateUsername"
    />
    <TextField
      v-model="accountDetails.fullName.value"
      autocomplete="name"
      validate-on="blur"
      :label="$t('user.full-name')"
      :rules="[validators.required]"
    />
    <TextField
      v-model="accountDetails.email.value"
      type="email"
      autocomplete="email"
      validate-on="blur"
      :label="$t('user.email')"
      :rules="[validators.required, validators.email]"
      :error-messages="emailErrorMessages"
      @blur="validateEmail"
    />
    <TextField
      v-model="credentials.password1.value"
      type="password"
      autocomplete="new-password"
      validate-on="blur"
      :label="$t('user.password')"
      :rules="[validators.required, validators.minLength(8), validators.maxLength(258)]"
    />
    <UserPasswordStrength v-model="credentials.password1.value" />
    <TextField
      v-model="credentials.password2.value"
      type="password"
      autocomplete="new-password"
      validate-on="blur"
      :label="$t('user.confirm-password')"
      :rules="[validators.required, credentials.passwordMatch]"
    />
    <CheckboxField
      v-model="accountDetails.advancedOptions.value"
      class="mt-2"
      :label="$t('user.enable-advanced-content')"
      :hint="$t('user.enable-advanced-content-description')"
    />
  </div>
</template>

<script setup lang="ts">
import { validators } from "~/composables/use-validators";
import { useUserRegistrationForm } from "~/composables/use-users/user-registration-form";
import UserPasswordStrength from "~/components/Domain/User/UserPasswordStrength.vue";
import CheckboxField from "~/components/ui/field/CheckboxField.vue";
import TextField from "~/components/ui/field/TextField.vue";
import { provideFieldGroup } from "~/composables/forms/use-field-validation";

const emit = defineEmits(["update:modelValue"]);
const {
  accountDetails,
  credentials,
  emailErrorMessages,
  usernameErrorMessages,
  validateUsername,
  validateEmail,
  domAccountForm,
} = useUserRegistrationForm();

// The registration composable validates through this ref, as it did with the old v-form
const group = provideFieldGroup();
domAccountForm.value = group as any;
watch(
  group.isValid,
  (val) => {
    emit("update:modelValue", val === true);
  },
  { immediate: true },
);
</script>
