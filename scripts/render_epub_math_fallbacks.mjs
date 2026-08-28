#!/usr/bin/env node

import crypto from "node:crypto";
import fs from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(scriptDir, "..");
const formulaDir = path.join(root, "build", "book", "math-fallbacks");
const inputPath = path.join(formulaDir, "formulas.json");
const renderPath = path.join(formulaDir, "render.html");
const receiptPath = path.join(root, "build", "EPUB_MATH_FALLBACK_RENDER_RECEIPT.json");
const expected = 17;
const browserCandidates = [
  process.env.BOOK_BROWSER_EXECUTABLE,
  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
].filter(Boolean);
const browserExecutable = browserCandidates.find((candidate) => fs.existsSync(candidate));
if (!browserExecutable) throw new Error("No bounded Chromium-family executable is available");

const payload = JSON.parse(fs.readFileSync(inputPath, "utf8"));
if (payload.formulas.length !== expected) {
  throw new Error(`Expected ${expected} fallback formulas, found ${payload.formulas.length}`);
}

const browser = await chromium.launch({ headless: true, executablePath: browserExecutable });
const page = await browser.newPage({ viewport: { width: 1600, height: 900 } });
const consoleMessages = [];
const pageErrors = [];
page.on("console", (message) => {
  if (["warning", "error"].includes(message.type())) {
    consoleMessages.push({ type: message.type(), text: message.text() });
  }
});
page.on("pageerror", (error) => pageErrors.push(String(error)));

try {
  await page.goto(pathToFileURL(renderPath).href, { waitUntil: "load", timeout: 120_000 });
  await page.evaluate(async () => {
    if (globalThis.MathJax?.startup?.promise) await globalThis.MathJax.startup.promise;
  });
  await page.waitForFunction(
    (count) => document.querySelectorAll("mjx-container").length === count,
    expected,
    { timeout: 120_000 },
  );
  const rendered = await page.evaluate(() => {
    const xml = new XMLSerializer();
    return [...document.querySelectorAll(".fallback-surface")].map((surface) => {
      const key = surface.getAttribute("data-key");
      const container = surface.querySelector("mjx-container");
      const svg = container?.querySelector("svg");
      if (!key || !svg) throw new Error("Missing fallback key or SVG");
      const clone = svg.cloneNode(true);
      clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
      clone.setAttribute("role", "img");
      clone.setAttribute("preserveAspectRatio", "xMidYMid meet");
      const idMap = new Map();
      for (const node of clone.querySelectorAll("[id]")) {
        const old = node.id;
        // Every standalone SVG ID must be an XML NCName.  The stable formula
        // key can begin with a digit, so always give generated IDs a letter
        // prefix instead of using the key itself as the first character.
        const replacement = `m-${key}-${old.replace(/[^A-Za-z0-9_.-]/g, "-")}`;
        idMap.set(old, replacement);
        node.id = replacement;
      }
      // Namespace-sensitive selectors do not consistently match MathJax's
      // xlink:href attributes across Chromium releases.  Inspect every
      // attribute by local name so each <use> reference follows its renamed
      // <path> target in the serialized standalone SVG.
      for (const node of clone.querySelectorAll("*")) {
        for (const attr of [...node.attributes]) {
          if (attr.localName === "href" && attr.value.startsWith("#")) {
            const replacement = idMap.get(attr.value.slice(1));
            if (replacement) node.setAttributeNS(attr.namespaceURI, attr.name, `#${replacement}`);
          }
        }
      }
      clone.removeAttribute("aria-hidden");
      return { key, svg: xml.serializeToString(clone) };
    });
  });

  if (pageErrors.length || consoleMessages.some((item) => item.type === "error")) {
    throw new Error(`Math fallback browser errors: ${JSON.stringify({ pageErrors, consoleMessages })}`);
  }
  const inventory = [];
  for (const item of rendered) {
    const record = payload.formulas.find((candidate) => candidate.key === item.key);
    if (!record) throw new Error(`Rendered unknown fallback ${item.key}`);
    const title = `<title id="title-${item.key}">${record.alt.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")}</title>`;
    const svg = item.svg
      .replace("<svg ", `<svg aria-labelledby="title-${item.key}" `)
      .replace(/(<svg[^>]*>)/, `$1${title}`)
      .replaceAll("currentColor", "#111820")
      .replaceAll("\r\n", "\n")
      .replaceAll("\r", "\n");
    const bytes = Buffer.from(`${svg.trim()}\n`, "utf8");
    const outputPath = path.join(formulaDir, `math-${item.key}.svg`);
    fs.writeFileSync(outputPath, bytes);
    inventory.push({
      bytes: bytes.length,
      key: item.key,
      path: path.relative(root, outputPath).replaceAll(path.sep, "/"),
      sha256: crypto.createHash("sha256").update(bytes).digest("hex"),
    });
  }
  inventory.sort((a, b) => a.key.localeCompare(b.key));
  const receipt = {
    browser: await browser.version(),
    consoleMessages,
    inventory,
    pageErrors,
    schema: "o006.stat415.epub-math-fallback-render.v1",
    status: "passed",
  };
  fs.writeFileSync(receiptPath, `${JSON.stringify(receipt, null, 2)}\n`, "utf8");
  process.stdout.write(`${JSON.stringify({ fallbacks: inventory.length, status: "passed" })}\n`);
} finally {
  await browser.close();
}
