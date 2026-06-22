# ============================================
# app.py
# Retail EDI Validation Portal
# Flask Web Application
# ============================================

import sys
sys.stdout.reconfigure(encoding="utf-8")

import os
import logging
from datetime import datetime
from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, send_file, session
)

from config import (
    FLASK_SECRET_KEY, ALLOWED_EXTENSION,
    INPUT_FOLDER, LOG_FOLDER
)
from edi.detector     import detect_transaction_type, get_transaction_name
from edi.validator    import validate, format_validation_report
from edi.parser       import parse
from edi.xml_builder  import build_xml
from edi.acknowledger import generate_997
from edi.mailbox      import submit_to_mailbox, get_mailbox_contents

# ── App Setup ─────────────────────────────
app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

# ── Logging Setup ─────────────────────────
os.makedirs(LOG_FOLDER, exist_ok=True)
log_filename = os.path.join(
    LOG_FOLDER,
    f"portal_{datetime.now().strftime('%Y%m%d')}.log"
)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_filename, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# ── In-memory transaction history ─────────
# Stores results of all uploads this session
transaction_history = []


# ── Helper ────────────────────────────────
def allowed_file(filename):
    return filename.lower().endswith(ALLOWED_EXTENSION)


# ============================================
# ROUTE 1: Home / Upload Page
# ============================================
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


# ============================================
# ROUTE 2: Process uploaded EDI file
# ============================================
@app.route("/process", methods=["POST"])
def process():
    # ── Check file was uploaded ───────────
    if "edi_file" not in request.files:
        flash("No file selected. Please choose an EDI file.", "error")
        return redirect(url_for("index"))

    file = request.files["edi_file"]

    if file.filename == "":
        flash("No file selected.", "error")
        return redirect(url_for("index"))

    if not allowed_file(file.filename):
        flash("Invalid file type. Only .edi files are accepted.", "error")
        return redirect(url_for("index"))

    # ── Save uploaded file ────────────────
    os.makedirs(INPUT_FOLDER, exist_ok=True)
    timestamp     = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    filepath      = os.path.join(INPUT_FOLDER, safe_filename)
    file.save(filepath)
    logging.info(f"File uploaded: {filepath}")

    # ── Read content ──────────────────────
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # ── Step 1: Detect transaction type ───
    transaction_code = detect_transaction_type(content)
    if not transaction_code:
        flash("Could not detect EDI transaction type. Check your file.", "error")
        return redirect(url_for("index"))

    transaction_name = get_transaction_name(transaction_code)

    # ── Step 2: Validate ──────────────────
    validation_result = validate(content, transaction_code)

    # ── Step 3: Parse ─────────────────────
    parsed_data = parse(content, transaction_code)

    # ── Step 4: Build XML ─────────────────
    xml_filepath = None
    if validation_result["valid"] and parsed_data:
        xml_filepath = build_xml(parsed_data, transaction_code, validation_result)

    # ── Step 5: Generate 997 FA ───────────
    ack_filepath, ack_code, ack_label = generate_997(
        parsed_data or {"interchange": {}},
        transaction_code,
        validation_result
    )

    # ── Step 6: Build result context ──────
    result = {
        "filename":         file.filename,
        "timestamp":        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "transaction_code": transaction_code,
        "transaction_name": transaction_name,
        "valid":            validation_result["valid"],
        "errors":           validation_result["errors"],
        "warnings":         validation_result["warnings"],
        "parsed":           parsed_data,
        "xml_filepath":     xml_filepath,
        "ack_filepath":     ack_filepath,
        "ack_label":        ack_label,
        "submitted":        False,
        "submit_message":   ""
    }

    # ── Add to history ────────────────────
    transaction_history.append({
        "timestamp":        result["timestamp"],
        "filename":         result["filename"],
        "transaction_code": transaction_code,
        "transaction_name": transaction_name,
        "status":           "VALID" if result["valid"] else "INVALID",
        "ack_label":        ack_label
    })

    # ── Store result in session for submit
    session["last_filepath"]         = filepath
    session["last_transaction_code"] = transaction_code

    return render_template("result.html", result=result)


# ============================================
# ROUTE 3: Submit to SFG Mailbox
# ============================================
@app.route("/submit", methods=["POST"])
def submit():
    filepath         = session.get("last_filepath")
    transaction_code = session.get("last_transaction_code")

    if not filepath or not transaction_code:
        flash("Session expired. Please upload your file again.", "error")
        return redirect(url_for("index"))

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    parsed_data = parse(content, transaction_code)
    success, dest, message = submit_to_mailbox(
        filepath, transaction_code, parsed_data
    )

    if success:
        flash(f"File submitted to SFG mailbox successfully! → {dest}", "success")
    else:
        flash(f"Submission failed: {message}", "error")

    return redirect(url_for("history"))


# ============================================
# ROUTE 4: Transaction History
# ============================================
@app.route("/history")
def history():
    mailbox_files = get_mailbox_contents("WALMART")
    return render_template(
        "history.html",
        history=transaction_history,
        mailbox_files=mailbox_files
    )


# ============================================
# ROUTE 5: Download files
# ============================================
@app.route("/download/<path:filepath>")
def download(filepath):
    try:
        return send_file(filepath, as_attachment=True)
    except Exception as e:
        flash(f"Download failed: {e}", "error")
        return redirect(url_for("index"))


# ── Run ───────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=5000)