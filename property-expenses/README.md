# Property Expense Tracker (Google Sheets + Drive)

Once a week this reads every new receipt or invoice in a Google Drive folder and adds a row to a Google Sheet:

| Date | Vendor | Total | Receipt | Status | Notes |
|---|---|---|---|---|---|
| 12/10/2026 | Bunnings | $101.48 | *link to file* | OK | |
| 03/10/2026 | Smith Plumbing | $2,200.00 | *link to file* | CHECK | Vendor is a best guess. |
| | | | *link to file* | CHECK | Total not confidently read — possible: $520.00, $450.00 |
| **TOTAL** | | **$2,301.48** | | 1 to check | |

- **Free.** Google Gemini (free tier) reads each receipt. Google Drive's built-in OCR double-checks it. No paid APIs.
- **Checked, not trusted.** Gemini's total is only accepted if that exact amount is actually printed in the document (or in the file name, as on Bunnings digital receipts). Anything else is flagged.
- **Never counts doubtful numbers.** Uncertain totals stay blank, the row turns orange, and the reason is in Notes.
- **Never double-counts.** Duplicates are flagged and left out of the TOTAL: the same file uploaded twice, the same invoice number, or the same vendor, date and amount.
- **Handles refunds and quotes.** Refunds come out negative. Quotes aren't counted.
- **Reads** PDFs, phone photos (JPG, PNG, HEIC), Google Docs and Sheets, and text files. Subfolders are included.
- **Emails you** after each sync, listing the rows that need checking first.
- **TOTAL row** stays at the bottom and sums everything above it, including rows you add by hand.

## Updating from an earlier version

1. Open the Sheet → **Extensions → Apps Script**.
2. In `Code.gs`, select all and delete, then paste the new `Code.gs`. **Put your folder ID back into `FOLDER_ID`.**
3. Save, go back to the Sheet and refresh it.
4. Do steps A–C under "After setup" below.

## Setup (about 5 minutes)

1. Create a new Google Sheet, e.g. "Property expenses".
2. Go to **Extensions → Apps Script**.
3. Replace the contents of `Code.gs` with this folder's `Code.gs`.
4. Click **Project Settings** (gear icon) and tick **Show "appsscript.json" manifest file in editor**. Go back to the Editor and replace `appsscript.json` with this folder's version. This turns on the Drive service that does the OCR.
5. In `Code.gs`, set `FOLDER_ID` to your receipts folder's ID. That's the last part of the folder URL: `https://drive.google.com/drive/folders/`**`1AbC...xyz`**
6. Save, then reload the Sheet. A **Receipts** menu appears.
7. Click **Receipts → Sync now**. Approve the permissions prompt the first time. Google will warn that the app is unverified, because it's your own script: click **Advanced → Go to project**.
8. Click **Receipts → Turn on weekly run + Sync checkbox**. It runs Mondays around 7am (change with `WEEKLY_DAY` / `WEEKLY_HOUR`) and switches on the **Sync now** checkbox at the top right of the sheet (cell I1).

## After setup: three one-time steps

**A. Tell it who you are (1 minute).** Click **Receipts → Set my name(s)** and type the names, company and street that appear under "Bill to" on your invoices, separated by commas. This stops your own name being picked as the vendor. It's stored privately with the script, not in the code.

**B. Turn on the free AI reader (3 minutes, recommended).** Without it the script uses OCR only and flags many more rows.
1. Signed in as the account that owns the Sheet, go to **https://aistudio.google.com/apikey**.
2. Accept the terms if asked, then click **Create API key**. Let it create a new project. **Never add billing** to that project; the free tier only stays free while there is no billing account.
3. Copy the key (it starts with `AIza`).
4. In the Sheet, click **Receipts → Set up free AI (Gemini) key**, paste the key and click OK. You should see "Key works".

**C. Fix existing rows.** Click **Receipts → Re-read ALL rows**. Big sheets continue automatically every minute until done.

**Privacy:** on Google's free tier, Google may use what you send to improve its products, and that can include people reviewing it. Your receipts show your name, address and phone number. If that's not acceptable, skip step B and the script uses OCR only.

**Free limits:** the free tier allows a few hundred receipts a day. If the limit is reached, rows are read with OCR only, tagged `[AI pending]`, and re-read with AI automatically on the next sync.

## Day-to-day

- Drop receipts into the folder. They're picked up on the next weekly run.
- **Need it now?** Tick the **Sync now** checkbox (cell I1). It works in the Google Sheets phone app too, where the Receipts menu doesn't show. It unticks itself when done, and the cell next to it shows when it last synced and what it added. On a computer, **Receipts → Sync now** does the same thing.
- For an orange **CHECK** row: open the link, fix or fill in Date, Vendor and Total, then set Status to **OK**.
- If you replace a blurry photo with a better one, select the row and click **Receipts → Re-read selected row(s)**.
- **A row says DUPLICATE:** it isn't counted. If it really is a separate purchase, type the amount into Total and set Status to OK.
- **Optional:** add shops to `KNOWN_VENDORS` in `Code.gs` so they always get the same name (e.g. "Bunnings Warehouse Belconnen" becomes "Bunnings").
- Manual rows can go anywhere above TOTAL. Leave column G blank for them.

## Known limits

- **An invoice plus a separate payment receipt for the same job** can still appear as two rows if they have different numbers and dates. Keep only one of them in the folder.
- **Badly lit or crumpled photos** may OCR poorly. These come up as CHECK, not wrong numbers.
- **Dates are read day-first** (Australian format). Change `DATE_ORDER` to `'MDY'` for US-style receipts.
- **Large batches:** each run stops after about 4.5 minutes (Google's time limit), then carries on automatically a minute later until every file is in.
