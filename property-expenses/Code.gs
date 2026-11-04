/**
 * Property Expense Tracker — Google Apps Script (bound to a Google Sheet)
 *
 * Weekly, it scans a Google Drive folder (and its subfolders) for receipts and
 * invoices (PDFs, phone photos, Google Docs, text files), runs them through
 * Google Drive's free built-in OCR, and adds one row per new file:
 *
 *   Date | Vendor | Total | Receipt | Status | Notes | File ID (hidden)
 *
 * A TOTAL row always sits at the bottom of the list.
 *
 * Nothing is guessed silently: if the total can't be read with confidence, the
 * Total cell is left BLANK, the row is highlighted, and the possible amounts
 * are put in Notes. You fill it in and change Status to "OK".
 *
 * Setup: see README.md in this folder.
 */

// ============================ SETTINGS ============================

const CONFIG = {
  // The ID of the Drive folder with the receipts. It's the last part of the
  // folder's URL: https://drive.google.com/drive/folders/<THIS_PART>
  FOLDER_ID: 'PASTE_FOLDER_ID_HERE',

  SHEET_NAME: 'Expenses',

  // Australian receipts write dates day-first (03/04/2026 = 3 April).
  DATE_ORDER: 'DMY',

  // Also look inside subfolders of the receipts folder.
  INCLUDE_SUBFOLDERS: true,

  // Email a summary after each run that added rows (to the account that owns
  // the script). Rows needing a check are listed first.
  EMAIL_SUMMARY: true,

  // Day and hour (24h, the script's time zone) for the weekly run.
  WEEKLY_DAY: 'MONDAY',
  WEEKLY_HOUR: 7,

  // Vendors to recognise by name anywhere in the receipt. Add your regular
  // tradies/suppliers here. The text on the left is matched (case-insensitive),
  // the text on the right is what goes in the sheet.
  KNOWN_VENDORS: {
    'bunnings': 'Bunnings',
    'mitre 10': 'Mitre 10',
    'officeworks': 'Officeworks',
    'reece': 'Reece',
    'tradelink': 'Tradelink',
    'total tools': 'Total Tools',
    'sydney tools': 'Sydney Tools',
    'beaumont tiles': 'Beaumont Tiles',
    'harvey norman': 'Harvey Norman',
    'the good guys': 'The Good Guys',
    'jb hi-fi': 'JB Hi-Fi',
    'kmart': 'Kmart',
    'ikea': 'IKEA',
    'amazon': 'Amazon',
    'woolworths': 'Woolworths',
    'coles': 'Coles',
    'home hardware': 'Home Hardware',
    'stratco': 'Stratco',
    'dulux': 'Dulux',
    'taubmans': 'Taubmans',
    'haymes': 'Haymes',
    'bcf': 'BCF',
    'supercheap': 'Supercheap Auto',
    'carpet court': 'Carpet Court',
    'tile republic': 'Tile Republic',
    'middys': 'Middy\'s',
    'lincraft': 'Lincraft',
    'spotlight': 'Spotlight',
    'big w': 'Big W',
    'aldi': 'ALDI',
  },

  // Stop early so a run never hits Apps Script's 6-minute limit. Whatever is
  // left over is picked up by the next run (or click "Process now" again).
  MAX_RUNTIME_MS: 4.5 * 60 * 1000,
};

const HEADERS = ['Date', 'Vendor', 'Total', 'Receipt', 'Status', 'Notes', 'File ID'];
const COL = { DATE: 1, VENDOR: 2, TOTAL: 3, LINK: 4, STATUS: 5, NOTES: 6, FILE_ID: 7 };
const TOTAL_LABEL = 'TOTAL';

// File types Drive's OCR can read directly.
const OCR_MIME_TYPES = [
  'application/pdf', 'image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp',
];

// ============================ MENU & TRIGGERS ============================

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('Receipts')
    .addItem('Sync now', 'processReceipts')
    .addItem('Re-read selected row(s)', 'reprocessSelectedRows')
    .addSeparator()
    .addItem('Turn on weekly run + Sync checkbox', 'installTriggers')
    .addItem('Turn off weekly run + Sync checkbox', 'removeTriggers')
    .addToUi();
  try { ensureSyncCheckbox_(getOrCreateSheet_()); } catch (e) { /* not fatal */ }
}

// Kept for anyone who set up the earlier version.
function installWeeklyTrigger() { installTriggers(); }

function installTriggers() {
  removeTriggers();
  ScriptApp.newTrigger('processReceipts')
    .timeBased()
    .everyWeeks(1)
    .onWeekDay(ScriptApp.WeekDay[CONFIG.WEEKLY_DAY])
    .atHour(CONFIG.WEEKLY_HOUR)
    .create();
  // An installable edit trigger: unlike menus, this also fires when the
  // checkbox is ticked in the Google Sheets phone app.
  ScriptApp.newTrigger('onSyncCheckbox')
    .forSpreadsheet(SpreadsheetApp.getActiveSpreadsheet())
    .onEdit()
    .create();
  ensureSyncCheckbox_(getOrCreateSheet_());
  toast_('Weekly run is on (' + CONFIG.WEEKLY_DAY.toLowerCase() + 's around ' + CONFIG.WEEKLY_HOUR +
    ':00). Tick "Sync now" at the top of the sheet any time.');
}

function removeTriggers() {
  const handlers = ['processReceipts', 'onSyncCheckbox', 'continueProcessing'];
  ScriptApp.getProjectTriggers()
    .filter(t => handlers.indexOf(t.getHandlerFunction()) !== -1)
    .forEach(t => ScriptApp.deleteTrigger(t));
}

// ============================ SYNC CHECKBOX ============================
// I1 holds a "Sync now" checkbox; H1 shows its status.

const SYNC_LABEL_CELL = 'H1';
const SYNC_BOX_CELL = 'I1';

function ensureSyncCheckbox_(sheet) {
  const box = sheet.getRange(SYNC_BOX_CELL);
  if (box.getDataValidation() === null) {
    box.insertCheckboxes().setValue(false);
    const label = sheet.getRange(SYNC_LABEL_CELL);
    if (!label.getValue()) label.setValue('Sync now →');
    label.setFontWeight('bold').setHorizontalAlignment('right');
    sheet.setColumnWidth(8, 230);
  }
}

function onSyncCheckbox(e) {
  if (!e || !e.range) return;
  const sheet = e.range.getSheet();
  if (sheet.getName() !== CONFIG.SHEET_NAME || e.range.getA1Notation() !== SYNC_BOX_CELL) return;
  if (e.range.getValue() !== true) return;

  const label = sheet.getRange(SYNC_LABEL_CELL);
  label.setValue('Syncing… (keep this open or come back in a minute)');
  SpreadsheetApp.flush();
  let msg;
  try {
    msg = processReceipts();
  } catch (err) {
    msg = 'Sync failed: ' + err.message;
  }
  e.range.setValue(false);
  label.setValue(msg || 'Sync now →');
}

/** Runs again a minute later when a sync ran out of time, until everything is in. */
function continueProcessing() {
  ScriptApp.getProjectTriggers()
    .filter(t => t.getHandlerFunction() === 'continueProcessing')
    .forEach(t => ScriptApp.deleteTrigger(t));
  const msg = processReceipts();
  try {
    const sheet = getOrCreateSheet_();
    sheet.getRange(SYNC_LABEL_CELL).setValue(msg);
  } catch (e) { /* not fatal */ }
}

function scheduleContinuation_() {
  const already = ScriptApp.getProjectTriggers().some(t => t.getHandlerFunction() === 'continueProcessing');
  if (!already) ScriptApp.newTrigger('continueProcessing').timeBased().after(60 * 1000).create();
}

// ============================ MAIN ============================

function processReceipts() {
  const started = Date.now();
  if (!CONFIG.FOLDER_ID || CONFIG.FOLDER_ID === 'PASTE_FOLDER_ID_HERE') {
    throw new Error('Set CONFIG.FOLDER_ID at the top of Code.gs to your receipts folder ID.');
  }
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(10 * 1000)) {
    const busy = 'A sync is already running — check back in a few minutes.';
    toast_(busy);
    return busy;
  }

  try {
    const sheet = getOrCreateSheet_();
    ensureSyncCheckbox_(sheet);
    const known = getProcessedFileIds_(sheet);
    const files = listFiles_(DriveApp.getFolderById(CONFIG.FOLDER_ID), CONFIG.INCLUDE_SUBFOLDERS);
    const pending = files.filter(f => !known.has(f.getId()));

    const added = [];
    let skippedForTime = 0;
    for (const file of pending) {
      if (Date.now() - started > CONFIG.MAX_RUNTIME_MS) {
        skippedForTime = pending.length - added.length;
        break;
      }
      const row = buildRow_(file);
      appendRow_(sheet, row);
      added.push(row);
    }

    ensureTotalRow_(sheet);
    if (skippedForTime) scheduleContinuation_();
    if (added.length && CONFIG.EMAIL_SUMMARY) sendSummary_(added, skippedForTime);

    const when = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'd MMM h:mm a');
    let msg = 'Last sync ' + when + ': ' + (added.length
      ? added.length + ' added, ' + added.filter(r => r.status !== 'OK').length + ' to check.'
      : 'nothing new.');
    if (skippedForTime) msg += ' ' + skippedForTime + ' more coming automatically in ~1 min.';
    toast_(msg);
    return msg;
  } finally {
    lock.releaseLock();
  }
}

/** Re-OCR the selected rows (e.g. after replacing a blurry photo). Overwrites Date/Vendor/Total/Status/Notes. */
function reprocessSelectedRows() {
  const sheet = getOrCreateSheet_();
  const range = sheet.getActiveRange();
  if (!range) return;
  for (let r = range.getRow(); r < range.getRow() + range.getNumRows(); r++) {
    const fileId = String(sheet.getRange(r, COL.FILE_ID).getValue() || '');
    if (!fileId) continue;
    const row = buildRow_(DriveApp.getFileById(fileId));
    writeRow_(sheet, r, row);
  }
  toast_('Re-read ' + range.getNumRows() + ' row(s).');
}

// ============================ BUILD A ROW ============================

function buildRow_(file) {
  const row = {
    fileId: file.getId(),
    fileName: file.getName(),
    url: file.getUrl(),
    date: null, vendor: '', total: null, status: 'OK', notes: [],
  };

  let text = '';
  try {
    text = extractText_(file);
  } catch (e) {
    row.status = 'CHECK';
    row.notes.push('Could not read file: ' + e.message);
    return finishRow_(row);
  }

  if (!text || text.replace(/\s/g, '').length < 10) {
    row.status = 'CHECK';
    row.notes.push('No readable text (blurry photo, or unsupported file type: ' + file.getMimeType() + ').');
    return finishRow_(row);
  }

  const parsed = parseReceipt(text, {
    dateOrder: CONFIG.DATE_ORDER,
    knownVendors: CONFIG.KNOWN_VENDORS,
    fileName: file.getName(),
    today: new Date(),
  });

  row.date = parsed.date;
  row.vendor = parsed.vendor;
  row.total = parsed.total;
  row.notes = row.notes.concat(parsed.issues);
  if (parsed.issues.length) row.status = 'CHECK';
  return finishRow_(row);
}

function finishRow_(row) {
  row.notes = row.notes.join(' ');
  return row;
}

// ============================ OCR ============================

/**
 * Returns the text of a Drive file. Uses Drive's free OCR (converting a copy
 * to a Google Doc, reading it, then deleting the copy).
 */
function extractText_(file) {
  const mime = file.getMimeType();

  if (mime === MimeType.GOOGLE_DOCS) return DocumentApp.openById(file.getId()).getBody().getText();
  if (mime === MimeType.GOOGLE_SHEETS) return sheetText_(file.getId());
  if (mime.indexOf('text/') === 0) return file.getBlob().getDataAsString();

  let blob;
  if (OCR_MIME_TYPES.indexOf(mime) !== -1) {
    blob = file.getBlob();
  } else if (mime.indexOf('image/') === 0) {
    // e.g. iPhone HEIC photos: Drive's OCR can't read them directly, but Drive
    // can render a large JPEG preview of them, which OCR can read.
    blob = largePreviewJpeg_(file.getId());
  } else {
    throw new Error('unsupported file type ' + mime);
  }

  const doc = Drive.Files.create(
    { name: '[tmp OCR] ' + file.getName(), mimeType: MimeType.GOOGLE_DOCS },
    blob,
    { ocrLanguage: 'en', fields: 'id' }
  );
  try {
    return DocumentApp.openById(doc.id).getBody().getText();
  } finally {
    try { Drive.Files.remove(doc.id); } catch (e) { /* best effort */ }
  }
}

function largePreviewJpeg_(fileId) {
  const meta = Drive.Files.get(fileId, { fields: 'thumbnailLink' });
  if (!meta.thumbnailLink) throw new Error('Drive has no preview for this file yet — try again next run');
  const url = meta.thumbnailLink.replace(/=s\d+$/, '=s2400');
  const resp = UrlFetchApp.fetch(url, {
    headers: { Authorization: 'Bearer ' + ScriptApp.getOAuthToken() },
    muteHttpExceptions: true,
  });
  if (resp.getResponseCode() !== 200) throw new Error('could not get a readable copy of the photo');
  return resp.getBlob().setName('preview.jpg').setContentType('image/jpeg');
}

function sheetText_(id) {
  return SpreadsheetApp.openById(id).getSheets()
    .map(s => s.getDataRange().getDisplayValues().map(r => r.join('  ')).join('\n'))
    .join('\n');
}

// ============================ PARSING (pure functions) ============================
// These don't touch Google services, so they can be tested outside Apps Script.

const MONEY_RE = /(-?)\$?\s?((?:\d{1,3}(?:[,\s]\d{3})+|\d+)[.,]\d{2})(?!\d)/g;

// Ordered strongest first. "Amount due" beats a bare "Total".
const TOTAL_PATTERNS = [
  { re: /\b(balance|amount|total)\s+(due|payable|owing)\b/i, weight: 6 },
  { re: /\bgrand\s+total\b/i, weight: 6 },
  { re: /\binvoice\s+total\b/i, weight: 6 },
  { re: /\btotal\s*(\(?\s*inc(l(uding|\.)?)?\.?\s*gst\s*\)?)/i, weight: 5 },
  { re: /\btotal\s+(aud|amount|price|payable|sale|paid)\b/i, weight: 5 },
  { re: /\bamount\s+paid\b/i, weight: 4 },
  { re: /\btotal\b/i, weight: 3 },
  { re: /\b(eftpos|visa|mastercard|amex|credit|debit|card)\b/i, weight: 1 },
];

// Lines that look like totals but aren't the amount spent.
const NOT_TOTAL_RE = /\b(sub[\s-]?total|total\s+(gst|tax|savings?|discount|items?|qty|quantity|excl?\.?|ex\s+gst)|gst|tax\b|change|rounding|cash\s+out|tendered|cash\s*$|saved|you\s+save|points|deposit\s+paid|previous)/i;

function parseReceipt(text, opts) {
  opts = opts || {};
  const lines = String(text).split(/\r?\n/).map(l => l.trim()).filter(Boolean);
  const issues = [];

  // ---- Total ----
  const totalResult = findTotal_(lines);
  let total = null;
  if (totalResult.confident) {
    total = totalResult.amount;
  } else {
    issues.push('Total not confidently read' +
      (totalResult.candidates.length ? ' — possible: ' + totalResult.candidates.map(fmtMoney_).join(', ') : '') + '.');
  }
  if (totalResult.conflict) issues.push(totalResult.conflict);

  // ---- Date ----
  const date = findDate_(lines, opts.dateOrder || 'DMY', opts.today || new Date());
  if (!date) issues.push('Date not found.');

  // ---- Vendor ----
  const v = findVendor_(lines, opts.knownVendors || {}, opts.fileName || '');
  if (!v.vendor) issues.push('Vendor not found.');
  else if (!v.confident) issues.push('Vendor is a best guess.');

  return { date: date, vendor: v.vendor, total: total, issues: issues };
}

function parseMoney_(s) {
  // "1,234.56" / "1 234.56" / "12,50" (comma decimal)
  s = s.replace(/\s/g, '');
  if (/,\d{2}$/.test(s) && s.indexOf('.') === -1) s = s.replace(/,(\d{2})$/, '.$1');
  return Math.round(parseFloat(s.replace(/,/g, '')) * 100) / 100;
}

function amountsIn_(line) {
  const out = [];
  let m;
  MONEY_RE.lastIndex = 0;
  while ((m = MONEY_RE.exec(line)) !== null) {
    const v = parseMoney_(m[2]);
    if (!isNaN(v)) out.push(m[1] === '-' ? -v : v);
  }
  return out;
}

function findTotal_(lines) {
  const hits = []; // {amount, weight}
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (NOT_TOTAL_RE.test(line) && !/\b(amount|balance)\s+(due|payable)|grand\s+total|total\s*\(?inc/i.test(line)) continue;
    const pat = TOTAL_PATTERNS.find(p => p.re.test(line));
    if (!pat) continue;

    // Amount on the same line, else on the next line or two (OCR often splits
    // label and number onto separate lines).
    let amts = amountsIn_(line);
    for (let k = 1; !amts.length && k <= 2 && i + k < lines.length; k++) {
      if (NOT_TOTAL_RE.test(lines[i + k])) break;
      amts = amountsIn_(lines[i + k]);
    }
    amts = amts.filter(a => a > 0);
    if (amts.length) hits.push({ amount: amts[amts.length - 1], weight: pat.weight });
  }

  const allAmounts = uniq_(lines.reduce((acc, l) => acc.concat(amountsIn_(l)), []).filter(a => a > 0));
  const topCandidates = allAmounts.slice().sort((a, b) => b - a).slice(0, 3);

  if (!hits.length) return { confident: false, candidates: topCandidates };

  const best = Math.max.apply(null, hits.map(h => h.weight));
  const bestAmounts = uniq_(hits.filter(h => h.weight === best).map(h => h.amount));

  // Only card/EFTPOS lines matched — usable but weak.
  if (best <= 1) return { confident: false, candidates: uniq_(bestAmounts.concat(topCandidates)).slice(0, 3) };

  if (bestAmounts.length > 1) {
    // Different "totals" on the same receipt — the biggest is usually right
    // (e.g. two invoices on one page is the other case), but ask.
    return { confident: false, candidates: bestAmounts.sort((a, b) => b - a).slice(0, 3) };
  }

  const amount = bestAmounts[0];
  // Sanity check: the total should usually be the largest amount on the
  // receipt, apart from cash tendered. Flag if something much bigger appears
  // on a line not explained as cash/tendered.
  const result = { confident: true, amount: amount, candidates: [amount] };
  const strongerOther = hits.find(h => h.weight >= 3 && h.amount > amount * 1.01);
  if (strongerOther) {
    result.conflict = 'Another total-like amount found (' + fmtMoney_(strongerOther.amount) + ') — please check.';
  }
  return result;
}

const MONTHS = { jan: 1, feb: 2, mar: 3, apr: 4, may: 5, jun: 6, jul: 7, aug: 8, sep: 9, sept: 9, oct: 10, nov: 11, dec: 12 };

function findDate_(lines, order, today) {
  const candidates = []; // {date, weight}
  const maxAgeMs = 5 * 365 * 24 * 3600 * 1000;
  const add = (y, m, d, line) => {
    if (y < 100) y += 2000;
    if (m < 1 || m > 12 || d < 1 || d > 31) return;
    const dt = new Date(y, m - 1, d);
    if (dt.getMonth() !== m - 1) return; // e.g. 31/02
    if (dt.getTime() > today.getTime() + 24 * 3600 * 1000) return; // future
    if (today.getTime() - dt.getTime() > maxAgeMs) return;
    let weight = 1;
    if (/\b(invoice|tax\s+invoice|transaction|purchase|issue|txn|receipt)?\s*date\b/i.test(line)) weight = 3;
    if (/\b(due|expir|valid|exp\.?)\b/i.test(line)) weight = 0; // due/expiry dates aren't the purchase date
    candidates.push({ date: dt, weight: weight });
  };

  lines.forEach(line => {
    let m;
    // 2026-10-12
    const iso = /\b(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})\b/g;
    while ((m = iso.exec(line))) add(+m[1], +m[2], +m[3], line);
    // 12/10/2026, 12-10-26, 12.10.2026
    const num = /\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{2}|\d{4})\b/g;
    while ((m = num.exec(line))) {
      if (order === 'MDY') add(+m[3], +m[1], +m[2], line);
      else add(+m[3], +m[2], +m[1], line);
    }
    // 12 Oct 2026, 12-Oct-26, 12th October 2026
    const dmy = /\b(\d{1,2})(?:st|nd|rd|th)?[\s\-.]+([A-Za-z]{3,9})\.?,?[\s\-.]+(\d{2,4})\b/g;
    while ((m = dmy.exec(line))) {
      const mo = MONTHS[m[2].toLowerCase().slice(0, m[2].toLowerCase().indexOf('sept') === 0 ? 4 : 3)];
      if (mo) add(+m[3], mo, +m[1], line);
    }
    // Oct 12, 2026
    const mdy = /\b([A-Za-z]{3,9})\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b/g;
    while ((m = mdy.exec(line))) {
      const mo = MONTHS[m[1].toLowerCase().slice(0, 3)];
      if (mo) add(+m[3], mo, +m[2], line);
    }
  });

  const usable = candidates.filter(c => c.weight > 0);
  if (!usable.length) return null;
  usable.sort((a, b) => b.weight - a.weight);
  return usable[0].date;
}

const NOT_VENDOR_RE = /^(tax\s+invoice|invoice|receipt|tax\s+receipt|sales\s+receipt|customer\s+copy|merchant\s+copy|statement|quote|quotation|order|welcome|thank|abn|acn|ph|phone|tel|fax|email|www\.|http|date|time|page|bill\s+to|ship\s+to|sold\s+to|to:|from:|\d)/i;

function findVendor_(lines, knownVendors, fileName) {
  const haystack = (lines.slice(0, 40).join('\n') + '\n' + fileName).toLowerCase();
  const keys = Object.keys(knownVendors).sort((a, b) => b.length - a.length);
  for (const k of keys) {
    if (haystack.indexOf(k.toLowerCase()) !== -1) return { vendor: knownVendors[k], confident: true };
  }

  // "From: X Pty Ltd" / a line containing a company suffix is a good signal.
  for (const line of lines.slice(0, 25)) {
    const m = line.match(/^([A-Za-z0-9&'.,\- ]{2,60}?\b(pty\.?\s*ltd|pty|ltd|limited|group|plumbing|electrical|builders?|constructions?|services|trades?|hardware|supplies|landscaping|roofing|painting|carpentry))\b/i);
    if (m && !NOT_VENDOR_RE.test(line)) return { vendor: tidy_(m[1]), confident: false };
  }

  // First plausible line near the top of the receipt.
  for (const line of lines.slice(0, 8)) {
    if (NOT_VENDOR_RE.test(line)) continue;
    const letters = (line.match(/[A-Za-z]/g) || []).length;
    if (letters < 3 || letters / line.length < 0.5) continue;
    if (/\b(street|st\.?|road|rd\.?|ave|avenue|drive|dr\.?|nsw|vic|qld|wa|sa|tas|act|nt)\b\s*\d{0,4}$/i.test(line)) continue;
    return { vendor: tidy_(line).slice(0, 60), confident: false };
  }
  return { vendor: '', confident: false };
}

function tidy_(s) {
  s = s.replace(/\s+/g, ' ').trim().replace(/[,.\-]+$/, '');
  if (s === s.toUpperCase()) s = s.toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
  return s;
}

function uniq_(arr) { return arr.filter((v, i) => arr.indexOf(v) === i); }
function fmtMoney_(n) { return '$' + n.toFixed(2); }

// ============================ SHEET ============================

function getOrCreateSheet_() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(CONFIG.SHEET_NAME);
  if (!sheet) {
    sheet = ss.insertSheet(CONFIG.SHEET_NAME);
  }
  if (sheet.getLastRow() === 0) {
    sheet.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]).setFontWeight('bold');
    sheet.setFrozenRows(1);
    sheet.setColumnWidth(COL.DATE, 100);
    sheet.setColumnWidth(COL.VENDOR, 220);
    sheet.setColumnWidth(COL.TOTAL, 110);
    sheet.setColumnWidth(COL.LINK, 220);
    sheet.setColumnWidth(COL.STATUS, 80);
    sheet.setColumnWidth(COL.NOTES, 380);
    sheet.hideColumns(COL.FILE_ID);
    addHighlightRule_(sheet);
    ensureTotalRow_(sheet);
  }
  return sheet;
}

function addHighlightRule_(sheet) {
  const rule = SpreadsheetApp.newConditionalFormatRule()
    .whenFormulaSatisfied('=$E2="CHECK"')
    .setBackground('#fde8c8')
    .setRanges([sheet.getRange('A2:F')])
    .build();
  sheet.setConditionalFormatRules(sheet.getConditionalFormatRules().concat([rule]));

  const status = SpreadsheetApp.newDataValidation()
    .requireValueInList(['OK', 'CHECK'], true).setAllowInvalid(true).build();
  sheet.getRange('E2:E').setDataValidation(status);
}

function findTotalRow_(sheet) {
  const last = sheet.getLastRow();
  if (last < 2) return 0;
  const colA = sheet.getRange(2, COL.DATE, last - 1, 1).getDisplayValues();
  for (let i = colA.length - 1; i >= 0; i--) {
    if (colA[i][0] === TOTAL_LABEL) return i + 2;
  }
  return 0;
}

/** Makes sure exactly one TOTAL row exists at the bottom, summing everything above it. */
function ensureTotalRow_(sheet) {
  let r = findTotalRow_(sheet);
  if (!r) {
    r = Math.max(sheet.getLastRow(), 1) + 1;
    sheet.getRange(r, COL.DATE).setValue(TOTAL_LABEL);
  } else if (r !== sheet.getLastRow()) {
    // Someone added rows under it by hand — move TOTAL back to the bottom.
    sheet.getRange(r, 1, 1, HEADERS.length).clearContent().clearFormat();
    r = sheet.getLastRow() + 1;
    sheet.getRange(r, COL.DATE).setValue(TOTAL_LABEL);
  }
  // INDIRECT keeps the sum correct however many rows get inserted above.
  sheet.getRange(r, COL.TOTAL).setFormula('=SUM(INDIRECT("C2:C"&ROW()-1))').setNumberFormat('$#,##0.00');
  sheet.getRange(r, 1, 1, HEADERS.length).setFontWeight('bold').setBorder(true, null, null, null, null, null);
  sheet.getRange(r, COL.STATUS).setFormula('=IF(COUNTIF(INDIRECT("E2:E"&ROW()-1),"CHECK"),COUNTIF(INDIRECT("E2:E"&ROW()-1),"CHECK")&" to check","")');
}

function appendRow_(sheet, row) {
  const totalRow = findTotalRow_(sheet);
  let r;
  if (totalRow) {
    sheet.insertRowBefore(totalRow);
    r = totalRow;
    sheet.getRange(r, 1, 1, HEADERS.length).setFontWeight('normal').setBorder(false, false, false, false, false, false);
  } else {
    r = sheet.getLastRow() + 1;
  }
  writeRow_(sheet, r, row);
}

function writeRow_(sheet, r, row) {
  const link = SpreadsheetApp.newRichTextValue().setText(row.fileName).setLinkUrl(row.url).build();
  sheet.getRange(r, COL.DATE).setValue(row.date || '').setNumberFormat('dd/mm/yyyy');
  sheet.getRange(r, COL.VENDOR).setValue(row.vendor || '');
  sheet.getRange(r, COL.TOTAL).setValue(row.total === null ? '' : row.total).setNumberFormat('$#,##0.00');
  sheet.getRange(r, COL.LINK).setRichTextValue(link);
  sheet.getRange(r, COL.STATUS).setValue(row.status);
  sheet.getRange(r, COL.NOTES).setValue(row.notes || '');
  sheet.getRange(r, COL.FILE_ID).setValue(row.fileId);
}

function getProcessedFileIds_(sheet) {
  const last = sheet.getLastRow();
  const ids = new Set();
  if (last < 2) return ids;
  sheet.getRange(2, COL.FILE_ID, last - 1, 1).getValues().forEach(r => { if (r[0]) ids.add(String(r[0])); });
  return ids;
}

// ============================ DRIVE ============================

function listFiles_(folder, recurse) {
  const out = [];
  const files = folder.getFiles();
  while (files.hasNext()) {
    const f = files.next();
    if (f.getMimeType() === MimeType.FOLDER || f.getName().indexOf('[tmp OCR]') === 0) continue;
    out.push(f);
  }
  if (recurse) {
    const subs = folder.getFolders();
    while (subs.hasNext()) Array.prototype.push.apply(out, listFiles_(subs.next(), true));
  }
  out.sort((a, b) => a.getDateCreated() - b.getDateCreated());
  return out;
}

// ============================ NOTIFY ============================

function sendSummary_(rows, leftOver) {
  const flagged = rows.filter(r => r.status !== 'OK');
  const ok = rows.filter(r => r.status === 'OK');
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const line = r => '• ' + r.fileName + ' — ' + (r.vendor || '?') + ', ' +
    (r.total === null ? 'total ?' : fmtMoney_(r.total)) + (r.notes ? '\n    ' + r.notes : '');

  let body = 'Receipts added this run: ' + rows.length + '\n\n';
  if (flagged.length) body += 'NEED YOUR CHECK (' + flagged.length + '):\n' + flagged.map(line).join('\n') + '\n\n';
  if (ok.length) body += 'Read OK (' + ok.length + '):\n' + ok.map(line).join('\n') + '\n\n';
  if (leftOver) body += leftOver + ' more file(s) are being added automatically in about a minute.\n\n';
  body += 'Open the sheet: ' + ss.getUrl();

  MailApp.sendEmail(Session.getEffectiveUser().getEmail(),
    'Property receipts: ' + rows.length + ' added' + (flagged.length ? ', ' + flagged.length + ' to check' : ''),
    body);
}

function toast_(msg) {
  try { SpreadsheetApp.getActiveSpreadsheet().toast(msg, 'Receipts', 8); } catch (e) { console.log(msg); }
}

// Allow the parser to be unit-tested in Node.
if (typeof module !== 'undefined') module.exports = { parseReceipt };
