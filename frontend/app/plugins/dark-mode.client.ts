import { useDark } from "@vueuse/core";

/** Keeps the `dark` class on <html> in step with the user's choice; the Tailwind tokens follow it. */
export default defineNuxtPlugin(() => {
  useDark();

  return {
    provide: {},
  };
});
