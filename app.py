"""Flask routes for entering, saving, editing, and viewing bills."""

import math
import re
import sqlite3
from datetime import date

from flask import Flask, jsonify, redirect, render_template, request, url_for

from config import (
    BANK_DETAILS,
    BILL_FOOTER_BUSINESS,
    BILL_FOOTER_MESSAGE,
    BILL_TITLE,
    BUSINESS_ADDRESS,
    BUSINESS_NAME,
    BUSINESS_SUBTITLE,
    DEFAULT_PRINT_MODE,
    PREPRINTED_OFFSETS_MM,
)
from database import (
    get_bill,
    get_next_challan_no,
    init_db,
    list_bills,
    save_bill as save_bill_to_db,
    search_bills as search_database,
    update_bill as update_bill_in_db,
)
from parser import amount_in_words, calculate_total, format_date, words_to_number

app = Flask(__name__)

# Create the tables when the Flask app starts.
init_db()


def _header_details():
    """Return the fixed business details used in bill pages."""
    return {
        "bill_title": BILL_TITLE,
        "business_name": BUSINESS_NAME,
        "business_subtitle": BUSINESS_SUBTITLE,
        "business_address": BUSINESS_ADDRESS,
        "bank_details": BANK_DETAILS,
        "footer_message": BILL_FOOTER_MESSAGE,
        "footer_business": BILL_FOOTER_BUSINESS,
    }


def _render_entry_form(bill=None, editing=False, error=None):
    """Render the same form for a new bill or an existing bill being edited."""
    bill = bill or {}
    action = (
        url_for("edit_bill", challan_no=bill["challan_no"])
        if editing
        else url_for("save_bill")
    )
    return render_template(
        "index.html",
        bill=bill,
        editing=editing,
        form_action=action,
        next_challan_no=bill.get("challan_no", get_next_challan_no()),
        today=date.today().isoformat(),
        amount_words=amount_in_words(bill.get("total", 0)),
        error=error,
        **_header_details(),
    )


def _bill_data_from_form():
    """Validate submitted bill fields and calculate the total on the server."""
    customer_name = request.form.get("customer_name", "").strip()
    vehicle_no = request.form.get("vehicle_no", "").strip()
    bill_date = request.form.get("date", "").strip()

    if not customer_name:
        raise ValueError("Customer name is required.")
    if not vehicle_no:
        raise ValueError("Vehicle number is required.")
    if not bill_date:
        raise ValueError("Date is required.")

    # The amount and description inputs are sent as parallel lists.
    descriptions = request.form.getlist("descriptions[]")
    amounts = request.form.getlist("amounts[]")
    if len(descriptions) != len(amounts):
        raise ValueError("Each bill row must have both a description and an amount.")

    bill_rows = []
    for row_number, (description, amount_text) in enumerate(zip(descriptions, amounts), start=1):
        description = description.strip()
        amount_text = amount_text.strip()
        if not description and not amount_text:
            continue
        if not description:
            raise ValueError(f"Description is required for row {row_number}.")
        if not amount_text:
            raise ValueError(f"Amount is required for row {row_number}.")

        try:
            amount = float(amount_text)
        except ValueError as error:
            raise ValueError(f"Amount in row {row_number} must be a number.") from error
        if not math.isfinite(amount):
            raise ValueError(f"Amount in row {row_number} must be a valid finite number.")
        if amount < 0:
            raise ValueError(f"Amount in row {row_number} cannot be negative.")

        amount = round(amount, 2)
        bill_rows.append({"description": description, "amount": amount})

    if not bill_rows:
        raise ValueError("Add at least one bill row with a description and amount.")

    try:
        balance = float(request.form.get("balance", "").strip())
    except ValueError as error:
        raise ValueError("Balance must be a number. Enter 0 if there is no balance.") from error
    if not math.isfinite(balance):
        raise ValueError("Balance must be a valid finite number.")
    if balance < 0:
        raise ValueError("Balance cannot be negative.")
    balance = round(balance, 2)

    # Validate the date with the shared parser helper before saving it.
    try:
        format_date(bill_date)
    except ValueError as error:
        raise ValueError("Enter a valid date.") from error

    total = round(calculate_total(bill_rows), 2)
    if not math.isfinite(total):
        raise ValueError("The bill total is too large to calculate safely.")

    return {
        "date": bill_date,
        "customer_name": customer_name,
        "vehicle_no": vehicle_no,
        "total": total,
        "balance": balance,
        "rows": bill_rows,
    }


def _submitted_bill_for_retry(challan_no=None):
    """Keep typed values visible when validation fails and the form is shown again."""
    descriptions = request.form.getlist("descriptions[]")
    amounts = request.form.getlist("amounts[]")
    row_count = max(len(descriptions), len(amounts))
    rows = []
    for index in range(row_count):
        rows.append(
            {
                "description": descriptions[index] if index < len(descriptions) else "",
                "amount": amounts[index] if index < len(amounts) else "",
            }
        )

    bill = {
        "date": request.form.get("date", ""),
        "customer_name": request.form.get("customer_name", ""),
        "vehicle_no": request.form.get("vehicle_no", ""),
        "balance": request.form.get("balance", ""),
        "total": 0,
        "rows": rows,
    }
    if challan_no is not None:
        bill["challan_no"] = challan_no
    return bill


def _format_bill_dates(bills):
    """Add a display-friendly date to each bill summary."""
    for bill in bills:
        bill["display_date"] = format_date(bill["date"])
    return bills


@app.route("/")
def home():
    """Show the form for entering a new bill."""
    return _render_entry_form()


@app.route("/api/words-to-number", methods=["POST"])
def convert_spoken_number():
    """Convert a spoken number phrase with the shared Python parser."""
    data = request.get_json(silent=True) or {}
    spoken_text = str(data.get("text", "")).strip()
    if not spoken_text:
        return jsonify({"error": "Please provide a number to convert."}), 400

    try:
        # Ignore a spoken currency suffix while parsing the number itself.
        number_text = re.sub(
            r"\s+(rupees?|rs\.?|रुपये|रुपया|रुपए)$",
            "",
            spoken_text,
            flags=re.IGNORECASE,
        ).strip()
        number = words_to_number(number_text or spoken_text)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    return jsonify({"number": number})


@app.route("/save", methods=["POST"])
def save_bill():
    """Save a new bill and open its preview page."""
    try:
        bill_data = _bill_data_from_form()
        challan_no = save_bill_to_db(bill_data)
    except ValueError as error:
        return _render_entry_form(
            bill=_submitted_bill_for_retry(), error=str(error)
        ), 400
    except sqlite3.Error:
        app.logger.exception("Could not save the new bill.")
        return _render_entry_form(
            bill=_submitted_bill_for_retry(),
            error="The bill could not be saved because of a database error. Please try again.",
        ), 500

    return redirect(url_for("view_bill", challan_no=challan_no))


@app.route("/bills")
def bills_page():
    """Show all saved bills."""
    return render_template(
        "bills_list.html",
        bills=_format_bill_dates(list_bills()),
        search_query="",
        **_header_details(),
    )


@app.route("/search")
def search_bills_page():
    """Search saved bills by challan number or customer name."""
    query = request.args.get("q", "").strip()
    bills = search_database(query) if query else list_bills()
    return render_template(
        "bills_list.html",
        bills=_format_bill_dates(bills),
        search_query=query,
        **_header_details(),
    )


@app.route("/bill/<int:challan_no>")
def view_bill(challan_no):
    """Display a saved bill for viewing or printing."""
    bill = get_bill(challan_no)
    if bill is None:
        return "Bill not found", 404

    selected_print_mode = request.args.get("mode", DEFAULT_PRINT_MODE)
    if selected_print_mode not in {"full", "values"}:
        selected_print_mode = DEFAULT_PRINT_MODE

    row_positions = []
    for index, row in enumerate(bill["rows"]):
        row_positions.append(
            {
                "sr_no": index + 1,
                "description": row["description"],
                "amount": f"{row['amount']:.2f}",
                "y": PREPRINTED_OFFSETS_MM["rows"]["start_y"]
                + index * PREPRINTED_OFFSETS_MM["rows"]["line_spacing"],
            }
        )

    return render_template(
        "bill.html",
        bill=bill,
        display_date=format_date(bill["date"]),
        amount_words=amount_in_words(bill["total"]),
        print_mode=selected_print_mode,
        print_offsets=PREPRINTED_OFFSETS_MM,
        preprinted_rows=row_positions,
        **_header_details(),
    )


@app.route("/bill/<int:challan_no>/edit", methods=["GET", "POST"])
def edit_bill(challan_no):
    """Show the edit form or save edits to an existing bill."""
    bill = get_bill(challan_no)
    if bill is None:
        return "Bill not found", 404

    if request.method == "GET":
        return _render_entry_form(bill=bill, editing=True)

    try:
        bill_data = _bill_data_from_form()
        update_bill_in_db(challan_no, bill_data)
    except ValueError as error:
        return _render_entry_form(
            bill=_submitted_bill_for_retry(challan_no),
            editing=True,
            error=str(error),
        ), 400
    except sqlite3.Error:
        app.logger.exception("Could not update bill %s.", challan_no)
        return _render_entry_form(
            bill=_submitted_bill_for_retry(challan_no),
            editing=True,
            error="The bill could not be updated because of a database error. Please try again.",
        ), 500

    return redirect(url_for("view_bill", challan_no=challan_no))


if __name__ == "__main__":
    # debug=True reloads the app when you change code (development only).
    app.run(debug=True)
