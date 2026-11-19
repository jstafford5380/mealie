import { existsSync, readFileSync, readdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const planning = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const root = resolve(planning, "..");
const manifest = JSON.parse(readFileSync(join(planning, "route-manifest.json"), "utf8"));
const failures = [];
const pending = [];

function walk(directory) {
  return readdirSync(directory, { withFileTypes: true }).flatMap(entry => {
    const path = join(directory, entry.name);
    return entry.isDirectory() ? walk(path) : [path];
  });
}

const sources = walk(join(root, "frontend/app/pages")).filter(path => path.endsWith(".vue"));
for (const source of sources) {
  if (!manifest.pages.some(page => join(root, page.source) === source)) failures.push(`Unlisted page source: ${source}`);
}
for (const page of manifest.pages) {
  if (!existsSync(join(root, page.source))) failures.push(`Missing source: ${page.source}`);
  const path = join(planning, page.document);
  if (!existsSync(path)) {
    pending.push(page.document);
    continue;
  }
  const text = readFileSync(path, "utf8");
  if (!text.includes("## Functions") && !text.includes("## Flow") && !text.includes("## Wizard") && !text.includes("## Avatar") && !text.includes("## Input")) {
    failures.push(`No function section: ${page.document}`);
  }
  if (!/!\[[^\]]*\]\([^)]*\.jpg\)/.test(text)) failures.push(`No screenshot: ${page.document}`);
  if (!text.includes("## Shadcn Vue replacement checklist")) failures.push(`No replacement checklist: ${page.document}`);
}

for (const file of walk(planning).filter(path => path.endsWith(".md"))) {
  const text = readFileSync(file, "utf8");
  for (const match of text.matchAll(/\[[^\]]*\]\(([^)]+)\)/g)) {
    if (/^(https?:|#)/.test(match[1])) continue;
    const target = decodeURIComponent(match[1].split("#")[0]);
    if (!existsSync(resolve(dirname(file), target))) failures.push(`Broken link in ${file}: ${target}`);
  }
}
const screenshots = walk(join(planning, "screenshots")).filter(path => path.endsWith(".jpg"));
for (const file of screenshots) {
  const bytes = readFileSync(file);
  if (bytes[0] !== 0xff || bytes[1] !== 0xd8) failures.push(`Invalid JPEG: ${file}`);
}

console.log(`${sources.length} page sources; ${manifest.pages.length - pending.length} page documents; ${screenshots.length} screenshots.`);
console.log(`${pending.length} page documents pending.`);
for (const failure of failures) console.error(failure);
if (failures.length) process.exitCode = 1;
if (process.argv.includes("--complete") && (pending.length || manifest.pages.some(page => page.status !== "reviewed"))) {
  console.error("Catalog completion remains unproven. Review every page, state capture, and function checklist.");
  process.exitCode = 1;
}
console.log("This structural check does not prove function coverage or screenshot quality.");
