// dcFtobAttribution.js
(function (root) {
  'use strict';

  var STORAGE_KEY = 'dc_ftob_utm';
  var MAX_VALUE_LENGTH = 100;
  var ATTRIBUTION_FIELDS = [
    'utm_source',
    'utm_medium',
    'utm_campaign',
    'utm_content',
    'utm_term'
  ];

  function cleanString(value) {
    if (typeof value !== 'string') {
      return null;
    }

    var trimmed = value.trim();
    if (trimmed.length === 0 || trimmed.length > MAX_VALUE_LENGTH) {
      return null;
    }

    return trimmed;
  }

  function normalizeRecord(input) {
    if (!input || typeof input !== 'object' || Array.isArray(input)) {
      return {};
    }

    var source = cleanString(input.utm_source);
    if (!source) {
      return {};
    }

    var record = { utm_source: source };
    for (var i = 1; i < ATTRIBUTION_FIELDS.length; i += 1) {
      var field = ATTRIBUTION_FIELDS[i];
      var value = cleanString(input[field]);
      if (value) {
        record[field] = value;
      }
    }

    return record;
  }

  function readCurrentQuery(search) {
    var params;
    try {
      params = new URLSearchParams(search || '');
    } catch (error) {
      return {};
    }

    var source = cleanString(params.get('utm_source'));
    if (!source) {
      return {};
    }

    var record = { utm_source: source };
    for (var i = 1; i < ATTRIBUTION_FIELDS.length; i += 1) {
      var field = ATTRIBUTION_FIELDS[i];
      var value = cleanString(params.get(field));
      if (value) {
        record[field] = value;
      }
    }

    return record;
  }

  function readSavedRecord() {
    var raw;
    try {
      if (!root.localStorage) {
        return {};
      }
      raw = root.localStorage.getItem(STORAGE_KEY);
    } catch (error) {
      return {};
    }

    if (typeof raw !== 'string' || raw.length === 0) {
      return {};
    }

    try {
      return normalizeRecord(JSON.parse(raw));
    } catch (error) {
      return {};
    }
  }

  function writeSavedRecord(record) {
    try {
      if (!root.localStorage) {
        return;
      }
      root.localStorage.setItem(STORAGE_KEY, JSON.stringify(record));
    } catch (error) {
      // Storage can be blocked. The current tagged query still returns.
    }
  }

  function dcFtobAttribution() {
    var search = '';
    try {
      if (root.location && typeof root.location.search === 'string') {
        search = root.location.search;
      }
    } catch (error) {
      search = '';
    }

    // Last tagged touch wins: a valid current utm_source replaces the whole saved record.
    var current = readCurrentQuery(search);
    if (current.utm_source) {
      writeSavedRecord(current);
      return current;
    }

    // Untagged: ignore partial current UTMs without source and read the saved record.
    return readSavedRecord();
  }

  root.dcFtobAttribution = dcFtobAttribution;
})(typeof window !== 'undefined' ? window : globalThis);
