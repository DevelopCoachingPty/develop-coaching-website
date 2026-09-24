/**
 * Beyond the Tender 2026 — member RSVP endpoint.
 *
 * Script properties:
 *   SHEET_ID        Google Sheet ID that stores RSVPs.
 *   GHL_WEBHOOK_URL Flow Build / GoHighLevel inbound-webhook URL.
 *
 * The public page submits URL-encoded form data to doPost(). The script saves
 * the RSVP first, then forwards it to GHL. GHL owns the confirmation email so
 * members receive one confirmation, not one from each system.
 */

const PROPS = PropertiesService.getScriptProperties();
const EVENT_SLUG = 'beyond-the-tender-2026';
const EVENT_NAME = 'Beyond the Tender 2026';
const HEADERS = [
  'Submitted at',
  'Name',
  'Business',
  'Email',
  'Attendance',
  'Hotel preference',
  'Dietary / notes',
  'Event',
  'Source',
  'GHL status',
  'GHL response',
  'Submission ID'
];

function cfg_(key) {
  return PROPS.getProperty(key) || '';
}

function sheet_() {
  const sheetId = cfg_('SHEET_ID');
  if (!sheetId) throw new Error('SHEET_ID is not configured');
  return SpreadsheetApp.openById(sheetId).getSheets()[0];
}

function doGet() {
  return json_({ ok: true, service: EVENT_NAME + ' RSVP endpoint' });
}

function doPost(e) {
  try {
    const p = e && e.parameter ? e.parameter : {};

    // Honeypot: bots get a successful-looking response without creating data.
    if (clean_(p.website, 200)) return json_({ ok: true });

    const row = {
      timestamp: new Date(),
      name: clean_(p.name, 100),
      business: clean_(p.company, 120),
      email: clean_(p.email, 254).toLowerCase(),
      attendance: p.attending === 'yes' ? 'Attending' : p.attending === 'no' ? 'Not attending' : '',
      hotel: clean_(p.room, 120),
      notes: clean_(p.notes, 1000),
      event: EVENT_SLUG,
      source: 'members-page',
      submissionId: Utilities.getUuid()
    };

    if (!row.name || !isEmail_(row.email) || !row.attendance) {
      return json_({ ok: false, error: 'Please complete your name, email and attendance.' });
    }

    const saved = saveRsvp_(row);
    if (saved.duplicate) {
      return json_({ ok: true, duplicate: true, attending: row.attendance === 'Attending' });
    }

    const ghl = postGhlWebhook_(row);
    updateDelivery_(row.submissionId, ghl);

    if (!ghl.ok) {
      return json_({
        ok: false,
        saved: true,
        error: 'Your RSVP was saved, but the confirmation could not be sent. The team will follow up.'
      });
    }

    return json_({ ok: true, saved: true, attending: row.attendance === 'Attending' });
  } catch (err) {
    console.error(err);
    return json_({ ok: false, error: 'We could not submit your RSVP. Please try again.' });
  }
}

function saveRsvp_(row) {
  const lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    const sheet = sheet_();
    ensureHeaders_(sheet);

    if (isDuplicate_(sheet, row.email, row.event)) {
      return { duplicate: true };
    }

    sheet.appendRow([
      row.timestamp,
      sheetText_(row.name),
      sheetText_(row.business),
      sheetText_(row.email),
      row.attendance,
      sheetText_(row.hotel),
      sheetText_(row.notes),
      row.event,
      row.source,
      'Pending',
      '',
      row.submissionId
    ]);
    return { duplicate: false };
  } finally {
    lock.releaseLock();
  }
}

function postGhlWebhook_(row) {
  const url = cfg_('GHL_WEBHOOK_URL');
  if (!url) return { ok: false, status: 'Not configured', detail: 'GHL_WEBHOOK_URL is missing' };

  const nameParts = row.name.split(/\s+/);
  const firstName = nameParts.shift() || '';
  const lastName = nameParts.join(' ');
  const attending = row.attendance === 'Attending';

  const payload = {
    email: row.email,
    firstName: firstName,
    lastName: lastName,
    fullName: row.name,
    companyName: row.business,
    tags: [
      'beyond-the-tender-2026-rsvp',
      attending ? 'beyond-the-tender-2026-attending' : 'beyond-the-tender-2026-declined'
    ],
    source: 'Beyond the Tender 2026 RSVP form',
    event: row.event,
    rsvp_timestamp_iso: row.timestamp.toISOString(),
    attending: attending ? 'Yes' : 'No',
    hotel_preference: row.hotel,
    dietary_notes: row.notes,
    submission_id: row.submissionId
  };

  const response = UrlFetchApp.fetch(url, {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  });
  const statusCode = response.getResponseCode();
  const responseText = clean_(response.getContentText(), 500);

  return statusCode >= 200 && statusCode < 300
    ? { ok: true, status: 'Sent', detail: 'HTTP ' + statusCode }
    : { ok: false, status: 'Failed', detail: 'HTTP ' + statusCode + (responseText ? ': ' + responseText : '') };
}

function updateDelivery_(submissionId, delivery) {
  const lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    const sheet = sheet_();
    const lastRow = sheet.getLastRow();
    if (lastRow < 2) return;
    const ids = sheet.getRange(2, 12, lastRow - 1, 1).getDisplayValues();
    for (let i = ids.length - 1; i >= 0; i--) {
      if (ids[i][0] === submissionId) {
        sheet.getRange(i + 2, 10, 1, 2).setValues([[sheetText_(delivery.status), sheetText_(delivery.detail)]]);
        return;
      }
    }
  } finally {
    lock.releaseLock();
  }
}

function ensureHeaders_(sheet) {
  const current = sheet.getRange(1, 1, 1, HEADERS.length).getDisplayValues()[0];
  if (current.join('|') !== HEADERS.join('|')) {
    throw new Error('The RSVP sheet headers do not match the endpoint schema');
  }
}

function isDuplicate_(sheet, email, event) {
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return false;
  const count = Math.min(lastRow - 1, 100);
  const values = sheet.getRange(lastRow - count + 1, 1, count, HEADERS.length).getValues();
  const fiveMinutesAgo = Date.now() - 5 * 60 * 1000;

  return values.some(function (r) {
    const timestamp = r[0] instanceof Date ? r[0].getTime() : new Date(r[0]).getTime();
    return String(r[3] || '').toLowerCase() === email && String(r[7] || '') === event && timestamp >= fiveMinutesAgo;
  });
}

function isEmail_(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

function clean_(value, maxLength) {
  return String(value || '').trim().slice(0, maxLength || 500);
}

// Sheets treats a cell starting with = + - @ (or a leading tab / CR) as a
// formula. Prefix an apostrophe so user text is always stored as literal text.
// getValues() returns the text without the apostrophe.
function sheetText_(value) {
  const text = String(value == null ? '' : value);
  return /^[=+\-@\t\r]/.test(text) ? "'" + text : text;
}

function json_(body) {
  return ContentService.createTextOutput(JSON.stringify(body))
    .setMimeType(ContentService.MimeType.JSON);
}

