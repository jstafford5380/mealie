export default defineI18nLocale(async () => {
  const { default: slSI } = await import("../messages/sl-SI.json");
  const { default: unitNames } = await import(
    "../../../../mealie/repos/seed/resources/units/locales/sl-SI.json",
  );
  return {
    ...slSI,
    "unit-names": unitNames,
  };
});
