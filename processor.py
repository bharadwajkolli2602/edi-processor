# ============================================
# EDI File Processor
# Phase 2: Read, Parse & Write Reports
# ============================================

import os
from datetime import datetime

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
    print("=" * 50)
    print(f"  FILE     : {filename}")
    print(f"  SENDER   : {parsed['sender']}")
    print(f"  RECEIVER : {parsed['receiver']}")
    print(f"  TYPE     : {parsed['transaction_type']}")
    print(f"  PO NUM   : {parsed['po_number']}")
    print(f"  ITEMS    : {len(parsed['line_items'])}")
    for item in parsed["line_items"]:
        print(f"    → Qty: {item['quantity']} {item['unit']} @ ${item['price']}")
    print("=" * 50)

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
            f.write(f"    → Qty: {item['quantity']} {item['unit']} @ ${item['price']}\n")
        f.write("=" * 50 + "\n\n")

# ── 7. Main processor ─────────────────────
def process_folder(folder):
    print(f"\n[START] Scanning folder: {folder}\n")

    # Create report file with timestamp
    report_file = get_report_filename()
    timestamp   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Write report header
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("EDI PROCESSING REPORT\n")
        f.write(f"Generated : {timestamp}\n")
        f.write(f"Folder    : {folder}\n\n")

    files = os.listdir(folder)

    if len(files) == 0:
        print("[WARN] No files found!")
        return

    for filename in files:
        filepath  = os.path.join(folder, filename)
        file_type = get_file_type(filename)

        print(f"[LOG] Found {file_type} file: {filename}")

        if file_type == "EDI":
            content = read_file(filepath)
            parsed  = parse_edi(content)
            print_summary(filename, parsed)
            write_report(filename, parsed, report_file)
        else:
            print(f"[SKIP] Skipping {filename}")

    print(f"\n[DONE] Report saved to: {report_file}")
    print("[DONE] Processing complete!")

# ── Run it! ───────────────────────────────
process_folder("input")