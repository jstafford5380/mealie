import type { ClassValue } from "clsx";
import { clsx } from "clsx";
import { extendTailwindMerge } from "tailwind-merge";

// Teach tailwind-merge the project's radius names so `cn()` resolves conflicts between them.
const twMerge = extendTailwindMerge({
  extend: {
    theme: {
      radius: ["item", "control", "card", "panel"],
    },
  },
});

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
