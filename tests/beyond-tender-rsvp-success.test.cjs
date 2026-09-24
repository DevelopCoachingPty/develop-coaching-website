const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const page = fs.readFileSync(
  path.join(__dirname, '../www/beyond-the-tender/index.html'),
  'utf8'
);

test('RSVP submission accepts an opaque Apps Script response', () => {
  assert.match(page, /mode:\s*'no-cors'/);
  assert.match(page, /response\.type\s*!==\s*'opaque'\s*&&\s*!response\.ok/);
  assert.doesNotMatch(page, /await response\.json\(\)/);
});

test('RSVP submission still reports network failures and attending success', () => {
  assert.match(page, /catch \(error\)/);
  assert.match(page, /You're in\. Check your inbox for confirmation\./);
  assert.match(page, /We could not submit your RSVP\. Please try again\./);
});
