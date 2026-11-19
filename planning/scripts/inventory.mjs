import { existsSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const planning = join(root, "planning");
const pageRoot = join(root, "frontend/app/pages");
const componentRoot = join(root, "frontend/app/components");
const normalize = value => value.replace(/[-_]/g, "").toLowerCase();
const unique = values => [...new Set(values)].sort();

function files(directory) {
  return readdirSync(directory, { withFileTypes: true }).flatMap(entry => {
    const path = join(directory, entry.name);
    return entry.isDirectory() ? files(path) : entry.name.endsWith(".vue") ? [path] : [];
  }).sort();
}

// New Shadcn Vue primitives (components/ui) are replacements, not legacy components to inventory.
const components = files(componentRoot).filter(file => !relative(componentRoot, file).startsWith("ui/")).map(file => ({
  source: relative(root, file),
  name: file.split("/").at(-1).replace(/\.vue$/, ""),
  text: readFileSync(file, "utf8"),
}));
const byName = new Map(components.map(component => [normalize(component.name), component.source]));

function evidence(text) {
  const imports = [...text.matchAll(/import\s+(\w+)\s+from\s+["']([^"']+\.vue)["']/g)];
  const names = new Map(imports.map(match => [match[1], match[2]]));
  const tags = unique([...text.matchAll(/<([A-Z][\w.-]*|[a-z][\w]*-[\w-]+)\b/g)].map(match => match[1]));
  const dependencies = unique(tags.flatMap(tag => {
    const imported = names.get(tag);
    if (imported?.startsWith("~/") || imported?.startsWith("@/")) return ["frontend/app/" + imported.slice(2)];
    const source = byName.get(normalize(tag));
    return source ? [source] : [];
  }));
  return {
    components: tags.filter(tag => !tag.startsWith("v-")),
    dependencies,
    vuetify: tags.filter(tag => tag.startsWith("v-")),
    events: unique([...text.matchAll(/@([\w:.-]+)="([^"]*)"/g)].map(match => match[1] + ": " + match[2])),
    models: unique([...text.matchAll(/v-model(?::[\w-]+)?(?:\.[\w-]+)*="([^"]*)"/g)].map(match => match[1])),
    conditions: unique([...text.matchAll(/v-(?:if|else-if)="([^"]*)"/g)].map(match => match[1])),
    dynamicComponents: unique([...text.matchAll(/:is="([^"]*)"/g)].map(match => match[1])),
    vuetifyAPIs: unique([...text.matchAll(/\$vuetify|\buseDisplay\b|\buseTheme\b|v-ripple|v-tooltip|v-intersect|v-resize/g)].map(match => match[0])),
  };
}

const previous = JSON.parse(readFileSync(join(planning, "route-manifest.json"), "utf8"));
const pages = files(pageRoot).map(file => {
  const source = relative(root, file);
  const stem = relative(pageRoot, file).replace(/\.vue$/, "");
  const id = stem.replaceAll("/", "--").replace(/[\[\]]/g, "");
  const old = previous.pages.find(page => page.source === source);
  return {
    id,
    route: "/" + stem.replace(/(^|\/)index$/, "").replace(/\[([^\]]+)\]/g, ":$1").replace(/\/$/, ""),
    source,
    document: `pages/${id}.md`,
    status: old?.status ?? "pending",
    ...evidence(readFileSync(file, "utf8")),
  };
});
const graph = components.map(({ text, ...component }) => ({ ...component, ...evidence(text) }));
const graphBySource = new Map(graph.map(component => [component.source, component]));

function closure(dependencies, seen = new Set()) {
  for (const dependency of dependencies) {
    if (seen.has(dependency)) continue;
    seen.add(dependency);
    closure(graphBySource.get(dependency)?.dependencies ?? [], seen);
  }
  return [...seen].sort();
}
for (const page of pages) page.componentClosure = closure(page.dependencies);

// Keep replacement statuses ([x]) from the existing inventory when regenerating it.
const inventoryPath = join(planning, "component-inventory.md");
const previousStatus = new Map(existsSync(inventoryPath)
  ? [...readFileSync(inventoryPath, "utf8").matchAll(/^\| \[(.)\] \| \[[^\]]+\]\(\.\.\/([^)]+)\)/gm)].map(match => [match[2], match[1]])
  : []);
const statusOf = source => previousStatus.get(source) ?? " ";

writeFileSync(join(planning, "route-manifest.json"), JSON.stringify({ ...previous, pages }, null, 2) + "\n");
writeFileSync(join(planning, "component-manifest.json"), JSON.stringify({ components: graph }, null, 2) + "\n");

const rows = graph.map(component => {
  const consumers = pages.filter(page => page.componentClosure.includes(component.source));
  return `| [${statusOf(component.source)}] | [${component.name}](../${component.source}) | ${component.vuetify.map(tag => "`" + tag + "`").join(", ") || "No direct Vuetify tags"} | ${consumers.map(page => "`" + page.id + "`").join(", ") || "Check layouts, dynamic use, and other consumers"} |`;
});
writeFileSync(join(planning, "component-inventory.md"), `# Component replacement inventory

This source inventory covers all ${graph.length} Vue files under frontend/app/components.
Every row needs a replacement or an explicit retention decision.
Page consumers include nested component references.
This static scan cannot prove runtime use or absence of use.
Check dynamic components, layouts, slots, directives, and programmatic UI separately.
The page documents define behavior; tag counts do not define behavior.

| Done | Component source | Direct Vuetify tags | Page consumers |
| --- | --- | --- | --- |
${rows.join("\n")}
`);
console.log(`${pages.length} page sources; ${graph.length} component sources.`);

const pageRows = pages.map(page => {
  const document = existsSync(join(planning, page.document))
    ? `[${page.id}](${page.document})`
    : `${page.id} — document pending`;
  return `| ${document} | ${page.route} | [Source](../${page.source}) | ${page.status} |`;
});
writeFileSync(join(planning, "PAGES.md"), `# Page catalog index

The inventory covers ${pages.length} page source files.
Parent routes and their index children have separate documents because they own different behavior.
Read [the shared shell](shared-shell.md) with every page.
Status describes catalog evidence, not UI migration completion.

| Page document | Route | Source | Catalog status |
| --- | --- | --- | --- |
${pageRows.join("\n")}

The [application error page](../frontend/app/error.vue) is an additional surface outside the page directory.
Its document and captures remain part of the catalog scope.
`);
