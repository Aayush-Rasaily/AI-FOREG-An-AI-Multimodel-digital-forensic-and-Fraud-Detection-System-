import { resolve } from "node:path";
import { spawnSync } from "node:child_process";

function run(script, args) {
  const result = spawnSync(
    process.execPath,
    [resolve("node_modules", script), ...args],
    { encoding: "utf8" },
  );

  if (result.stdout) {
    process.stdout.write(result.stdout);
  }
  if (result.stderr) {
    process.stderr.write(result.stderr);
  }

  if (result.error) {
    console.error(result.error);
    process.exit(1);
  }

  const status = result.status ?? 1;
  if (status !== 0) {
    process.exit(status);
  }
}

run("typescript/bin/tsc", ["-b"]);
run("vite/bin/vite.js", ["build"]);
