#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const hubPath = path.join(root, 'www/5-pillars-free-trainings/index.html');
const markupPath = path.join(root, 'content/five-pillars-hub.html');
const cssPath = path.join(root, 'content/_five-pillars-hub.css');
const styleId = 'five-pillars-hub-redesign';

function renderHub(options = {}) {
  const targetHubPath = options.hubPath || hubPath;
  const targetMarkupPath = options.markupPath || markupPath;
  const targetCssPath = options.cssPath || cssPath;
  let html = fs.readFileSync(targetHubPath, 'utf8');
  const markup = fs.readFileSync(targetMarkupPath, 'utf8').trim();
  const css = fs.readFileSync(targetCssPath, 'utf8').trim();
  const style = `<style id="${styleId}">\n${css}\n</style>`;

  const mainPattern = /<main\b[\s\S]*?<\/main>/i;
  if (!mainPattern.test(html)) throw new Error('Five Pillars hub main element not found');
  html = html.replace(mainPattern, markup);

  // build_site.py modernises the legacy footer before this renderer runs.
  // The hub template already contains its own book, award and footer, so remove
  // those shared replacements to prevent duplicate CTAs and duplicate footers.
  html = html
    .replace(/<section\b[^>]*class="[^"]*\bdc-book-award\b[^"]*"[^>]*>[\s\S]*?<\/section>\s*/i, '')
    .replace(/<footer\b[^>]*\bdata-dc-modern-footer\b[^>]*>[\s\S]*?<\/footer>\s*/i, '')
    .replace(/<style id="dc-modern-footer">[\s\S]*?<\/style>\s*/i, '');

  const stylePattern = new RegExp(`<style id="${styleId}">[\\s\\S]*?<\\/style>`, 'i');
  if (stylePattern.test(html)) html = html.replace(stylePattern, style);
  else html = html.replace(/<\/head>/i, `${style}\n</head>`);

  fs.writeFileSync(targetHubPath, html);
  return html;
}

if (require.main === module) {
  renderHub();
  console.log('Rendered redesigned Five Pillars hub.');
}

module.exports = {renderHub};
