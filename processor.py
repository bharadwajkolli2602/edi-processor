# ============================================
# EDI File Processor
# Phase 5: API Notifications
# ============================================

import os
import logging
import requests
from datetime import datetime

# ── Webhook Config ────────────────────────
WEBHOOK_URL = "https://webhook.site/7e966afc-6c5b-4ed7-b26f-1b434bc23a73"

# ── Logging Setup ─────────────────────────
def setup_logging():
    log_filename = f"logs/processor_{datetime.now().strftime('%Y%m%d')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_filename, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    logging.info("Logging initialized")
    logging.info(f"Log file: {log_filename}")

# ── 1. Get file type ──────────────────────
def get_file_type(filename):
    if filename.endswith(".edi"):
        return "EDI"
    elif filename.endswith(".csv"):
        return "CSV"
    else:
        return "Unknown"

# ── 2. Read file content ──────────────────
def read_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read()
        return content
    except FileNotFoundError:
        logging.error(f"File not found: {filepath}")
        return None
    except Exception as e:
        logging.error(f"Failed to read file {filepath}: {e}")
        return None

# ── 3. Parse EDI segments ─────────────────
def parse_edi(content):
    try:
        segments = content.strip().split("\n")
        result = {
            "sender": "",
            "receiver": "",
            "transaction_type": "",
            "po_number": "",
            "line_items": []
        }
        for segment in segments:
            elements = segment.split("*")
            tag = elements[0]
            if tag == "ISA":
                result["sender"]   = elements[6].strip()
                result["receiver"] = elements[8].strip()
            elif tag == "ST":
                result["transaction_type"] = elements[1]
            elif tag == "BEG":
                result["po_number"] = elements[3]
            elif tag == "PO1":
                item = {
                    "quantity": elements[2],
                    "unit":     elements[3],
                    "price":    elements[4]
                }
                result["line_items"].append(item)

        if not result["sender"]:
            raise ValueError("Missing ISA sender in EDI file")
        if not result["transaction_type"]:
            raise ValueError("Missing ST transaction type in EDI file")

        return result

    except ValueError as e:
        logging.error(f"EDI validation error: {e}")
        return None
    except Exception as e:
        logging.error(f"Failed to parse EDI content: {e}")
        return None

# ── 4. Print summary ──────────────────────
def print_summary(filename, parsed):
    logging.info("=" * 50)
    logging.info(f"  FILE     : {filename}")
    logging.info(f"  SENDER   : {parsed['sender']}")
    logging.info(f"  RECEIVER : {parsed['receiver']}")
    logging.info(f"  TYPE     : {parsed['transaction_type']}")
    logging.info(f"  PO NUM   : {parsed['po_number']}")
    logging.info(f"  ITEMS    : {len(parsed['line_items'])}")
    for item in parsed["line_items"]:
        logging.info(f"  Qty: {item['quantity']} {item['unit']} @ ${item['price']}")
    logging.info("=" * 50)

# ── 5. Generate report filename ───────────
def get_report_filename():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"output/report_{timestamp}.txt"

# ── 6. Write summary to file ──────────────
def write_report(filename, parsed, report_file):
    try:
        with open(report_file, "a", encoding="utf-8") as f:
            f.write("=" * 50 + "\n")
            f.write(f"  FILE     : {filename}\n")
            f.write(f"  SENDER   : {parsed['sender']}\n")
            f.write(f"  RECEIVER : {parsed['receiver']}\n")
            f.write(f"  TYPE     : {parsed['transaction_type']}\n")
            f.write(f"  PO NUM   : {parsed['po_number']}\n")
            f.write(f"  ITEMS    : {len(parsed['line_items'])}\n")
            for item in parsed["line_items"]:
                f.write(f"  Qty: {item['quantity']} {item['unit']} @ ${item['price']}\n")
            f.write("=" * 50 + "\n\n")
    except Exception as e:
        logging.error(f"Failed to write report: {e}")

# ── 7. Send notification ──────────────────
def send_notification(processed, skipped, errors, report_file):
    try:
        payload = {
            "summary":   "EDI Processing Complete",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "results": {
                "processed": processed,
                "skipped":   skipped,
                "errors":    errors,
                "report":    report_file
            },
            "status": "SUCCESS" if errors == 0 else "COMPLETED WITH ERRORS"
        }
        response = requests.post(
            WEBHOOK_URL,
            json=payload,
            timeout=10
        )
        logging.info(f"Response status  : {response.status_code}")
        logging.info(f"Response message : {response.text[:100]}")
        if response.status_code == 200:
            logging.info("Notification sent successfully!")
        else:
            logging.warning(f"Notification failed: {response.status_code}")

    except requests.exceptions.ConnectionError:
        logging.error("Could not connect to webhook URL!")
    except requests.exceptions.Timeout:
        logging.error("Webhook request timed out!")
    except Exception as e:
        logging.error(f"Notification error: {e}")

# ── 8. Main processor ─────────────────────
def process_folder(folder):
    if not os.path.exists(folder):
        logging.error(f"Folder not found: {folder}")
        return

    logging.info(f"Scanning folder: {folder}")

    report_file = get_report_filename()
    timestamp   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(report_file, "w", encoding="utf-8") as f:
        f.write("EDI PROCESSING REPORT\n")
        f.write(f"Generated : {timestamp}\n")
        f.write(f"Folder    : {folder}\n\n")

    files     = os.listdir(folder)
    processed = 0
    skipped   = 0
    errors    = 0

    if len(files) == 0:
        logging.warning("No files found in folder!")
        return

    for filename in files:
        filepath  = os.path.join(folder, filename)
        file_type = get_file_type(filename)

        if file_type == "EDI":
            logging.info(f"Processing EDI file: {filename}")
            content = read_file(filepath)
            if content is None:
                errors += 1
                continue
            parsed = parse_edi(content)
            if parsed is None:
                errors += 1
                continue
            print_summary(filename, parsed)
            write_report(filename, parsed, report_file)
            processed += 1
        else:
            logging.warning(f"Skipping unknown file: {filename}")
            skipped += 1

    logging.info("=" * 50)
    logging.info(f"  PROCESSED : {processed} files")
    logging.info(f"  SKIPPED   : {skipped} files")
    logging.info(f"  ERRORS    : {errors} files")
    logging.info(f"  REPORT    : {report_file}")
    logging.info("=" * 50)
    logging.info("Processing complete!")

    # Send notification
    send_notification(processed, skipped, errors, report_file)

# ── Run it! ───────────────────────────────
setup_logging()
process_folder("input")