import fs from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';

const { chromium } = createRequire(import.meta.url)(process.env.BASIN_PLAYWRIGHT_MODULE || 'playwright');
const out = path.resolve('output/browser-rehearsal');
await fs.rm(out, { recursive: true, force: true });
await fs.mkdir(out, { recursive: true });

const width = Number(process.env.BASIN_VIEWPORT_WIDTH || 1366);
const height = Number(process.env.BASIN_VIEWPORT_HEIGHT || 768);
const browser = await chromium.launch({
  headless: true,
  ...(process.env.BASIN_BROWSER_EXECUTABLE ? { executablePath: process.env.BASIN_BROWSER_EXECUTABLE } : {}),
});
const context = await browser.newContext({
  viewport: { width, height },
  recordVideo: { dir: out, size: { width, height } },
  acceptDownloads: true,
});

const external = [];
await context.route('**/*', async route => {
  const url = new URL(route.request().url());
  if (['127.0.0.1', 'localhost'].includes(url.hostname) || ['data:', 'blob:'].includes(url.protocol)) {
    return route.continue();
  }
  external.push(url.href);
  await route.abort();
});

const page = await context.newPage();
const errors = [];
const viewportChecks = [];
page.on('pageerror', error => errors.push(error.message));

async function recordViewport(stage, locator) {
  const box = await locator.boundingBox();
  viewportChecks.push({
    stage,
    viewport: { width, height },
    primary_action_visible: Boolean(box && box.y >= 0 && box.y + box.height <= height),
    primary_action_box: box,
    document_scroll_height: await page.evaluate(() => document.documentElement.scrollHeight),
  });
}

await page.goto(process.env.BASIN_URL || 'http://127.0.0.1:8521');
const exampleButton = page.getByRole('button', { name: 'Try an example', exact: true });
await exampleButton.waitFor({ timeout: 60000 });
await recordViewport('first use', exampleButton);
await page.screenshot({ path: path.join(out, '01-first-use.png') });

await page.getByText('Scenario settings · new run', { exact: true }).click();
const createButton = page.getByRole('button', { name: 'Create rainfall scenarios', exact: true });
await createButton.click();
await page.getByText('Decision summary', { exact: true }).waitFor({ timeout: 60000 });
await page.locator('.js-plotly-plot').first().waitFor({ timeout: 60000 });
const reviewButton = page.getByRole('button', { name: 'Review selected scenarios', exact: true });
await recordViewport('build scenarios', reviewButton);
await page.screenshot({ path: path.join(out, '02-workspace.png') });

await page.getByText('Settings', { exact: true }).click();
await page.getByRole('button', { name: 'Dark', exact: true }).click();
await page.getByText('Dark appearance selected.', { exact: true }).waitFor();
await page.screenshot({ path: path.join(out, '03-dark-workspace.png') });
await page.getByRole('button', { name: 'Light', exact: true }).click();
await page.getByText('Light appearance selected.', { exact: true }).waitFor();

await page.getByText('Compare scenarios and priorities', { exact: true }).click();
await page.getByText('Compare two or three candidates', { exact: true }).scrollIntoViewIfNeeded();
await page.screenshot({ path: path.join(out, '04-comparison.png') });

await page.getByText('3. Review choices', { exact: true }).first().click();
const acceptButton = page.getByRole('button', { name: 'Accept', exact: true });
await acceptButton.waitFor();
await recordViewport('review choices', acceptButton);
await page.getByRole('tab', { name: 'Reference & provenance' }).click();
await page.getByText('Evidence and assumptions', { exact: true }).scrollIntoViewIfNeeded();
await page.screenshot({ path: path.join(out, '05-evidence.png') });
await page.getByRole('textbox', { name: 'Public disagreement', exact: true }).fill(
  'Internal rehearsal: airport observations and catchment rainfall have different spatial meanings.',
);
await page.getByRole('textbox', { name: 'Public comparability limits (dates, definitions, units, geography)', exact: true }).fill(
  'Geographic applicability is unvalidated. Request practitioner review.',
);
await page.getByRole('button', { name: 'Record unresolved disagreement', exact: true }).click();
await page.getByText('Disagreement saved; both evidence records retained.', { exact: true }).waitFor();

await page.getByText('Cumulative rainfall', { exact: true }).first().click();
const scenarioBox = page.getByRole('combobox', { name: 'Scenario', exact: true });
await scenarioBox.waitFor();
await page.getByRole('textbox', { name: 'Review note', exact: true }).fill(
  'Automated browser rehearsal approval; not practitioner validation.',
);
await page.getByRole('button', { name: 'Accept', exact: true }).click();
await page.waitForTimeout(1500);

await page.getByText('4. Share results', { exact: true }).first().click();
const exportButton = page.getByRole('button', { name: 'Build verified export', exact: true });
await exportButton.waitFor();
await recordViewport('share results', exportButton);
if (await exportButton.isEnabled()) throw new Error('Export gate opened before every selected scenario was reviewed');
if (await page.getByText('Draft preview of currently accepted revisions.', { exact: false }).count() !== 1) {
  throw new Error('Accepted-scenario report preview was not rendered');
}
await page.screenshot({ path: path.join(out, '06-export.png') });

await page.getByText('1. Check data', { exact: true }).first().click();
await page.getByText('Snapshot metadata & quality policy', { exact: true }).waitFor();
await page.screenshot({ path: path.join(out, '07-data.png') });

if (errors.length) throw new Error(JSON.stringify(errors));
if (viewportChecks.some(check => !check.primary_action_visible)) {
  throw new Error(`Primary action was outside the viewport: ${JSON.stringify(viewportChecks)}`);
}

await fs.writeFile(path.join(out, 'report.json'), JSON.stringify({
  source_revision: process.env.BASIN_SOURCE_REVISION || null,
  external_requests_blocked: external,
  browser_errors: errors,
  viewport_checks: viewportChecks,
  scope: 'Browser requests to nonlocal hosts blocked; current four-stage source, generation, comparison, evidence conflict, one human-review action, report preview, locked export gate and data map were exercised. Full approved export/replay remains covered by application and integration tests. Actual presentation laptop remains untested.',
}, null, 2));

const video = page.video();
await context.close();
if (video) await video.saveAs(path.join(out, 'BASIN-internal-rehearsal.webm'));
await browser.close();
console.log(JSON.stringify({ external_requests_blocked: external, errors, viewportChecks, output: out }));
