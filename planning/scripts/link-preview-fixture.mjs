import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const checkout = resolve(process.argv[3] || "/tmp/mealie-ui-catalog");
if (checkout !== "/tmp/mealie-ui-catalog") throw new Error("Use the isolated catalog checkout only.");
const replacements = [
  ["frontend/app/components/Domain/User/UserInviteDialog.vue", 'const token = ref("");', 'const token = ref("catalog-preview-not-a-valid-invitation");'],
  ["frontend/app/pages/admin/manage/users/[id].vue", 'const resetUrl = ref<string | null>(null);', 'const resetUrl = ref<string | null>(`${window.location.origin}/reset-password/?token=catalog-preview-not-a-valid-reset`);'],
];
if (!["--apply", "--restore"].includes(process.argv[2])) throw new Error("Use --apply or --restore.");
const changes = replacements.map(([relative, original, preview]) => {
  const file = resolve(checkout, relative);
  const text = readFileSync(file, "utf8");
  const [from, to] = process.argv[2] === "--apply" ? [original, preview] : [preview, original];
  if (!text.includes(from)) throw new Error(`Expected initializer not found in ${relative}`);
  return [file, text.replace(from, to)];
});
for (const [file, text] of changes) writeFileSync(file, text);
