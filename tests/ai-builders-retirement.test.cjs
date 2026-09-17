const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.join(__dirname, '..');
const workshopPath = '/ai-for-builders-september-2026/';

test('public workshop landing page is retired from the site and discovery files', () => {
  assert.equal(fs.existsSync(path.join(root, 'www/ai-for-builders-september-2026/index.html')), false);

  const sitemap = fs.readFileSync(path.join(root, 'www/page-sitemap.xml'), 'utf8');
  assert.equal(sitemap.includes(workshopPath), false);

  const searchIndex = JSON.parse(fs.readFileSync(path.join(root, 'www/search-index.json'), 'utf8'));
  assert.equal(searchIndex.some(entry => entry.u === workshopPath), false);
});

test('existing buyers retain the confirmation page and verification endpoint', () => {
  assert.equal(fs.existsSync(path.join(root, 'www/ai-for-builders-september-2026/thank-you/index.html')), true);
  assert.equal(fs.existsSync(path.join(root, 'www/api/ai-builders-checkout-status.js')), true);
});
