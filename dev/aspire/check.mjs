import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { setTimeout } from "node:timers/promises";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("../../", import.meta.url));
const required = ["frontend", "backend", "postgres", "database", "mailpit"];
const deadline = Date.now() + 10 * 60 * 1000;
let resources;

while (true) {
  const output = execFileSync("aspire", [
    "describe", "--apphost", "dev/aspire/apphost.mts", "--format", "Json",
  ], { cwd: root, encoding: "utf8", timeout: 30000 });
  if (!output.trim()) throw new Error("Start the stack with npm run dev:aspire first.");
  ({ resources } = JSON.parse(output));
  const pending = required.filter(name => !resources.some(resource =>
    resource.displayName === name && resource.state === "Running" && resource.healthStatus === "Healthy"));
  if (pending.length === 0) break;
  if (Date.now() >= deadline) throw new Error(`Services did not become healthy: ${pending.join(", ")}`);
  console.log(`Waiting for ${pending.join(", ")}...`);
  await setTimeout(5000);
}

function url(name) {
  return resources.find(resource => resource.displayName === name).urls.find(endpoint => endpoint.name === "http").url;
}

async function get(address) {
  const response = await fetch(address, { signal: AbortSignal.timeout(30000) });
  assert.equal(response.status, 200, address);
  return response;
}

const backend = await (await get(`${url("backend")}/api/app/about`)).json();
const frontend = await (await get(`${url("frontend")}/api/app/about`)).json();
assert.equal(resources.find(resource => resource.displayName === "backend").environment.BASE_URL, url("frontend"));
assert.equal(frontend.version, backend.version);
assert.equal(frontend.production, false);
assert.match(await (await get(url("frontend"))).text(), /__nuxt/);
await get(`${url("mailpit")}/readyz`);

console.log(`Mealie ${frontend.version}: all services are healthy.`);
console.log(`Application: ${url("frontend")}`);
console.log(`API docs: ${url("backend")}/docs`);
console.log(`Mailpit: ${url("mailpit")}`);
