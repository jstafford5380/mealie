import { spawn, spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("../../", import.meta.url));
const apphost = fileURLToPath(new URL("./", import.meta.url));
const npmCli = process.env.npm_execpath;
if (!npmCli) throw new Error("Start this command with npm run dev:aspire.");

for (const [command, args, help] of [
  ["aspire", ["--version"], "Install Aspire CLI 13.6.5 or later: https://aspire.dev/get-started/install-cli/"],
  ["docker", ["info"], "Start Docker Desktop or a Docker-compatible container runtime."],
]) {
  const result = spawnSync(command, args, { stdio: "ignore" });
  if (result.error || result.status !== 0) {
    console.error(help);
    process.exit(1);
  }
}

async function run(command, args, cwd) {
  const child = spawn(command, args, { cwd, stdio: "inherit" });
  const forward = signal => child.kill(signal);
  const onInterrupt = () => forward("SIGINT");
  const onTerminate = () => forward("SIGTERM");
  process.on("SIGINT", onInterrupt);
  process.on("SIGTERM", onTerminate);
  try {
    await new Promise((resolve, reject) => {
      child.on("error", reject);
      child.on("exit", (code, signal) => {
        if (code === 0) resolve();
        else reject(new Error(`${command} exited with ${signal ?? code}`));
      });
    });
  } finally {
    process.off("SIGINT", onInterrupt);
    process.off("SIGTERM", onTerminate);
  }
}

try {
  await run(process.execPath, [npmCli, "ci", "--include=dev", "--no-audit", "--no-fund"], apphost);
  await run("aspire", ["run", "--isolated", "--apphost", "dev/aspire/apphost.mts", ...process.argv.slice(2)], root);
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
