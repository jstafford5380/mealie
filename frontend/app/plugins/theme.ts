import { readableForeground } from "~/lib/color";

export interface ThemeConfig {
  lightPrimary: string;
  lightAccent: string;
  lightSecondary: string;
  lightSuccess: string;
  lightInfo: string;
  lightWarning: string;
  lightError: string;
  darkPrimary: string;
  darkAccent: string;
  darkSecondary: string;
  darkSuccess: string;
  darkInfo: string;
  darkWarning: string;
  darkError: string;
}

let __cachedTheme: ThemeConfig | undefined;

const DEFAULT_LIGHT_PRIMARY = "#2E6A4F";
const DEFAULT_DARK_PRIMARY = "#5FAE87";

/** Exposes the configured primary colours to the Tailwind/Shadcn tokens in tailwind.css. */
function applyTokenOverrides(theme: ThemeConfig | undefined) {
  if (typeof document === "undefined") {
    return;
  }
  const light = theme?.lightPrimary || DEFAULT_LIGHT_PRIMARY;
  const dark = theme?.darkPrimary || DEFAULT_DARK_PRIMARY;
  const style = document.documentElement.style;
  style.setProperty("--theme-light-primary", light);
  style.setProperty("--theme-light-primary-foreground", readableForeground(light));
  style.setProperty("--theme-dark-primary", dark);
  style.setProperty("--theme-dark-primary-foreground", readableForeground(dark));
}

async function fetchTheme(): Promise<ThemeConfig | undefined> {
  const route = "/api/app/about/theme";

  try {
    const response = await fetch(route);
    const data = await response.json();
    return data as ThemeConfig;
  }
  catch {
    return undefined;
  }
}

export default defineNuxtPlugin(async () => {
  let theme = __cachedTheme;
  if (!theme) {
    theme = await fetchTheme();
    __cachedTheme = theme;
  }
  applyTokenOverrides(theme);
});
