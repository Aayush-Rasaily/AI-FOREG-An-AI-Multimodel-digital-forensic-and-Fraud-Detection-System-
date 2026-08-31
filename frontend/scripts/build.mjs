import { resolve } from "node:path";
import { spawnSync } from "node:child_process";

function run(script, args) {
  const result = spawnSync(
    process.execPath,
    [resolve("node_modules", script), ...args],
    { stdio: "inherit" },
  );
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}

run("typescript/bin/tsc", ["-b"]);
run("vite/bin/vite.js", ["build"]);
