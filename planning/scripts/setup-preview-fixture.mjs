import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

// This helper changes only the initial setup step in the disposable capture checkout.
const checkout = resolve(process.argv[3] || "/tmp/mealie-ui-catalog");
if (checkout !== "/tmp/mealie-ui-catalog") throw new Error("Use the isolated catalog checkout only.");
const file = resolve(checkout, "frontend/app/pages/admin/setup.vue");
const original = "const currentPage = ref(Pages.LANDING);";
const preview = `const catalogPreviewStep = Number(useRoute().query.catalogPreviewStep);
const currentPage = ref<Pages>([3, 4, 5, 6].includes(catalogPreviewStep) ? catalogPreviewStep : Pages.LANDING);`;
const text = readFileSync(file, "utf8");
if (process.argv[2] === "--apply") {
  if (!text.includes(original)) throw new Error("Expected the unmodified setup initializer.");
  writeFileSync(file, text.replace(original, preview));
} else if (process.argv[2] === "--restore") {
  if (!text.includes(preview)) throw new Error("Expected the catalog preview initializer.");
  writeFileSync(file, text.replace(preview, original));
} else throw new Error("Use --apply or --restore.");
