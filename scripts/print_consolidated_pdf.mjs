#!/usr/bin/env node

import fs from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(scriptDir, "..");
const input = path.resolve(
  process.argv[2] || path.join(root, "build", "book", "stat415-id-book.html"),
);
const output = path.resolve(
  process.argv[3] || path.join(root, "tmp", "pdfs", "stat415-id-book.raw.pdf"),
);
const metricsPath = path.resolve(
  process.argv[4] || path.join(root, "build", "CONSOLIDATED_PDF_RENDER_METRICS.json"),
);
const printCss = path.join(root, "source", "book", "print.css");
const expectedMathContainers = 3176;

function repoRelative(value) {
  const relative = path.relative(root, value);
  if (!relative || relative.startsWith(`..${path.sep}`) || path.isAbsolute(relative)) {
    throw new Error(`Path is outside the repository boundary: ${value}`);
  }
  return relative.split(path.sep).join("/");
}
const browserCandidates = [
  process.env.BOOK_BROWSER_EXECUTABLE,
  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
].filter(Boolean);
const browserExecutable = browserCandidates.find((candidate) => fs.existsSync(candidate));
if (!browserExecutable) {
  throw new Error("No bounded Chromium-family executable is available");
}

fs.mkdirSync(path.dirname(output), { recursive: true });
fs.mkdirSync(path.dirname(metricsPath), { recursive: true });

const browser = await chromium.launch({ headless: true, executablePath: browserExecutable });
const page = await browser.newPage({ viewport: { width: 794, height: 1123 } });
const consoleMessages = [];
const pageErrors = [];
page.on("console", (message) => {
  if (["warning", "error"].includes(message.type())) {
    consoleMessages.push({ type: message.type(), text: message.text() });
  }
});
page.on("pageerror", (error) => pageErrors.push(String(error)));

try {
  await page.emulateMedia({ media: "print" });
  await page.goto(pathToFileURL(input).href, {
    waitUntil: "load",
    timeout: 120_000,
  });
  await page.addStyleTag({ path: printCss });
  await page.evaluate(async () => {
    if (document.fonts?.ready) await document.fonts.ready;
    if (globalThis.MathJax?.startup?.promise) await globalThis.MathJax.startup.promise;
  });
  await page.evaluate(() => {
    if (document.querySelector(".book-cover")) return;
    const cover = document.createElement("section");
    cover.className = "book-cover";
    cover.innerHTML = `
      <p class="book-cover-kicker">STAT 415</p>
      <h1>Pengantar Statistika Matematis</h1>
      <p class="book-cover-subtitle">Edisi Bahasa Indonesia</p>
      <p class="book-cover-scope">Laman utama dan Pelajaran 00-12</p>
      <div class="book-cover-credit">
        <p><strong>Sumber:</strong> Departemen Statistika, The Pennsylvania State University</p>
        <p><strong>Terjemahan dan rekonstruksi:</strong> OpenAI Codex gpt-5.6-sol, Ultra</p>
        <p><strong>Edisi:</strong> 26 Agustus 2026</p>
        <p><strong>Preservasi:</strong> 10.5281/zenodo.22077422</p>
      </div>`;

    const toc = document.createElement("nav");
    toc.className = "book-print-toc";
    toc.setAttribute("aria-label", "Daftar isi edisi cetak");
    const heading = document.createElement("h1");
    heading.textContent = "Daftar Isi";
    toc.append(heading);
    const list = document.createElement("ol");
    for (const chapter of document.querySelectorAll(".book-document")) {
      const chapterHeading = chapter.querySelector("h1");
      if (!chapterHeading || !chapter.id) continue;
      const item = document.createElement("li");
      const link = document.createElement("a");
      link.href = `#${chapter.id}`;
      link.textContent = chapterHeading.textContent.trim();
      item.append(link);
      list.append(item);
    }
    toc.append(list);
    document.body.prepend(toc);
    document.body.prepend(cover);
  });
  await page.waitForFunction(
    (expected) => document.querySelectorAll("mjx-container").length >= expected,
    expectedMathContainers,
    { timeout: 240_000 },
  );
  const pendingImages = await page.evaluate(async () => {
    const images = [...document.images];
    for (const image of images) {
      image.loading = "eager";
      image.decoding = "sync";
      const current = image.getAttribute("src");
      if (current) image.setAttribute("src", current);
    }
    await Promise.race([
      Promise.all(images.map((image) => image.decode().catch(() => undefined))),
      new Promise((resolve) => setTimeout(resolve, 60_000)),
    ]);
    return images
      .filter((image) => !image.complete)
      .map((image) => image.getAttribute("src"));
  });
  if (pendingImages.length) {
    throw new Error(`Images did not finish loading: ${JSON.stringify(pendingImages)}`);
  }

  const metrics = await page.evaluate(() => {
    const brokenImages = [...document.images]
      .filter((image) => image.naturalWidth === 0 || image.naturalHeight === 0)
      .map((image) => image.getAttribute("src"));

    const wideTables = [];
    for (const table of document.querySelectorAll("table")) {
      const parentWidth = table.parentElement?.getBoundingClientRect().width || 0;
      const width = table.getBoundingClientRect().width;
      if (parentWidth && width > parentWidth + 0.5) {
        table.classList.add("book-table-wide");
        wideTables.push({
          id: table.id || null,
          originalWidth: Math.round(width * 100) / 100,
          parentWidth: Math.round(parentWidth * 100) / 100,
        });
      }
    }

    const scaledMath = [];
    const displays = [...document.querySelectorAll('mjx-container[display="true"]')];
    for (const container of displays) {
      const parentWidth = container.parentElement?.getBoundingClientRect().width || 0;
      const svg = container.querySelector("svg");
      const width = svg?.getBoundingClientRect().width || 0;
      if (parentWidth && width > parentWidth - 1) {
        const percent = Math.max(54, Math.min(96, (parentWidth / width) * 94));
        container.style.fontSize = `${percent.toFixed(2)}%`;
        container.classList.add("book-math-scaled");
        scaledMath.push({
          sourceId:
            container.closest("[data-o006-math-id]")?.getAttribute("data-o006-math-id") ||
            null,
          originalWidth: Math.round(width * 100) / 100,
          parentWidth: Math.round(parentWidth * 100) / 100,
          percent: Math.round(percent * 100) / 100,
        });
      }
    }

    return {
      brokenImages,
      codeBlocks: document.querySelectorAll("pre").length,
      documents: document.querySelectorAll(".book-document").length,
      figures: document.querySelectorAll("figure").length,
      imageOccurrences: document.images.length,
      mathContainers: document.querySelectorAll("mjx-container").length,
      mathErrors: document.querySelectorAll("mjx-merror, .MathJax_Error").length,
      scaledMath,
      tables: document.querySelectorAll("table").length,
      wideTables,
    };
  });

  if (metrics.brokenImages.length) {
    throw new Error(`Broken images: ${JSON.stringify(metrics.brokenImages)}`);
  }
  if (metrics.mathContainers !== expectedMathContainers || metrics.mathErrors !== 0) {
    throw new Error(
      `MathJax mismatch containers=${metrics.mathContainers} errors=${metrics.mathErrors}`,
    );
  }
  if (pageErrors.length || consoleMessages.some((item) => item.type === "error")) {
    throw new Error(
      `Browser errors: ${JSON.stringify({ pageErrors, consoleMessages }, null, 2)}`,
    );
  }

  await page.pdf({
    path: output,
    format: "A4",
    printBackground: true,
    displayHeaderFooter: true,
    headerTemplate: '<div style="font-size:1px"></div>',
    footerTemplate:
      '<div style="box-sizing:border-box;color:#5c6875;font-family:Arial,sans-serif;font-size:7.5px;padding:0 16mm;width:100%;display:flex;justify-content:space-between"><span>STAT 415 - Edisi Bahasa Indonesia</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>',
    margin: { top: "16mm", right: "16mm", bottom: "18mm", left: "16mm" },
    preferCSSPageSize: true,
    outline: true,
    tagged: true,
  });

  const receipt = {
    browser: await browser.version(),
    browserExecutable: path.basename(browserExecutable),
    consoleMessages,
    input: repoRelative(input),
    metrics,
    output: repoRelative(output),
    pageErrors,
    schema: "o006.stat415.consolidated-pdf-render.v1",
    status: "passed",
  };
  fs.writeFileSync(metricsPath, `${JSON.stringify(receipt, null, 2)}\n`, "utf8");
  process.stdout.write(`${JSON.stringify(receipt)}\n`);
} finally {
  await browser.close();
}
