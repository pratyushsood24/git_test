# Property Expense Tracker (Google Sheets + Drive)

Once a week this reads every new receipt or invoice in a Google Drive folder and adds a row to a Google Sheet:

| Date | Vendor | Total | Receipt | Status | Notes |
|---|---|---|---|---|---|
| 12/10/2026 | Bunnings | $101.48 | *link to file* | OK | |
| 03/10/2026 | Smith Plumbing | $2,200.00 | *link to file* | CHECK | Vendor is a best guess. |
| | | | *link to file* | CHECK | Total not confidently read — possible: $520.00, $450.00 |
| **TOTAL** | | **$2,301.48** | | 1 to check | |

- **Free.** Uses Google Drive's built-in OCR. No paid APIs.
- **Reads** PDFs, phone photos (JPG, PNG, and iPhone HEIC via Drive's preview), Google Docs/Sheets, and text files. Subfolders are included.
- **Never guesses a total.** If it isn't confident, the Total cell stays blank, the row is highlighted orange, and the possible amounts are listed in Notes.
- **Emails you** after each run, listing the rows that need checking first.
- **Never adds a file twice.** It keeps track of each file it has processed (hidden column G), so your manual edits are never overwritten.
- **TOTAL row** stays at the bottom and sums everything above it, including rows you add by hand.

## Setup (about 5 minutes)

1. Create a new Google Sheet, e.g. "Property expenses".
2. Go to **Extensions → Apps Script**.
3. Replace the contents of `Code.gs` with this folder's `Code.gs`.
4. Click **Project Settings** (gear icon) and tick **Show "appsscript.json" manifest file in editor**. Go back to the Editor and replace `appsscript.json` with this folder's version. This turns on the Drive service that does the OCR.
5. In `Code.gs`, set `FOLDER_ID` to your receipts folder's ID. That's the last part of the folder URL: `https://drive.google.com/drive/folders/`**`1AbC...xyz`**
6. Save, then reload the Sheet. A **Receipts** menu appears.
7. Click **Receipts → Process new receipts now**. Approve the permissions prompt the first time. Google will warn that the app is unverified, because it's your own script: click **Advanced → Go to project**.
8. Click **Receipts → Turn on weekly automatic run**. It runs Mondays around 7am. You can change this with `WEEKLY_DAY` and `WEEKLY_HOUR`.

## Day-to-day

- Drop receipts into the folder. They're picked up on the next weekly run, or straight away with **Process new receipts now**.
- For an orange **CHECK** row: open the link, fix or fill in Date, Vendor and Total, then set Status to **OK**.
- If you replace a blurry photo with a better one, select the row and click **Receipts → Re-read selected row(s)**.
- Add regular suppliers and tradies to `KNOWN_VENDORS` in `Code.gs`. Their names are then picked up reliably instead of flagged as a "best guess".
- Manual rows can go anywhere above TOTAL. Leave column G blank for them.

## Known limits

- **Two documents for one purchase get counted twice.** For example, a tradie's invoice plus a separate payment receipt. The script can't tell they're the same job. Keep only one in the folder, or delete one row.
- **Badly lit or crumpled photos** may OCR poorly. These come up as CHECK, not wrong numbers.
- **Dates are read day-first** (Australian format). Change `DATE_ORDER` to `'MDY'` for US-style receipts.
- **Large first batch:** each run stops after about 4.5 minutes to stay under Google's time limit. With a big backlog, click "Process now" a few times.
