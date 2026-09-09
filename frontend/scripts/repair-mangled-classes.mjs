/**
 * One-shot repair: fix className strings mangled by a faulty sed pass.
 * Each junk core maps back to the modifier prefix it replaced.
 * Run: node frontend/scripts/repair-mangled-classes.mjs
 */

import { readdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const SRC = fileURLToPath(new URL("../src", import.meta.url));

// Order matters: longer/more-specific cores first.
const REPAIRS = [
  // Interrupted Phase 11A pass: hover: → group-hover:text-primary:
  ["group-hover:text-primary:", "hover:"],
  // Interrupted pass: hover:border-primary/60 mangled on upload dropzone
  [
    "text-primary:border-primary-strong:hover:border-primary-strong:border-primary/60",
    "hover:border-primary/60",
  ],
  // "group-hover:" prefix (bash sed turned "+" into ":")
  [
    "text-primary:border-primary-strong:hover:border-primary-strong:bg-surface-muted",
    "group-hover:bg-surface-muted",
  ],
  [
    "text-primary:border-primary-strong:hover:border-primary-strong:text-foreground",
    "group-hover:text-foreground",
  ],
  [
    "text-primary:border-primary-strong:hover:border-primary-strong:text-primary",
    "group-hover:text-primary",
  ],
  // "focus-visible:" prefix (bash sed turned "-" into ":")
  [
    "text-primary:border-primary-strong:hover:border-primary-strong-visible:outline-none",
    "focus-visible:outline-none",
  ],
  [
    "text-primary:border-primary-strong:hover:border-primary-strong-visible:ring-2",
    "focus-visible:ring-2",
  ],
  [
    "text-primary:border-primary-strong:hover:border-primary-strong-visible:ring-ring",
    "focus-visible:ring-ring",
  ],
  // "focus:" prefix (bash sed turned "+" into ":")
  [
    "border-primary-strong:border-cyan-400:focus:border-primary:border-primary-strong:border-primary",
    "focus:border-primary",
  ],
  [
    "border-primary-strong:border-cyan-400:focus:border-primary:border-primary-strong:border-primary-strong",
    "focus:border-primary-strong",
  ],
  [
    "border-primary-strong:border-cyan-400:focus:border-primary:border-primary-strong:border-cyan-400",
    "focus:border-primary",
  ],
  [
    "border-primary-strong:border-cyan-400:focus:border-primary:border-primary-strong:outline-none",
    "focus:outline-none",
  ],
  [
    "border-primary-strong:border-cyan-400:focus:border-primary:border-primary-strong:ring-2",
    "focus:ring-2",
  ],
  [
    "border-primary-strong:border-cyan-400:focus:border-primary:border-primary-strong:ring-ring",
    "focus:ring-ring",
  ],
  // "focus-visible:" prefix inside the border-cyan-400 junk
  [
    "border-primary-strong:border-cyan-400:focus:border-primary:border-primary-strong-visible:outline-none",
    "focus-visible:outline-none",
  ],
  [
    "border-primary-strong:border-cyan-400:focus:border-primary:border-primary-strong-visible:ring-2",
    "focus-visible:ring-2",
  ],
  [
    "border-primary-strong:border-cyan-400:focus:border-primary:border-primary-strong-visible:ring-ring",
    "focus-visible:ring-ring",
  ],
  // "group-focus-within:" prefix (bash sed turned "-" into ":")
  [
    "group-border-cyan-700:border-cyan-400:focus:border-primary:border-primary-strong-within:opacity-100",
    "group-focus-within:opacity-100",
  ],
  [
    "group-border-cyan-400:focus:border-primary:border-primary-strong-within:opacity-100",
    "group-focus-within:opacity-100",
  ],
  // "group-hover:" prefix (variant B)
  [
    "group-text-cyan-300:border-primary-strong:hover:border-primary-strong:text-primary:opacity-100",
    "group-hover:opacity-100",
  ],
  // Unclassifiable: single occurrence in WorkflowTaskPanel (hover link underline)
  [
    "text-primary:border-primary-strong:hover:border-primary-strong:text-primary:underline",
    "focus-visible:underline",
  ],
];

let changedFiles = 0;
const leftovers = [];

function* walk(dir) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) yield* walk(full);
    else if (entry.name.endsWith(".tsx")) yield full;
  }
}

for (const path of walk(SRC)) {
  let text = readFileSync(path, "utf8");
  const original = text;
  for (const [junk, good] of REPAIRS) {
    text = text.split(junk).join(good);
  }
  if (text !== original) {
    writeFileSync(path, text, "utf8");
    changedFiles += 1;
  }
  // Leftover detection: any residual junk signature
  const lines = text.split("\n");
  lines.forEach((line, i) => {
    if (
      /border-primary-strong:|border-primary-visible|group-border-cyan|group-text-cyan|group-hover:text-primary:/.test(
        line,
      )
    ) {
      leftovers.push(`${path}:${i + 1}: ${line.trim().slice(0, 160)}`);
    }
  });
}

console.log(`files repaired: ${changedFiles}`);
if (leftovers.length > 0) {
  console.log("LEFTOVER JUNK:");
  for (const l of leftovers) console.log("  " + l);
} else {
  console.log("no leftover junk detected");
}
