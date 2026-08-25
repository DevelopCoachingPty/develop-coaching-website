#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const hubPath = path.join(root, 'www/5-pillars-free-trainings/index.html');
const markupPath = path.join(root, 'content/five-pillars-hub.html');
const cssPath = path.join(root, 'content/_five-pillars-hub.css');
const styleId = 'five-pillars-hub-redesign';

function renderHub() {
  let html = fs.readFileSync(hubPath, 'utf8');
  const markup = fs.readFileSync(markupPath, 'utf8').trim();
  const css = fs.readFileSync(cssPath, 'utf8').trim();
  const style = `<style id="${styleId}">\n${css}\n</style>`;

  const mainPattern = /<main\b[\s\S]*?<\/main>/i;
  if (!mainPattern.test(html)) throw new Error('Five Pillars hub main element not found');
  html = html.replace(mainPattern, markup);

  const stylePattern = new RegExp(`<style id="${styleId}">[\\s\\S]*?<\\/style>`, 'i');
  if (stylePattern.test(html)) html = html.replace(stylePattern, style);
  else html = html.replace('</head>', `${style}\n</head>`);

  fs.writeFileSync(hubPath, html);
  return html;
}

if (require.main === module) {
  renderHub();
  console.log('Rendered redesigned Five Pillars hub.');
}

module.exports = {renderHub};
