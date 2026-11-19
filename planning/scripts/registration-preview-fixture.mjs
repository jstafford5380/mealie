import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const checkout = resolve(process.argv[3] || "/tmp/mealie-ui-catalog");
if (checkout !== "/tmp/mealie-ui-catalog") throw new Error("Use the isolated catalog checkout only.");
const file = resolve(checkout, "frontend/app/pages/register/index.vue");
const original = "</script>";
const preview = `// Catalog-only confirmation preview; never submit this incomplete draft.
onMounted(() => {
  if (!useRoute().query.catalogPreview) return;
  state.setType(useRoute().query.catalogPreview === "join" ? RegistrationType.JoinGroup : RegistrationType.CreateGroup);
  groupName.value = "Catalog preview group";
  groupSeed.value = true;
  groupPrivate.value = true;
  accountDetails.email.value = "catalog-preview@example.invalid";
  accountDetails.fullName.value = "Catalog Preview";
  accountDetails.username.value = "catalog-preview";
  accountDetails.advancedOptions.value = true;
  state.setState(States.Confirmation);
});
</script>`;
let text = readFileSync(file, "utf8");
if (process.argv[2] === "--apply") {
  if (text.includes("// Catalog-only confirmation preview")) throw new Error("Already applied.");
  text = text.replace(original, preview);
} else if (process.argv[2] === "--restore") {
  if (!text.includes(preview)) throw new Error("Expected preview not found.");
  text = text.replace(preview, original);
} else throw new Error("Use --apply or --restore.");
writeFileSync(file, text);
