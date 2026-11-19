<template>
  <BaseDialog
    v-model="modelValue"
    :icon="$globals.icons.translate"
    :title="$t('language-dialog.choose-language')"
  >
    <div class="flex flex-col gap-3 px-6 pb-2 text-[15px]">
      <p class="m-0 text-muted-foreground">
        {{ $t("language-dialog.select-description") }}
      </p>
      <FilterSelect
        v-model="selectedLocale"
        :items="locales"
        item-value="value"
        item-key="value"
        :clearable="false"
        :aria-label="$t('language-dialog.choose-language')"
      >
        <template #item="{ item }">
          <span class="flex items-baseline justify-between gap-3">
            <span class="truncate">{{ item.name }}</span>
            <span class="shrink-0 text-xs text-muted-foreground">{{ item.progress }}% {{ $t("language-dialog.translated") }}</span>
          </span>
        </template>
      </FilterSelect>
      <p class="m-0 text-sm text-muted-foreground">
        <i18n-t keypath="language-dialog.how-to-contribute-description">
          <template #read-the-docs-link>
            <a
              href="https://docs.mealie.io/contributors/translating/"
              target="_blank"
              class="font-semibold text-primary"
            >
              {{ $t("language-dialog.read-the-docs") }}
            </a>
          </template>
        </i18n-t>
      </p>
    </div>
  </BaseDialog>
</template>

<script setup lang="ts">
import { useLocales } from "~/composables/use-locales";
import FilterSelect from "~/components/ui/field/FilterSelect.vue";

const modelValue = defineModel<boolean>({ default: () => false });

const { locales: LOCALES, locale, i18n } = useLocales();

const selectedLocale = ref<string>(locale.value);
watch(selectedLocale, (value) => {
  if (value && value !== locale.value && locales.some(l => l.value === value)) {
    locale.value = value as any;
  }
});

watch(locale, () => {
  modelValue.value = false; // Close dialog when locale changes
});

const locales = LOCALES.filter(lc =>
  i18n.locales.value.map(i18nLocale => i18nLocale.code).includes(lc.value as any),
);
</script>
