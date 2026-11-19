import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

// Render the existing result controls without generating a usable credential.
const checkout = resolve(process.argv[3] || "/tmp/mealie-ui-catalog");
if (checkout !== "/tmp/mealie-ui-catalog") throw new Error("Use the isolated catalog checkout only.");
const file = resolve(checkout, "frontend/app/pages/user/profile/api-tokens.vue");
const replacements = [
  ['return auth.user.value;', 'return { ...auth.user.value, tokens: [{ id: -1, name: "Catalog preview — invalid token", createdAt: "2026-11-18T12:00:00Z" }] };'],
  ['const createdToken = ref("");', 'const createdToken = ref("catalog-preview-not-a-valid-token");'],
  ['const name = ref("");', 'const name = ref("Catalog preview — invalid token");'],
];
let text = readFileSync(file, "utf8");
if (!["--apply", "--restore"].includes(process.argv[2])) throw new Error("Use --apply or --restore.");
for (const [original, preview] of replacements) {
  const [from, to] = process.argv[2] === "--apply" ? [original, preview] : [preview, original];
  if (!text.includes(from)) throw new Error("Expected fixture source not found.");
  text = text.replace(from, to);
}
writeFileSync(file, text);
