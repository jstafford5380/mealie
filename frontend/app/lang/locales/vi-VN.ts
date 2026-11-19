export default defineI18nLocale(async () => {
  const { default: viVN } = await import("../messages/vi-VN.json");
  const { default: unitNames } = await import(
    "../../../../mealie/repos/seed/resources/units/locales/vi-VN.json",
  );
  return {
    ...viVN,
    "unit-names": unitNames,
  };
});
