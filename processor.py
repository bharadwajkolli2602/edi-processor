# ============================================
# EDI File Processor
# Phase 3: Professional Logging
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


# ── EDI File Processor ───────────────────
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
    with open(filepath, "r") as file:
        content = file.read()
    return content

# ── 3. Parse EDI segments ─────────────────
def parse_edi(content):
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

    return result

# ── 4. Print summary to screen ────────────
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

# ── 7. Main processor ─────────────────────
def process_folder(folder):
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

    for filename in files:
        filepath  = os.path.join(folder, filename)
        file_type = get_file_type(filename)

        if file_type == "EDI":
            logging.info(f"Processing EDI file: {filename}")
            content = read_file(filepath)
            parsed  = parse_edi(content)
            print_summary(filename, parsed)
            write_report(filename, parsed, report_file)
        else:
            logging.warning(f"Skipping unknown file: {filename}")

    logging.info(f"Report saved to: {report_file}")
    logging.info("Processing complete!")

# ── Run it! ───────────────────────────────
setup_logging()
process_folder("input")