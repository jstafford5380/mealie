import type { LocaleObject } from "@nuxtjs/i18n";
import { LOCALES } from "./available-locales";
import { useGlobalI18n } from "../use-global-i18n";

export const useLocales = () => {
  const i18n = useGlobalI18n();

  const locale = computed<LocaleObject["code"]>({
    get: () => i18n.locale.value,
    set(value) {
      i18n.setLocale(value);
    },
  });

  // the page's language and reading direction follow the chosen locale (RTL for Arabic, Hebrew)
  function updateLocale(lc: LocaleObject["code"]) {
    if (typeof document === "undefined") {
      return;
    }
    const entry = LOCALES.find(l => l.value === lc);
    document.documentElement.lang = lc;
    document.documentElement.dir = entry?.dir === "rtl" ? "rtl" : "ltr";
  }

  // keep <html lang/dir> in step with the locale
  watch(locale, (lc) => {
    updateLocale(lc);
  });

  // set initial locale
  if (i18n.locale.value) {
    updateLocale(i18n.locale.value);
  };

  return {
    locale,
    locales: LOCALES,
    i18n,
  };
};
