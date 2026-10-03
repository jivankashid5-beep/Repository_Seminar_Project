# Driver Billing System

A beginner-friendly billing app made with Flask, SQLite, HTML, CSS, and JavaScript.

## Requirements

- Python installed on your computer
- Google Chrome (recommended for voice input)
- Internet connection for browser speech recognition

## Setup and run

Open PowerShell or a terminal in the `driver_billing` project folder, then run:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

If PowerShell blocks virtual-environment activation, you can use the Python executable directly instead:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```

When Flask says it is running, open <http://127.0.0.1:5000> in your browser. Leave the terminal open while using the app. Press `Ctrl+C` in that terminal to stop it.

## Using the app

1. Enter customer, date, vehicle number, balance, and at least one complete description/amount row.
2. The total and amount in words update as row amounts change.
3. Select **Save Bill**. The app assigns a challan number and opens the saved bill.
4. Use **Saved bills** to search, view, or edit earlier bills.
5. On a bill preview, choose **Full bill** to print the designed bill, or **Values only** to print values on pre-printed bill paper. Select **Print** to open the browser print dialog.

## Voice input (Chrome)

On the new/edit bill form, select **English (India)** or **Hindi (India)**, allow microphone access, and click the main microphone. Speak a line in this format:

> Dhoot Transmission, Yazaki to Dhoot, 2200

The recognized words appear in an editable box. Correct the text if needed and click **Apply line to fields**. A microphone beside an individual field fills only that field. Number words are sent to the Flask `/api/words-to-number` route and converted by `parser.py`.

Voice recognition can require an internet connection. Use the app at the local address above rather than opening an HTML file directly. If recognition does not start, check Chrome's site microphone permission and your Windows microphone privacy/device settings.

## Adjusting pre-printed paper alignment

In `config.py`, edit `PREPRINTED_OFFSETS_MM`. Positions are in millimetres from the top-left of an A5 portrait page:

- Increase an `x` value to move that value right; decrease it to move left.
- Increase a `y` value to move it down; decrease it to move up.
- `rows.line_spacing` changes the vertical gap between printed item rows.

Print a values-only test on plain paper first. In the print dialog, choose A5 portrait, 100% scale, and turn off browser headers and footers. Compare the test sheet with the pre-printed form, adjust the relevant values, and test again. Printer feed and margins vary, so small iterative adjustments are expected.

## Run the built-in checks

From the project folder:

```powershell
python parser.py
python database.py
```

The database checks use a temporary database and do not overwrite your saved bills.

## Project files

- `app.py` — Flask pages, form validation, and number-conversion API
- `database.py` — SQLite schema and bill storage/search functions
- `parser.py` — number/date helpers and parser checks
- `config.py` — business header, database name, and print alignment settings
- `templates/` — bill-entry, bill-preview, and saved-bills pages
- `static/` — browser interactions and page/print styles
- `driver_billing.db` — SQLite data file, created when the app initializes
