import { spawnSync } from "node:child_process";

const result = spawnSync(
  "vue-tsc",
  ["--noEmit", "--pretty", "false"],
  { encoding: "utf8", shell: process.platform === "win32" },
);

if (result.error) throw result.error;
if (result.status === 0) process.exit(0);

// Add other areas as their existing diagnostics are resolved.
const checkedFiles = [
  /^app\/composables\/partials\/(?:__tests__\/)?use-(?:actions|store)-factory\./,
  /^app\/composables\/store\/use-(?:category|cookbook|food|label|tag|tool|unit)-store\.ts$/,
  /^app\/composables\/use-group-recipe-actions\.ts$/,
  /^app\/pages\/group\/data\/(?:categories|foods|labels|recipe-actions|tags|tools|units)\.vue$/,
  /^app\/pages\/group\/data\/foods\.test\.ts$/,
  /^app\/components\/Domain\/(?:Group\/GroupDataPage|Recipe\/RecipeDataSubstitutionManagerDialog)\.vue$/,
];
const diagnostics = result.stdout.trim().split(/\n(?=\S)/);
const errors = diagnostics.filter((diagnostic) => {
  const location = diagnostic.match(/^(.+)\(\d+,\d+\): error TS\d+:/);
  return !location || checkedFiles.some(pattern => pattern.test(location[1]));
});

if (result.stderr || errors.length || result.status === null) {
  if (result.stderr) console.error(result.stderr.trim());
  if (errors.length) console.error(errors.join("\n"));
  process.exit(1);
}

console.log(`Stores and organizer pages passed type-checking. ${diagnostics.length} diagnostics are outside this check's scope.`);
