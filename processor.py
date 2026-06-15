# ============================================
# EDI File Processor
# Phase 4: Error Handling
# ============================================

import os
import logging
from datetime import datetime

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

        # Validate required fields
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

# ── 7. Main processor ─────────────────────
def process_folder(folder):

    # Check if folder exists
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

    files = os.listdir(folder)

    if len(files) == 0:
        logging.warning("No files found in folder!")
        return

    # Track stats
    processed = 0
    skipped   = 0
    errors    = 0

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

    # Final summary
    logging.info("=" * 50)
    logging.info(f"  PROCESSED : {processed} files")
    logging.info(f"  SKIPPED   : {skipped} files")
    logging.info(f"  ERRORS    : {errors} files")
    logging.info(f"  REPORT    : {report_file}")
    logging.info("=" * 50)
    logging.info("Processing complete!")

# ── Run it! ───────────────────────────────
setup_logging()
process_folder("input")