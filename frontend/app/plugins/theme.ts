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

/** Dark or light text, whichever reads better on the given hex background. */
function readableForeground(hex: string): string {
  const value = hex.replace("#", "");
  const full = value.length === 3 ? value.split("").map(c => c + c).join("") : value;
  const [r, g, b] = [0, 2, 4].map((i) => {
    const c = Number.parseInt(full.slice(i, i + 2), 16) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  const luminance = 0.2126 * r! + 0.7152 * g! + 0.0722 * b!;
  return luminance > 0.36 ? "#0E1712" : "#FFFFFF";
}

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

export default defineNuxtPlugin(async (nuxtApp) => {
  nuxtApp.hook("vuetify:before-create", async ({ vuetifyOptions }) => {
    let theme = __cachedTheme;
    if (!theme) {
      theme = await fetchTheme();
      __cachedTheme = theme;
    }
    applyTokenOverrides(theme);
    // Coexistence with Reka UI dialogs (z-index 2050): Vuetify menus and tooltips opened inside
    // them must stack above. Remove with Vuetify.
    const defaults = (vuetifyOptions.defaults ?? {}) as Record<string, Record<string, unknown>>;
    vuetifyOptions.defaults = {
      ...defaults,
      VMenu: { ...defaults.VMenu, zIndex: 2400 },
      VTooltip: { ...defaults.VTooltip, zIndex: 2400 },
    };
    vuetifyOptions.theme = {
      defaultTheme: nuxtApp.$config.public.useDark ? "dark" : "light",
      variations: {
        colors: ["primary", "accent", "secondary", "success", "info", "warning", "error", "background"],
        lighten: 3,
        darken: 3,
      },
      themes: {
        light: {
          dark: false,
          colors: {
            primary: theme?.lightPrimary ?? DEFAULT_LIGHT_PRIMARY,
            accent: theme?.lightAccent ?? "#007A99",
            secondary: theme?.lightSecondary ?? "#973542",
            success: theme?.lightSuccess ?? "#43A047",
            info: theme?.lightInfo ?? "#1976d2",
            warning: theme?.lightWarning ?? "#FF6D00",
            error: theme?.lightError ?? "#EF5350",
            background: "#F5F7F3",
            surface: "#FFFFFF",
          },
        },
        dark: {
          dark: true,
          colors: {
            primary: theme?.darkPrimary ?? DEFAULT_DARK_PRIMARY,
            accent: theme?.darkAccent ?? "#007A99",
            secondary: theme?.darkSecondary ?? "#973542",
            success: theme?.darkSuccess ?? "#43A047",
            info: theme?.darkInfo ?? "#1976d2",
            warning: theme?.darkWarning ?? "#FF6D00",
            error: theme?.darkError ?? "#EF5350",
            background: "#141816",
            surface: "#1C211E",
          },
        },
      },
    };
  });
});
