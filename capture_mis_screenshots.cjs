const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const outDir = path.resolve('doc_assets', 'screenshots');
fs.mkdirSync(outDir, { recursive: true });

async function shot(page, url, name) {
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.screenshot({ path: path.join(outDir, name), fullPage: true });
  console.log(path.join(outDir, name));
}

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  });
  const page = await browser.newPage({ viewport: { width: 1366, height: 900 }, deviceScaleFactor: 1 });
  const base = 'http://127.0.0.1:8001';

  await page.goto(`${base}/users/login/`, { waitUntil: 'networkidle' });
  await page.fill('input[name="username"]', 'admin');
  await page.fill('input[name="password"]', 'admin123');
  await Promise.all([
    page.waitForNavigation({ waitUntil: 'networkidle' }),
    page.click('button[type="submit"]'),
  ]);

  await shot(page, `${base}/dashboard/dashboard/`, '01-admin-dashboard.png');
  await shot(page, `${base}/proposals/`, '02-proposals-list.png');
  await shot(page, `${base}/research/`, '03-research-records.png');
  await shot(page, `${base}/extension/`, '04-extension-records.png');
  await shot(page, `${base}/extension/reports/quarterly/`, '05-quarterly-reports.png');
  await shot(page, `${base}/users/users/`, '06-user-management.png');

  await browser.close();
})();
