import { createHash } from "node:crypto";
import { realpathSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { join } from "node:path";
import { createBuilder, EndpointProperty } from "./.aspire/modules/aspire.mjs";

const root = realpathSync(fileURLToPath(new URL("../../", import.meta.url)));
const checkout = createHash("sha256").update(root).digest("hex").slice(0, 12);
const volumePrefix = "mealie-aspire-" + checkout;
const builder = await createBuilder();

const password = await builder.addParameter("postgres-password", { value: "mealie-local-dev", secret: true });
const postgres = await builder.addPostgres("postgres", { password })
  .withImageTag("15")
  .withDataVolume({ name: volumePrefix + "-postgres" });
const database = await postgres.addDatabase("database", { databaseName: "mealie" });

const mailpit = await builder.addContainer("mailpit", "axllent/mailpit:v1.27.8")
  .withHttpEndpoint({ targetPort: 8025 })
  .withEndpoint({ name: "smtp", targetPort: 1025 })
  .withHttpHealthCheck({ path: "/readyz" });

const frontend = await builder.addDockerfile("frontend", root, { dockerfilePath: "dev/aspire/frontend.Dockerfile" })
  .withBindMount(join(root, "mealie/repos/seed/resources/units/locales"), "/workspace/mealie/repos/seed/resources/units/locales", { isReadOnly: true })
  .withEnvironment("NODE_ENV", "development")
  .withEnvironment("NUXT_TELEMETRY_DISABLED", "1")
  .withHttpEndpoint({ targetPort: 3000 });

for (const source of ["app", "public", "server", "eslint-rules", "nuxt.config.ts", "tsconfig.json", "eslint.config.mjs", "vuetify.options.js"]) {
  await frontend.withBindMount(join(root, "frontend", source), "/workspace/frontend/" + source, { isReadOnly: true });
}

const backend = await builder.addDockerfile("backend", root, { dockerfilePath: "dev/aspire/backend.Dockerfile" })
  .withBindMount(join(root, "mealie"), "/workspace/mealie", { isReadOnly: true })
  .withVolume("/workspace/dev/data", { name: volumePrefix + "-data" })
  .withEnvironment("PRODUCTION", "false")
  .withEnvironment("TESTING", "false")
  .withEnvironment("API_DOCS", "true")
  .withEnvironment("API_PORT", "9000")
  .withEnvironment("DEFAULT_GROUP", "Home")
  .withEnvironment("DEFAULT_HOUSEHOLD", "Family")
  .withEnvironment("DB_ENGINE", "postgres")
  .withEnvironment("POSTGRES_SERVER", postgres.getEndpoint("tcp").property(EndpointProperty.Host))
  .withEnvironment("POSTGRES_PORT", postgres.getEndpoint("tcp").property(EndpointProperty.Port))
  .withEnvironment("POSTGRES_USER", "postgres")
  .withEnvironment("POSTGRES_PASSWORD", password)
  .withEnvironment("POSTGRES_DB", "mealie")
  .withEnvironment("SMTP_HOST", mailpit.getEndpoint("smtp").property(EndpointProperty.Host))
  .withEnvironment("SMTP_PORT", mailpit.getEndpoint("smtp").property(EndpointProperty.Port))
  .withEnvironment("SMTP_FROM_NAME", "MealieDev")
  .withEnvironment("SMTP_FROM_EMAIL", "mealie@example.com")
  .withEnvironment("SMTP_AUTH_STRATEGY", "NONE")
  .withEnvironmentCallback(async context => {
    await context.environment().set("BASE_URL", await frontend.getEndpoint("http").url());
  })
  .withHttpEndpoint({ targetPort: 9000 })
  .withHttpHealthCheck({ path: "/api/app/about" })
  .waitFor(database)
  .waitFor(mailpit);

await frontend
  .withEnvironment("API_URL", backend.getEndpoint("http"))
  .withEnvironment("NUXT_API_URL", backend.getEndpoint("http"))
  .withHttpHealthCheck({ path: "/api/app/about" })
  .waitFor(backend);

await builder.build().run();
