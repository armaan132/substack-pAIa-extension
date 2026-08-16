#!/usr/bin/env node
"use strict";
/* Hardening check: the Chrome Web Store forbids remote code and MV3's CSP blocks
 * it. This fails if any shipped file evals, builds functions from strings, or
 * loads scripts/modules from a remote URL. Test fixtures and node_modules are
 * excluded (they don't ship). */
const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..");
const SKIP_DIRS = new Set(["node_modules", "tests", "scripts", ".git", "icons"]);
const SHIP_EXT = new Set([".js", ".html", ".css", ".json"]);

const RULES = [
  { re: /\beval\s*\(/g, msg: "eval()" },
  { re: /new\s+Function\s*\(/g, msg: "new Function()" },
  { re: /<script\b[^>]*\bsrc\s*=\s*["']https?:\/\//gi, msg: "remote <script src>" },
  { re: /\bimport\s*\(\s*["']https?:\/\//gi, msg: "remote dynamic import()" },
  { re: /\bimportScripts\s*\(\s*["']https?:\/\//gi, msg: "remote importScripts()" },
];

function walk(dir, out = []) {
  for (const name of fs.readdirSync(dir)) {
    if (SKIP_DIRS.has(name)) continue;
    const p = path.join(dir, name);
    const st = fs.statSync(p);
    if (st.isDirectory()) walk(p, out);
    else if (SHIP_EXT.has(path.extname(name))) out.push(p);
  }
  return out;
}

const violations = [];
for (const file of walk(ROOT)) {
  const text = fs.readFileSync(file, "utf8");
  for (const { re, msg } of RULES) {
    re.lastIndex = 0;
    if (re.test(text)) violations.push(`${path.relative(ROOT, file)}: ${msg}`);
  }
}

if (violations.length) {
  console.error("✗ remote-code / unsafe patterns found:");
  violations.forEach((v) => console.error("  - " + v));
  process.exit(1);
}
console.log("✓ no remote code / eval in shipped files");
