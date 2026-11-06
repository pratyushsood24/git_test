/**
 * Property Expense Tracker — Google Apps Script (bound to a Google Sheet)
 *
 * Scans a Google Drive folder (and subfolders) for receipts and invoices and
 * adds one row per file:
 *
 *   Date | Vendor | Total | Receipt | Status | Notes | File ID (hidden)
 *
 * How each file is read:
 *   1. Google Gemini (free tier) reads the PDF/photo and returns vendor, date,
 *      total, invoice number and document type.
 *   2. Google Drive's free OCR reads the same file as an independent check:
 *      Gemini's total must actually appear in the document text (or the file
 *      name). If it doesn't, the row is flagged instead of trusted.
 *   3. Duplicates (same file, same invoice number, or same vendor+date+amount)
 *      are flagged and NOT counted in the TOTAL.
 *   If Gemini isn't set up or its free daily limit is used up, the OCR-only
 *   reader is used and the row is re-read with Gemini on the next sync.
 *
 * Nothing doubtful is counted: uncertain totals are left blank, the row is
 * highlighted orange, and the reason is in Notes.
 *
 * Setup: see README.md in this folder.
 */

// ============================ SETTINGS ============================

const CONFIG = {
  // The ID of the Drive folder with the receipts. It's the last part of the
  // folder's URL: https://drive.google.com/drive/folders/<THIS_PART>
  FOLDER_ID: 'PASTE_FOLDER_ID_HERE',

  SHEET_NAME: 'Expenses',

  // The BUYER — you — is set from the sheet: Receipts → "Set my name(s)".
  // It's stored privately with the script, not in this code.

  // Free Gemini model. If Google retires this name, the script automatically
  // picks the newest available "flash-lite" model instead.
  GEMINI_MODEL: 'gemini-3.5-flash-lite',

  // Pause between Gemini calls so the free per-minute limit isn't hit.
  AI_MIN_GAP_MS: 4500,

  // Australian receipts write dates day-first (03/04/2026 = 3 April).
  DATE_ORDER: 'DMY',

  INCLUDE_SUBFOLDERS: true,

  // Email a summary after each sync that added rows.
  EMAIL_SUMMARY: true,

  WEEKLY_DAY: 'MONDAY',
  WEEKLY_HOUR: 7,

  // Vendor names are tidied to these so the same shop always has the same
  // name (e.g. "Bunnings Warehouse Belconnen" -> "Bunnings").
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
    'supercheap': 'Supercheap Auto',
    'carpet court': 'Carpet Court',
    'big w': 'Big W',
    'aldi': 'ALDI',
  },

  // Stop early so a run never hits Apps Script's 6-minute limit; the rest is
  // picked up automatically a minute later.
  MAX_RUNTIME_MS: 4.5 * 60 * 1000,
};

const HEADERS = ['Date', 'Vendor', 'Total', 'Receipt', 'Status', 'Notes', 'File ID'];
const COL = { DATE: 1, VENDOR: 2, TOTAL: 3, LINK: 4, STATUS: 5, NOTES: 6, FILE_ID: 7 };
const TOTAL_LABEL = 'TOTAL';
const AI_PENDING_TAG = '[AI pending]';

// File types Drive's OCR can read directly.
const OCR_MIME_TYPES = [
  'application/pdf', 'image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp',
];
// File types Gemini can read directly.
const AI_MIME_TYPES = [
  'application/pdf', 'image/jpeg', 'image/png', 'image/webp', 'image/heic', 'image/heif',
];

// ============================ MENU & TRIGGERS ============================

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('Receipts')
    .addItem('Sync now', 'processReceipts')
    .addItem('Re-read selected row(s)', 'reprocessSelectedRows')
    .addItem('Re-read ALL rows (fixes old readings)', 'reprocessAllRows')
    .addSeparator()
    .addItem('Set up free AI (Gemini) key', 'setGeminiKey')
    .addItem('Set my name(s) (so they\'re never the vendor)', 'setOwnNames')
    .addItem('Turn on weekly run + Sync checkbox', 'installTriggers')
    .addItem('Turn off weekly run + Sync checkbox', 'removeTriggers')
    .addToUi();
  try { ensureSyncCheckbox_(getOrCreateSheet_()); } catch (e) { /* not fatal */ }
}

// Kept for anyone who set up the earliest version.
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
  const handlers = ['processReceipts', 'onSyncCheckbox', 'continueProcessing', 'continueReprocessAll'];
  ScriptApp.getProjectTriggers()
    .filter(t => handlers.indexOf(t.getHandlerFunction()) !== -1)
    .forEach(t => ScriptApp.deleteTrigger(t));
}

function setGeminiKey() {
  const ui = SpreadsheetApp.getUi();
  const res = ui.prompt('Free Gemini API key',
    'Paste the key from aistudio.google.com/apikey (starts with "AIza").\n' +
    'Leave empty and click OK to remove the key and use OCR only.',
    ui.ButtonSet.OK_CANCEL);
  if (res.getSelectedButton() !== ui.Button.OK) return;
  const key = res.getResponseText().trim();
  const props = PropertiesService.getScriptProperties();
  if (!key) {
    props.deleteProperty('GEMINI_API_KEY');
    ui.alert('Key removed. Receipts will be read with OCR only.');
    return;
  }
  props.setProperty('GEMINI_API_KEY', key);
  props.deleteProperty('GEMINI_RESOLVED_MODEL');
  try {
    const model = resolveModel_(key, true);
    ui.alert('Key works (model: ' + model + ').\n\nNow use Receipts → "Re-read ALL rows" to fix existing rows.');
  } catch (e) {
    ui.alert('The key was saved but the test failed:\n' + e.message);
  }
}

/** Names/companies/addresses of the buyer, comma-separated, kept in script properties. */
function setOwnNames() {
  const ui = SpreadsheetApp.getUi();
  const current = ownNames_().join(', ');
  const res = ui.prompt('Your name(s)',
    'Names, company names and street that appear under "Bill to" on your invoices, separated by commas.\n' +
    'e.g.  Jane Citizen, Citizen Holdings, 12 Example St' + (current ? '\n\nCurrent: ' + current : ''),
    ui.ButtonSet.OK_CANCEL);
  if (res.getSelectedButton() !== ui.Button.OK) return;
  PropertiesService.getScriptProperties().setProperty('OWN_NAMES', res.getResponseText());
  ui.alert('Saved: ' + ownNames_().join(', '));
}

function ownNames_() {
  let raw = '';
  try { raw = PropertiesService.getScriptProperties().getProperty('OWN_NAMES') || ''; } catch (e) { /* tests */ }
  return raw.split(',').map(s => s.trim()).filter(s => s.length >= 3);
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
  deleteTriggersFor_('continueProcessing');
  const msg = processReceipts();
  try { getOrCreateSheet_().getRange(SYNC_LABEL_CELL).setValue(msg); } catch (e) { /* not fatal */ }
}

function scheduleOnce_(handler) {
  const already = ScriptApp.getProjectTriggers().some(t => t.getHandlerFunction() === handler);
  if (!already) ScriptApp.newTrigger(handler).timeBased().after(60 * 1000).create();
}

function deleteTriggersFor_(handler) {
  ScriptApp.getProjectTriggers()
    .filter(t => t.getHandlerFunction() === handler)
    .forEach(t => ScriptApp.deleteTrigger(t));
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
    const ctx = loadRows_(sheet);
    const outOfTime = () => Date.now() - started > CONFIG.MAX_RUNTIME_MS;
    const added = [];
    let leftOver = 0;

    // 1. Rows read without AI last time (key missing / daily limit) — retry them.
    if (geminiKey_()) {
      for (const existing of ctx.rows.filter(r => r.notes.indexOf(AI_PENDING_TAG) !== -1)) {
        if (outOfTime() || AI_STATE.exhausted) break;
        rereadRow_(sheet, ctx, existing);
      }
    }

    // 2. New files.
    const files = listFiles_(DriveApp.getFolderById(CONFIG.FOLDER_ID), CONFIG.INCLUDE_SUBFOLDERS);
    const pending = files.filter(f => !ctx.byFileId[f.getId()]);
    for (let i = 0; i < pending.length; i++) {
      if (outOfTime()) { leftOver = pending.length - i; break; }
      const row = buildRow_(pending[i], ctx.rows);
      const r = appendRow_(sheet, row);
      addToContext_(ctx, r, row);
      added.push(row);
    }

    ensureTotalRow_(sheet);
    if (leftOver) scheduleOnce_('continueProcessing');
    if (added.length && CONFIG.EMAIL_SUMMARY) sendSummary_(added, leftOver);

    const when = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'd MMM h:mm a');
    let msg = 'Last sync ' + when + ': ' + (added.length
      ? added.length + ' added, ' + added.filter(r => r.status !== 'OK').length + ' to check.'
      : 'nothing new.');
    if (leftOver) msg += ' ' + leftOver + ' more coming automatically in ~1 min.';
    if (AI_STATE.exhausted) msg += ' Free AI limit reached for today — those rows will be re-read next sync.';
    toast_(msg);
    return msg;
  } finally {
    lock.releaseLock();
  }
}

/** Re-read the selected rows (e.g. after replacing a blurry photo). */
function reprocessSelectedRows() {
  const sheet = getOrCreateSheet_();
  const range = sheet.getActiveRange();
  if (!range) return;
  const ctx = loadRows_(sheet);
  let n = 0;
  for (let r = range.getRow(); r < range.getRow() + range.getNumRows(); r++) {
    const existing = ctx.rows.find(x => x.row === r);
    if (!existing) continue;
    rereadRow_(sheet, ctx, existing);
    n++;
  }
  ensureTotalRow_(sheet);
  toast_('Re-read ' + n + ' row(s).');
}

/**
 * Re-read every row that came from a file, top to bottom, so readings from an
 * older version of the script (or without AI) are corrected and duplicates
 * are re-detected. Overwrites Date/Vendor/Total/Status/Notes on those rows.
 */
function reprocessAllRows() {
  try {
    const ui = SpreadsheetApp.getUi();
    const ok = ui.alert('Re-read ALL rows?',
      'Every row that links to a receipt will be read again. Date, Vendor, Total, Status and Notes ' +
      'on those rows will be replaced (rows you typed in yourself are not touched).',
      ui.ButtonSet.OK_CANCEL);
    if (ok !== ui.Button.OK) return;
  } catch (e) { /* running from a trigger — no UI */ }
  PropertiesService.getScriptProperties().setProperty('REPROCESS_FROM_ROW', '2');
  continueReprocessAll();
}

function continueReprocessAll() {
  deleteTriggersFor_('continueReprocessAll');
  const started = Date.now();
  const props = PropertiesService.getScriptProperties();
  const from = Number(props.getProperty('REPROCESS_FROM_ROW') || 0);
  if (!from) return;
  const sheet = getOrCreateSheet_();
  const ctx = loadRows_(sheet);
  // Rows above the starting point count as already-checked for duplicates.
  const targets = ctx.rows.filter(r => r.row >= from);
  ctx.rows = ctx.rows.filter(r => r.row < from);
  for (const existing of targets) {
    if (Date.now() - started > CONFIG.MAX_RUNTIME_MS) {
      props.setProperty('REPROCESS_FROM_ROW', String(existing.row));
      scheduleOnce_('continueReprocessAll');
      ensureTotalRow_(sheet);
      toast_('Re-reading… continues automatically in about a minute (from row ' + existing.row + ').');
      return;
    }
    ctx.rows.push(existing);
    rereadRow_(sheet, ctx, existing);
  }
  props.deleteProperty('REPROCESS_FROM_ROW');
  ensureTotalRow_(sheet);
  toast_('Finished re-reading all rows.');
}

function rereadRow_(sheet, ctx, existing) {
  let file;
  try { file = DriveApp.getFileById(existing.fileId); } catch (e) {
    sheet.getRange(existing.row, COL.STATUS).setValue('CHECK');
    sheet.getRange(existing.row, COL.NOTES).setValue('Receipt file no longer exists in Drive.');
    return;
  }
  const others = ctx.rows.filter(r => r.fileId !== existing.fileId);
  const row = buildRow_(file, others);
  writeRow_(sheet, existing.row, row);
  Object.assign(existing, toCtxRow_(existing.row, row));
}

// ============================ BUILD A ROW ============================

function buildRow_(file, existingRows) {
  const row = {
    fileId: file.getId(), fileName: file.getName(), url: file.getUrl(),
    date: null, vendor: '', total: null, status: 'OK', notes: [],
    invoiceNo: '', md5: '',
  };
  try { row.md5 = Drive.Files.get(row.fileId, { fields: 'md5Checksum' }).md5Checksum || ''; } catch (e) { /* ok */ }

  // ---- Get the file's content (and an image Gemini/OCR can read) ----
  let blob = null;
  let text = '';
  const mime = file.getMimeType();
  try {
    blob = readableBlob_(file); // null for Google Docs/Sheets/text
    text = extractText_(file, blob);
  } catch (e) {
    row.notes.push('Could not read file: ' + e.message);
  }

  // ---- Gemini ----
  let ai = null;
  let aiNote = '';
  if (geminiKey_()) {
    try {
      ai = geminiExtract_(blob, text, file.getName());
    } catch (e) {
      aiNote = e.message;
    }
  } else {
    aiNote = 'no AI key set';
  }

  // ---- OCR-only parse (used as fallback and as a cross-check) ----
  const ocr = parseReceipt(text, {
    dateOrder: CONFIG.DATE_ORDER, knownVendors: CONFIG.KNOWN_VENDORS,
    ownNames: ownNames_(), fileName: file.getName(), today: new Date(),
  });

  if (ai) {
    applyAi_(row, ai, text, ocr);
  } else {
    row.date = ocr.date;
    row.vendor = ocr.vendor;
    row.total = ocr.total;
    row.notes = row.notes.concat(ocr.issues);
    if (aiNote && aiNote !== 'no AI key set') {
      row.notes.push('AI unavailable (' + aiNote + ') — read with OCR only. ' + AI_PENDING_TAG);
      row.status = 'CHECK';
    }
  }

  if (!text && !ai) {
    row.notes.push('No readable text (blurry photo, or unsupported file type: ' + mime + ').');
  }

  // ---- Duplicates are never counted ----
  const dup = findDuplicate_(row, existingRows || []);
  if (dup) {
    const amt = row.total === null ? '' : ' (' + fmtMoney_(row.total) + ')';
    row.notes.unshift('DUPLICATE of row ' + dup.row + ' — ' + dup.reason + amt +
      '; not counted. If it really is a separate purchase, type the amount in.');
    row.total = null;
  }

  if (row.notes.length || row.total === null || !row.date || !row.vendor) row.status = 'CHECK';
  row.notes = row.notes.join(' ');
  return row;
}

/** Fill the row from Gemini's answer, checking it against the OCR text. */
function applyAi_(row, ai, text, ocr) {
  row.invoiceNo = String(ai.invoice_number || '').trim();
  row.vendor = canonicalVendor_(ai.vendor || '');
  if (!row.vendor && ocr.vendor) row.vendor = ocr.vendor;
  if (!row.vendor) row.notes.push('Vendor not found.');

  const d = ai.date && /^(\d{4})-(\d{2})-(\d{2})$/.exec(ai.date);
  if (d) {
    const dt = new Date(+d[1], +d[2] - 1, +d[3]);
    const ageDays = (Date.now() - dt.getTime()) / 86400000;
    if (ageDays < -1 || ageDays > 5 * 365) row.notes.push('Date ' + ai.date + ' looks wrong.');
    else row.date = dt;
  }
  if (!row.date) {
    row.date = ocr.date;
    if (!row.date) row.notes.push('Date not found.');
  }

  const type = String(ai.document_type || '').toLowerCase();
  let total = typeof ai.total === 'number' ? Math.round(ai.total * 100) / 100 : null;
  if (total !== null && type === 'refund' && total > 0) total = -total;

  if (type === 'quote' || type === 'statement') {
    row.notes.push('This looks like a ' + type + ', not a purchase' +
      (total !== null ? ' (' + fmtMoney_(total) + ')' : '') + ' — not counted.');
    return;
  }
  if (total === null || total === 0) {
    row.notes.push('Total not found' + (ai.reason ? ': ' + ai.reason : '') + '.');
    return;
  }

  // Cross-check: the total must really be printed in the document (OCR text)
  // or in the file name. Stops a misread or made-up number being counted.
  const printed = amountsInText_(text + '\n' + row.fileName).map(Math.abs);
  const grounded = printed.some(a => Math.abs(a - Math.abs(total)) < 0.005);
  if (grounded) {
    row.total = total;
    if (ai.confidence === 'low') row.notes.push('AI was unsure: ' + (ai.reason || 'check the receipt') + '.');
  } else if (!text) {
    row.notes.push('AI read ' + fmtMoney_(total) + ' but the file has no readable text to confirm it — please check.');
  } else {
    row.notes.push('AI read ' + fmtMoney_(total) + ' but that amount isn\'t in the document text' +
      (ocr.total !== null ? ' (OCR read ' + fmtMoney_(ocr.total) + ')' : '') + ' — please check.');
  }
  if (type === 'refund' && row.total !== null) row.notes.push('Refund — subtracted from the total.');
}

function canonicalVendor_(name) {
  name = String(name || '').trim();
  if (!name) return '';
  const lower = name.toLowerCase();
  if (ownNames_().some(n => lower.indexOf(n.toLowerCase()) !== -1)) return '';
  const keys = Object.keys(CONFIG.KNOWN_VENDORS).sort((a, b) => b.length - a.length);
  for (const k of keys) if (lower.indexOf(k) !== -1) return CONFIG.KNOWN_VENDORS[k];
  return tidy_(name.replace(/\b(pty\.?\s*ltd\.?|pty|ltd\.?|limited)\b/ig, ''));
}

// ============================ DUPLICATES ============================

function findDuplicate_(row, rows) {
  const norm = s => String(s || '').toLowerCase().replace(/[^a-z0-9]/g, '');
  const dayKey = d => (d instanceof Date && !isNaN(d)) ? d.toDateString() : '';
  for (const r of rows) {
    if (r.fileId === row.fileId) continue;
    if (row.md5 && r.md5 && row.md5 === r.md5) return { row: r.row, reason: 'identical file' };
    if (norm(row.invoiceNo).length >= 3 && norm(row.invoiceNo) === norm(r.invoiceNo) &&
        (!row.vendor || !r.vendor || norm(row.vendor) === norm(r.vendor))) {
      return { row: r.row, reason: 'same invoice number ' + row.invoiceNo };
    }
    if (row.total !== null && r.total !== null && row.total === r.total && row.vendor &&
        norm(row.vendor) === norm(r.vendor) && dayKey(row.date) && dayKey(row.date) === dayKey(r.date)) {
      return { row: r.row, reason: 'same vendor, date and amount' };
    }
  }
  return null;
}

// ============================ GEMINI (free tier) ============================

const AI_STATE = { lastCall: 0, exhausted: false, model: null };

function geminiKey_() {
  return PropertiesService.getScriptProperties().getProperty('GEMINI_API_KEY');
}

function geminiExtract_(blob, text, fileName) {
  if (AI_STATE.exhausted) throw new Error('free daily limit reached');
  const key = geminiKey_();
  const model = resolveModel_(key, false);

  const parts = [];
  if (blob && AI_MIME_TYPES.indexOf(blob.getContentType()) !== -1 && blob.getBytes().length < 15 * 1024 * 1024) {
    parts.push({ inline_data: { mime_type: blob.getContentType(), data: Utilities.base64Encode(blob.getBytes()) } });
  } else if (text) {
    parts.push({ text: 'DOCUMENT TEXT:\n' + text.slice(0, 20000) });
  } else {
    throw new Error('nothing readable to send');
  }
  parts.push({ text: geminiPrompt_(fileName) });

  const payload = {
    contents: [{ role: 'user', parts: parts }],
    generationConfig: {
      temperature: 0,
      responseMimeType: 'application/json',
      responseSchema: {
        type: 'OBJECT',
        properties: {
          vendor: { type: 'STRING' },
          date: { type: 'STRING', description: 'YYYY-MM-DD, or empty' },
          total: { type: 'NUMBER', nullable: true },
          document_type: { type: 'STRING', enum: ['tax_invoice', 'receipt', 'refund', 'quote', 'statement', 'other'] },
          invoice_number: { type: 'STRING' },
          confidence: { type: 'STRING', enum: ['high', 'medium', 'low'] },
          reason: { type: 'STRING' },
        },
        required: ['vendor', 'date', 'total', 'document_type', 'invoice_number', 'confidence'],
      },
    },
  };

  for (let attempt = 0; attempt < 2; attempt++) {
    const wait = CONFIG.AI_MIN_GAP_MS - (Date.now() - AI_STATE.lastCall);
    if (wait > 0) Utilities.sleep(wait);
    AI_STATE.lastCall = Date.now();
    const resp = UrlFetchApp.fetch(
      'https://generativelanguage.googleapis.com/v1beta/models/' + model + ':generateContent', {
        method: 'post', contentType: 'application/json', payload: JSON.stringify(payload),
        headers: { 'x-goog-api-key': key }, muteHttpExceptions: true,
      });
    const code = resp.getResponseCode();
    if (code === 200) {
      const body = JSON.parse(resp.getContentText());
      const out = body.candidates && body.candidates[0] && body.candidates[0].content &&
        body.candidates[0].content.parts && body.candidates[0].content.parts[0].text;
      if (!out) throw new Error('empty AI answer');
      return JSON.parse(out);
    }
    if (code === 429) {
      if (/per.?day|daily|PerDay/i.test(resp.getContentText()) || attempt === 1) {
        AI_STATE.exhausted = true;
        throw new Error('free daily limit reached');
      }
      Utilities.sleep(30 * 1000); // per-minute limit — wait and retry once
      continue;
    }
    if (code === 404) {
      PropertiesService.getScriptProperties().deleteProperty('GEMINI_RESOLVED_MODEL');
      AI_STATE.model = null;
      throw new Error('model ' + model + ' not available — will auto-pick another next time');
    }
    throw new Error('AI error ' + code + ': ' + resp.getContentText().slice(0, 150));
  }
  throw new Error('AI busy');
}

function geminiPrompt_(fileName) {
  return [
    'This is a purchase document (receipt, tax invoice, refund, quote or statement) for an Australian rental property.',
    'File name: "' + fileName + '".',
    (ownNames_().length ? 'The BUYER/customer is: ' + ownNames_().join('; ') + '. ' : '') +
      'NEVER return the buyer/customer ("Bill to", "Ship to", "Customer") as the vendor —',
    'the vendor is the business that issued the document and was paid (usually its logo/letterhead, ABN, "From").',
    'Return:',
    '- vendor: the business trading name, short (e.g. "Bunnings", "Apex Flooring"); no "Pty Ltd", no branch/suburb.',
    '- date: the issue/purchase/transaction date as YYYY-MM-DD. NOT the due date. Australian dates are day-first.',
    '- total: the final amount charged INCLUDING GST. Not the subtotal, not the GST, not "savings"/"PowerPass savings"/discounts,',
    '  not a deposit, not cash tendered or change. If "Amount due" is $0.00 because it was already paid, use the invoice Total.',
    '  For a refund or credit note return a NEGATIVE number. null if there is no clear total.',
    '- document_type: tax_invoice, receipt, refund, quote (an estimate, not a purchase), statement, or other.',
    '- invoice_number: the invoice/receipt/transaction number exactly as printed, or "".',
    '- confidence: "high" only if vendor, date and total are all clearly printed; otherwise medium/low.',
    '- reason: a few words on anything unclear, or "".',
  ].join('\n');
}

/** Use the configured model; if Google has retired it, pick the newest free "flash-lite" (or "flash"). */
function resolveModel_(key, test) {
  if (AI_STATE.model && !test) return AI_STATE.model;
  const props = PropertiesService.getScriptProperties();
  let model = props.getProperty('GEMINI_RESOLVED_MODEL') || CONFIG.GEMINI_MODEL;

  if (test || !props.getProperty('GEMINI_RESOLVED_MODEL')) {
    const resp = UrlFetchApp.fetch('https://generativelanguage.googleapis.com/v1beta/models?pageSize=200',
      { headers: { 'x-goog-api-key': key }, muteHttpExceptions: true });
    if (resp.getResponseCode() !== 200) {
      throw new Error('Gemini rejected the key (' + resp.getResponseCode() + '): ' + resp.getContentText().slice(0, 150));
    }
    const names = (JSON.parse(resp.getContentText()).models || [])
      .filter(m => (m.supportedGenerationMethods || []).indexOf('generateContent') !== -1)
      .map(m => m.name.replace(/^models\//, ''));
    if (names.indexOf(model) === -1) {
      const usable = names.filter(n => /^gemini-[\d.]+-flash/.test(n) && !/(preview|exp|tts|image|live|audio|thinking)/.test(n));
      const ver = n => parseFloat((n.match(/gemini-([\d.]+)/) || [0, 0])[1]);
      usable.sort((a, b) => (/lite/.test(b) - /lite/.test(a)) || ver(b) - ver(a));
      if (!usable.length) throw new Error('no free Gemini Flash model found for this key');
      model = usable[0];
    }
    props.setProperty('GEMINI_RESOLVED_MODEL', model);
  }
  AI_STATE.model = model;
  return model;
}

// ============================ READING FILES ============================

/** An image/PDF blob that OCR and Gemini can read, or null for Google Docs/Sheets/text. */
function readableBlob_(file) {
  const mime = file.getMimeType();
  if (mime === MimeType.GOOGLE_DOCS || mime === MimeType.GOOGLE_SHEETS || mime.indexOf('text/') === 0) return null;
  if (OCR_MIME_TYPES.indexOf(mime) !== -1 || AI_MIME_TYPES.indexOf(mime) !== -1) return file.getBlob();
  if (mime.indexOf('image/') === 0) return largePreviewJpeg_(file.getId());
  throw new Error('unsupported file type ' + mime);
}

/** Text of a file, using Drive's free OCR for PDFs and photos. */
function extractText_(file, blob) {
  const mime = file.getMimeType();
  if (mime === MimeType.GOOGLE_DOCS) return DocumentApp.openById(file.getId()).getBody().getText();
  if (mime === MimeType.GOOGLE_SHEETS) return sheetText_(file.getId());
  if (mime.indexOf('text/') === 0) return file.getBlob().getDataAsString();
  if (!blob) return '';

  // Drive OCR can't take HEIC directly; use a JPEG preview for it.
  let ocrBlob = blob;
  if (OCR_MIME_TYPES.indexOf(blob.getContentType()) === -1) ocrBlob = largePreviewJpeg_(file.getId());

  const doc = Drive.Files.create(
    { name: '[tmp OCR] ' + file.getName(), mimeType: MimeType.GOOGLE_DOCS },
    ocrBlob,
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

// ============================ OCR-ONLY PARSER (pure functions) ============================
// Used when Gemini isn't available, and as a cross-check. No Google services
// here, so these can be tested outside Apps Script.

// Amount, allowing "-$22.78", "$-22.78", "1,234.56".
const MONEY_RE = /(-?)\$?\s?(-?)((?:\d{1,3}(?:,\d{3})+|\d+)\.\d{2})(?!\d)/g;

// Ordered strongest first. "Amount due" beats a bare "Total".
const TOTAL_PATTERNS = [
  { re: /\b(balance|amount|total)\s+(due|payable|owing)\b/i, weight: 6 },
  { re: /\bgrand\s+total\b/i, weight: 6 },
  { re: /\binvoice\s+total\b/i, weight: 6 },
  { re: /\btotal\s*(\(?\s*inc(l(uding|\.)?)?\.?\s*gst\s*\)?)/i, weight: 5 },
  { re: /\btotal\s+(aud|amount|price|payable|sale|paid)\b/i, weight: 5 },
  { re: /\b(amount\s+paid|refund\s+total|total\s+refund)\b/i, weight: 4 },
  { re: /\btotal\b/i, weight: 3 },
  { re: /\b(eftpos|visa|mastercard|amex|credit|debit|card)\b/i, weight: 1 },
];

// Lines that mention "total" but aren't the amount spent.
const NOT_TOTAL_RE = /(sub[\s-]?total|total\s+(gst|tax|items?|qty|quantity|excl?\.?|ex\s+gst)|\bgst\b|\btax\b|savings?|saved|you\s+save|powerpass|discount|\bdisc\b|change|rounding|cash\s+out|tendered|points|deposit|previous|less\s+amount\s+paid)/i;

function parseReceipt(text, opts) {
  opts = opts || {};
  const lines = String(text || '').split(/\r?\n/).map(l => l.trim()).filter(Boolean);
  const issues = [];
  const isRefund = /\brefund|credit\s+note|returns?\b.*\b(refund|credit)/i.test(text || '') || /\$\s?-\d/.test(opts.fileName || '');

  // ---- Total ----
  const fileAmounts = amountsInText_(opts.fileName || '');
  const tr = findTotal_(lines);
  let total = null;
  const fileAmt = fileAmounts.length === 1 ? fileAmounts[0] : null;
  if (fileAmt !== null && tr.allAmounts.some(a => Math.abs(Math.abs(a) - Math.abs(fileAmt)) < 0.005)) {
    // The file name carries the amount (e.g. Bunnings digital receipts) and
    // it's printed in the document too — the strongest signal there is.
    total = fileAmt;
    if (tr.confident && Math.abs(Math.abs(tr.amount) - Math.abs(fileAmt)) >= 0.005) {
      issues.push('File name says ' + fmtMoney_(fileAmt) + ' but the receipt total reads ' + fmtMoney_(tr.amount) + ' — please check.');
      total = null;
    }
  } else if (tr.confident) {
    total = tr.amount;
    if (tr.conflict) issues.push(tr.conflict);
  } else {
    issues.push('Total not confidently read' +
      (tr.candidates.length ? ' — possible: ' + tr.candidates.map(fmtMoney_).join(', ') : '') + '.');
  }
  if (total !== null && isRefund && total > 0) total = -total;

  // ---- Date ----
  const date = findDate_(lines, opts.dateOrder || 'DMY', opts.today || new Date());
  if (!date) issues.push('Date not found.');

  // ---- Vendor ----
  const v = findVendor_(lines, opts.knownVendors || {}, opts.fileName || '', opts.ownNames || []);
  if (!v.vendor) issues.push('Vendor not found.');
  else if (!v.confident) issues.push('Vendor is a best guess.');

  return { date: date, vendor: v.vendor, total: total, issues: issues };
}

function amountsInText_(s) {
  const out = [];
  let m;
  const re = new RegExp(MONEY_RE.source, 'g');
  while ((m = re.exec(String(s || ''))) !== null) {
    const v = Math.round(parseFloat(m[3].replace(/,/g, '')) * 100) / 100;
    if (!isNaN(v)) out.push(m[1] === '-' || m[2] === '-' ? -v : v);
  }
  return out;
}

function findTotal_(lines) {
  const hits = []; // {amount, weight}
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const strong = /\b(amount|balance)\s+(due|payable)|grand\s+total|total\s*\(?inc/i.test(line);
    if (NOT_TOTAL_RE.test(line) && !strong) continue;
    const pat = TOTAL_PATTERNS.find(p => p.re.test(line));
    if (!pat) continue;

    // Amount on the same line, else on the next line or two (OCR often splits
    // label and number onto separate lines).
    let amts = amountsIn_(line);
    for (let k = 1; !amts.length && k <= 2 && i + k < lines.length; k++) {
      if (NOT_TOTAL_RE.test(lines[i + k])) break;
      amts = amountsIn_(lines[i + k]);
    }
    amts = amts.filter(a => a !== 0);
    if (amts.length) hits.push({ amount: amts[amts.length - 1], weight: pat.weight });
  }

  const allAmounts = uniq_(lines.reduce((acc, l) => acc.concat(amountsIn_(l)), []).filter(a => a !== 0));
  const topCandidates = allAmounts.slice().sort((a, b) => Math.abs(b) - Math.abs(a)).slice(0, 3);
  const res = { confident: false, candidates: topCandidates, allAmounts: allAmounts };
  if (!hits.length) return res;

  const best = Math.max.apply(null, hits.map(h => h.weight));
  const bestAmounts = uniq_(hits.filter(h => h.weight === best).map(h => h.amount));
  if (best <= 1) { res.candidates = uniq_(bestAmounts.concat(topCandidates)).slice(0, 3); return res; }
  if (bestAmounts.length > 1) { res.candidates = bestAmounts.sort((a, b) => b - a).slice(0, 3); return res; }

  res.confident = true;
  res.amount = bestAmounts[0];
  res.candidates = [res.amount];
  const strongerOther = hits.find(h => h.weight >= 3 && Math.abs(h.amount) > Math.abs(res.amount) * 1.01);
  if (strongerOther) res.conflict = 'Another total-like amount found (' + fmtMoney_(strongerOther.amount) + ') — please check.';
  return res;
}

function amountsIn_(line) { return amountsInText_(line); }

const MONTHS = { jan: 1, feb: 2, mar: 3, apr: 4, may: 5, jun: 6, jul: 7, aug: 8, sep: 9, oct: 10, nov: 11, dec: 12 };

function datesInLine_(line, order) {
  const found = []; // {y, m, d, index}
  let m;
  const iso = /\b(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})\b/g;
  while ((m = iso.exec(line))) found.push({ y: +m[1], m: +m[2], d: +m[3], index: m.index });
  const num = /\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{4}|\d{2})\b/g;
  while ((m = num.exec(line))) {
    if (order === 'MDY') found.push({ y: +m[3], m: +m[1], d: +m[2], index: m.index });
    else found.push({ y: +m[3], m: +m[2], d: +m[1], index: m.index });
  }
  const dmy = /\b(\d{1,2})(?:st|nd|rd|th)?[\s\-.]+([A-Za-z]{3,9})\.?,?[\s\-.]+(\d{4}|\d{2})\b/g;
  while ((m = dmy.exec(line))) {
    const mo = MONTHS[m[2].toLowerCase().slice(0, 3)];
    if (mo) found.push({ y: +m[3], m: mo, d: +m[1], index: m.index });
  }
  const mdy = /\b([A-Za-z]{3,9})\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b/g;
  while ((m = mdy.exec(line))) {
    const mo = MONTHS[m[1].toLowerCase().slice(0, 3)];
    if (mo) found.push({ y: +m[3], m: mo, d: +m[2], index: m.index });
  }
  return found.sort((a, b) => a.index - b.index);
}

function findDate_(lines, order, today) {
  const candidates = []; // {date, weight}
  const maxAgeMs = 5 * 365 * 24 * 3600 * 1000;
  const toDate = f => {
    let y = f.y < 100 ? f.y + 2000 : f.y;
    if (f.m < 1 || f.m > 12 || f.d < 1 || f.d > 31) return null;
    const dt = new Date(y, f.m - 1, f.d);
    if (dt.getMonth() !== f.m - 1) return null;
    if (dt.getTime() > today.getTime() + 24 * 3600 * 1000) return null;
    if (today.getTime() - dt.getTime() > maxAgeMs) return null;
    return dt;
  };

  lines.forEach((line, i) => {
    const found = datesInLine_(line, order);
    if (!found.length) return;

    // Invoice layouts often put labels on one line and values on the next:
    //   "Amount due   Due date     Issue date    Invoice number"
    //   "$0.00        2 Nov 2026   26 Oct 2026   INV-2026225"
    const prev = (lines[i - 1] || '').toLowerCase();
    const labels = [];
    const labelRe = /(due\s+date|issue\s+date|invoice\s+date|date\s+issued|transaction\s+date|purchase\s+date|order\s+date)/g;
    let lm;
    while ((lm = labelRe.exec(prev))) labels.push(lm[1]);
    if (labels.length >= 2 && found.length === labels.length) {
      found.forEach((f, k) => {
        const dt = toDate(f);
        if (dt) candidates.push({ date: dt, weight: /due/.test(labels[k]) ? 0 : 4 });
      });
      return;
    }

    found.forEach(f => {
      const dt = toDate(f);
      if (!dt) return;
      let weight = 1;
      if (/\b(invoice|issue|transaction|purchase|txn|receipt|order)\s*date\b|\bdate\s*(issued|of\s+issue)?\s*:/i.test(line)) weight = 3;
      if (/\b(due|expir|valid|exp\.?|pay\s+by)\b/i.test(line) || /\bdue\b/.test(prev) && !/issue|invoice/.test(prev)) weight = 0;
      candidates.push({ date: dt, weight: weight });
    });
  });

  const usable = candidates.filter(c => c.weight > 0);
  if (!usable.length) return null;
  usable.sort((a, b) => b.weight - a.weight);
  return usable[0].date;
}

const NOT_VENDOR_RE = /^(tax\s+invoice|invoice|receipt|tax\s+receipt|sales\s+receipt|digital\s+receipt|customer\s+copy|merchant\s+copy|statement|quote|quotation|order|welcome|thank|abn|acn|ph|phone|tel|fax|email|www\.|http|date|time|page|bill\s+to|ship\s+to|sold\s+to|deliver\s+to|customer|to:|from:|\*|\d)/i;

function findVendor_(lines, knownVendors, fileName, ownNames) {
  const own = (ownNames || []).map(n => n.toLowerCase());
  const isOwn = l => own.some(n => l.toLowerCase().indexOf(n) !== -1);

  const haystack = (lines.slice(0, 40).join('\n') + '\n' + fileName).toLowerCase();
  const keys = Object.keys(knownVendors).sort((a, b) => b.length - a.length);
  for (const k of keys) {
    if (haystack.indexOf(k.toLowerCase()) !== -1) return { vendor: knownVendors[k], confident: true };
  }

  // Skip the customer block ("Bill to" / "Ship to" and the 3 lines after it).
  const skip = new Set();
  lines.forEach((l, i) => {
    if (/\b(bill|ship|sold|deliver|invoice)\s+to\b|^customer\b|^to\b:?/i.test(l)) for (let k = 0; k <= 3; k++) skip.add(i + k);
  });
  const candidatesAt = n => lines.slice(0, n).map((l, i) => ({ l: l, i: i })).filter(x => !skip.has(x.i) && !isOwn(x.l));

  for (const { l } of candidatesAt(25)) {
    const m = l.match(/^([A-Za-z0-9&'.,\- ]{2,60}?\b(pty\.?\s*ltd|pty|ltd|limited|group|plumbing|electrical|builders?|constructions?|services|trades?|hardware|supplies|landscaping|roofing|painting|carpentry|flooring|tiles?|kitchens?|glass|blinds|fencing))\b/i);
    if (m && !NOT_VENDOR_RE.test(l)) return { vendor: tidy_(m[1].replace(/\b(pty\.?\s*ltd|pty|ltd|limited)\b/ig, '')), confident: false };
  }
  for (const { l } of candidatesAt(8)) {
    if (NOT_VENDOR_RE.test(l)) continue;
    const letters = (l.match(/[A-Za-z]/g) || []).length;
    if (letters < 3 || letters / l.length < 0.5) continue;
    if (/\b(street|st\.?|road|rd\.?|ave|avenue|drive|dr\.?|nsw|vic|qld|wa|sa|tas|act|nt)\b\s*\d{0,4}$/i.test(l)) continue;
    return { vendor: tidy_(l).slice(0, 60), confident: false };
  }
  return { vendor: '', confident: false };
}

function tidy_(s) {
  s = s.replace(/\s+/g, ' ').trim().replace(/[,.\-]+$/, '').trim();
  if (s === s.toUpperCase()) s = s.toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
  return s;
}

function uniq_(arr) { return arr.filter((v, i) => arr.indexOf(v) === i); }
function fmtMoney_(n) { return (n < 0 ? '-$' : '$') + Math.abs(n).toFixed(2); }

// ============================ SHEET ============================

function getOrCreateSheet_() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(CONFIG.SHEET_NAME);
  if (!sheet) sheet = ss.insertSheet(CONFIG.SHEET_NAME);
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
  for (let i = colA.length - 1; i >= 0; i--) if (colA[i][0] === TOTAL_LABEL) return i + 2;
  return 0;
}

/** Makes sure exactly one TOTAL row exists at the bottom, summing everything above it. */
function ensureTotalRow_(sheet) {
  let r = findTotalRow_(sheet);
  if (!r) {
    r = Math.max(sheet.getLastRow(), 1) + 1;
    sheet.getRange(r, COL.DATE).setValue(TOTAL_LABEL);
  } else if (r !== sheet.getLastRow()) {
    sheet.getRange(r, 1, 1, HEADERS.length).clearContent().clearFormat();
    r = sheet.getLastRow() + 1;
    sheet.getRange(r, COL.DATE).setValue(TOTAL_LABEL);
  }
  sheet.getRange(r, COL.TOTAL).setFormula('=SUM(INDIRECT("C2:C"&ROW()-1))').setNumberFormat('$#,##0.00;-$#,##0.00');
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
  return r;
}

function writeRow_(sheet, r, row) {
  const link = SpreadsheetApp.newRichTextValue().setText(row.fileName).setLinkUrl(row.url).build();
  sheet.getRange(r, COL.DATE).setValue(row.date || '').setNumberFormat('dd/mm/yyyy');
  sheet.getRange(r, COL.VENDOR).setValue(row.vendor || '');
  sheet.getRange(r, COL.TOTAL).setValue(row.total === null ? '' : row.total).setNumberFormat('$#,##0.00;-$#,##0.00');
  sheet.getRange(r, COL.LINK).setRichTextValue(link);
  sheet.getRange(r, COL.STATUS).setValue(row.status);
  sheet.getRange(r, COL.NOTES).setValue(row.notes || '');
  sheet.getRange(r, COL.FILE_ID).setValue(row.fileId);
  saveMeta_(row.fileId, { inv: row.invoiceNo || '', md5: row.md5 || '' });
}

// Invoice numbers and file fingerprints are kept out of sight (for duplicate checks).
function saveMeta_(fileId, meta) {
  try { PropertiesService.getDocumentProperties().setProperty('m_' + fileId, JSON.stringify(meta)); } catch (e) { /* ok */ }
}

function toCtxRow_(r, row) {
  return { row: r, fileId: row.fileId, date: row.date, vendor: row.vendor, total: row.total,
    notes: row.notes || '', invoiceNo: row.invoiceNo || '', md5: row.md5 || '' };
}

function addToContext_(ctx, r, row) {
  const c = toCtxRow_(r, row);
  ctx.rows.push(c);
  ctx.byFileId[row.fileId] = c;
}

/** Every row in the sheet that came from a file, with its stored invoice no./fingerprint. */
function loadRows_(sheet) {
  const ctx = { rows: [], byFileId: {} };
  const last = sheet.getLastRow();
  if (last < 2) return ctx;
  const values = sheet.getRange(2, 1, last - 1, HEADERS.length).getValues();
  const meta = PropertiesService.getDocumentProperties().getProperties();
  values.forEach((v, i) => {
    const fileId = String(v[COL.FILE_ID - 1] || '');
    if (!fileId) return;
    let m = {};
    try { m = JSON.parse(meta['m_' + fileId] || '{}'); } catch (e) { /* ok */ }
    const c = {
      row: i + 2, fileId: fileId,
      date: v[COL.DATE - 1] instanceof Date ? v[COL.DATE - 1] : null,
      vendor: String(v[COL.VENDOR - 1] || ''),
      total: typeof v[COL.TOTAL - 1] === 'number' ? v[COL.TOTAL - 1] : null,
      notes: String(v[COL.NOTES - 1] || ''),
      invoiceNo: m.inv || '', md5: m.md5 || '',
    };
    ctx.rows.push(c);
    ctx.byFileId[fileId] = c;
  });
  return ctx;
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
if (typeof module !== 'undefined') module.exports = { parseReceipt, findDuplicate_ };
