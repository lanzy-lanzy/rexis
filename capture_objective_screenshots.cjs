const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const outDir = path.resolve('doc_assets', 'screenshots');
fs.mkdirSync(outDir, { recursive: true });

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  });
  const page = await browser.newPage({ viewport: { width: 1366, height: 900 }, deviceScaleFactor: 1 });
  const base = 'http://127.0.0.1:8001';

  await page.goto(`${base}/users/login/`, { waitUntil: 'networkidle' });
  await page.fill('input[name="username"]', 'faculty');
  await page.fill('input[name="password"]', 'faculty123');
  await Promise.all([
    page.waitForNavigation({ waitUntil: 'networkidle' }),
    page.click('button[type="submit"]'),
  ]);
  await page.goto(`${base}/proposals/create/`, { waitUntil: 'networkidle' });
  await page.fill('input[name="title"]', 'Sample Research and Extension Documentation Proposal');
  await page.locator('button:has-text("Next Step"):visible').click();
  await page.fill('textarea[name="abstract"]', 'This sample abstract is used only to display the proposal submission workflow and document upload stage of the Management Information System.');
  await page.fill('textarea[name="full_description"]', 'This sample description demonstrates how faculty users can encode proposal details before attaching supporting files in the system.');
  await page.locator('button:has-text("Next Step"):visible').click();
  await page.screenshot({ path: path.join(outDir, '07-proposal-upload-form.png'), fullPage: true });

  await browser.close();
})();
