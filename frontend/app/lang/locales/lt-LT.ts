export default defineI18nLocale(async () => {
  const { default: ltLT } = await import("../messages/lt-LT.json");
  const { default: unitNames } = await import(
    "../../../../mealie/repos/seed/resources/units/locales/lt-LT.json",
  );
  return {
    ...ltLT,
    "unit-names": unitNames,
  };
});
