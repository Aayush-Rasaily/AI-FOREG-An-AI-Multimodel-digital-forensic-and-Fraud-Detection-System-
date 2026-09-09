/**
 * One-shot codemod: map remaining Tailwind palette classes to semantic tokens.
 * Run: node frontend/scripts/migrate-palette.mjs
 * Reports any palette class it could not map instead of guessing.
 */

import { readdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const SRC = fileURLToPath(new URL("../src", import.meta.url));

const MAPPING = {
  // danger
  "text-red-300": "text-danger",
  "text-red-200": "text-danger",
  "text-rose-300": "text-danger",
  "text-rose-400/80": "text-danger/80",
  "border-red-400/20": "border-danger/20",
  "bg-red-400/10": "bg-danger-soft",
  // success
  "text-emerald-300": "text-success",
  "text-green-300": "text-success",
  // primary
  "text-cyan-300": "text-primary",
  "text-cyan-400/80": "text-primary/80",
  "text-cyan-400": "text-primary",
  "text-cyan-200": "text-primary/85",
  "text-cyan-100": "text-primary/90",
  "hover:text-cyan-300": "hover:text-primary",
  "border-cyan-400/60": "border-primary/60",
  "border-cyan-400/40": "border-primary/40",
  "border-cyan-300/80": "border-primary/80",
  "border-cyan-700": "border-primary-strong",
  "hover:border-cyan-700": "hover:border-primary-strong",
  "hover:border-cyan-400/60": "hover:border-primary/60",
  "focus:border-cyan-700": "focus:border-primary-strong",
  "focus:border-cyan-400": "focus:border-primary",
  "bg-cyan-400/10": "bg-primary-soft",
  "bg-cyan-300/10": "bg-primary-soft",
  "bg-cyan-400/40": "bg-primary/40",
  "bg-cyan-400": "bg-primary",
  "bg-cyan-900": "bg-primary/20",
  "bg-cyan-950/30": "bg-primary-soft",
  // warning
  "text-amber-300": "text-warning",
  "text-amber-500": "text-warning",
  "text-amber-400": "text-warning",
  "text-amber-200/80": "text-warning/80",
  "text-amber-200": "text-warning",
  "text-amber-100/80": "text-warning/85",
  "text-amber-100/90": "text-warning/90",
  "border-amber-900/40": "border-warning/40",
  "border-amber-900/50": "border-warning/50",
  "bg-amber-950/20": "bg-warning-soft",
  // info
  "text-purple-300": "text-info",
  "text-violet-300": "text-info",
};

const CLASS_RE =
  /(?<![\w-])(([a-z-]+:)?)([a-z]+)-(slate|cyan|emerald|amber|red|rose|purple|violet|green|blue|gray|zinc|sky|teal|orange|yellow|lime|indigo|fuchsia|pink|stone|neutral)-(\d{2,3})(\/\d{1,3})?(?![\w-])/g;

const unmapped = new Map();
let changedFiles = 0;
let changedClasses = 0;

function* walk(dir) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) yield* walk(full);
    else if (entry.name.endsWith(".tsx")) yield full;
  }
}

for (const path of walk(SRC)) {
  const text = readFileSync(path, "utf8");
  let count = 0;
  const next = text.replace(CLASS_RE, (full, _p, prefix, base, palette, shade, alpha) => {
    const tail = alpha ?? "";
    const keyed = `${prefix}${base}-${palette}-${shade}${tail}`;
    if (MAPPING[keyed]) {
      count += 1;
      return `${prefix}${MAPPING[keyed]}`;
    }
    const bare = `${base}-${palette}-${shade}${tail}`;
    if (MAPPING[bare]) {
      count += 1;
      return MAPPING[bare];
    }
    unmapped.set(full, (unmapped.get(full) ?? 0) + 1);
    return full;
  });
  if (next !== text) {
    writeFileSync(path, next, "utf8");
    changedFiles += 1;
    changedClasses += count;
  }
}

console.log(`files changed: ${changedFiles}, classes remapped: ${changedClasses}`);
if (unmapped.size > 0) {
  console.log("UNMAPPED (left as-is):");
  for (const [cls, n] of [...unmapped.entries()].sort((a, b) => b[1] - a[1])) {
    console.log(`  ${String(n).padStart(4)}  ${cls}`);
  }
}
