import { useDark } from "@vueuse/core";

export default defineNuxtPlugin((nuxtApp) => {
  const isDark = useDark({
    onChanged: (v, defaultHandler, mode) => {
      console.log(`changing theme to ${v ? "dark" : "light"} using @vueuse/useDark`);
      // Applies the `dark` class to <html> for the Tailwind/Shadcn tokens.
      defaultHandler(mode);
      const $vuetify = nuxtApp.vueApp.$nuxt.$vuetify;
      if ($vuetify)
        $vuetify.theme.toggle();
    },
  });

  nuxtApp.hook("vuetify:ready", (vuetify) => {
    vuetify.theme.change(isDark.value ? "dark" : "light");
  });

  return {
    provide: {},
  };
});
