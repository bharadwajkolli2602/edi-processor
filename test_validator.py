# ============================================
# test_validator.py
# Tests detector + validator together
# Run: python test_validator.py
# ============================================

import sys
sys.stdout.reconfigure(encoding="utf-8")

import logging
from edi.detector  import detect_transaction_type
from edi.validator import validate, format_validation_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

test_files = [
    "input/walmart_850_test.edi",
    "input/walmart_810_test.edi",
    "input/walmart_856_test.edi",
    "input/walmart_830_test.edi",
    "input/walmart_850_bad.edi",
]

for filepath in test_files:
    print(f"\nTesting: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    code   = detect_transaction_type(content)
    result = validate(content, code)
    report = format_validation_report(code, result)

    print(report)

    # ── Test Parser ───────────────────────────
print("\n\nPARSER TEST")
print("=" * 50)

from edi.parser import parse

valid_files = [
    ("input/walmart_850_test.edi", "850"),
    ("input/walmart_810_test.edi", "810"),
    ("input/walmart_856_test.edi", "856"),
    ("input/walmart_830_test.edi", "830"),
]

for filepath, code in valid_files:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    data = parse(content, code)

    if data:
        print(f"\n✅ {code} - {data['transaction_name']}")
        print(f"   Sender      : {data['interchange']['sender']}")
        print(f"   Receiver    : {data['interchange']['receiver']}")

        if code == "850":
            print(f"   PO Number   : {data['po_number']}")
            print(f"   Ship Date   : {data['ship_date']}")
            print(f"   Line Items  : {len(data['line_items'])}")
            print(f"   Order Total : ${data['order_total']}")

        elif code == "810":
            print(f"   Invoice #   : {data['invoice_number']}")
            print(f"   PO Number   : {data['po_number']}")
            print(f"   Total       : ${data['invoice_total']}")

        elif code == "856":
            print(f"   Shipment ID : {data['shipment_id']}")
            print(f"   Ship Date   : {data['ship_date']}")
            print(f"   Carrier     : {data['carrier_scac']}")
            print(f"   BOL Number  : {data['bol_number']}")

        elif code == "830":
            print(f"   Release #   : {data['release_number']}")
            print(f"   Schedule Dt : {data['schedule_date']}")
            print(f"   Line Items  : {len(data['line_items'])}")
            print(f"   Forecasts   : {sum(len(i['forecasts']) for i in data['line_items'])}")
    else:
        print(f"\n❌ {code} - Parsing failed")

print("\n" + "=" * 50)
# ── Test XML Builder ──────────────────────
print("\n\nXML BUILDER TEST")
print("=" * 50)

from edi.xml_builder import build_xml

for filepath, code in valid_files:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    data           = parse(content, code)
    validation     = {"valid": True, "errors": [], "warnings": []}
    xml_filepath   = build_xml(data, code, validation)

    if xml_filepath:
        print(f"✅ {code} → {xml_filepath}")
    else:
        print(f"❌ {code} → XML generation failed")

print("=" * 50)
# ── Test Acknowledger ─────────────────────
print("\n\nACKNOWLEDGER TEST")
print("=" * 50)

from edi.acknowledger import generate_997

# Test accepted — all 4 valid files
for filepath, code in valid_files:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    data       = parse(content, code)
    validation = {"valid": True, "errors": [], "warnings": []}
    filepath_out, ack_code, ack_label = generate_997(data, code, validation)

    if filepath_out:
        print(f"✅ {code} → {ack_label} → {filepath_out}")
    else:
        print(f"❌ {code} → 997 generation failed")

# Test rejected — bad file
print()
with open("input/walmart_850_bad.edi", "r", encoding="utf-8") as f:
    bad_content = f.read()

bad_code       = detect_transaction_type(bad_content)
bad_data       = parse(bad_content, bad_code)
bad_validation = validate(bad_content, bad_code)
filepath_out, ack_code, ack_label = generate_997(bad_data, bad_code, bad_validation)

if filepath_out:
    print(f"✅ BAD FILE → {ack_label} → {filepath_out}")

print("=" * 50)
print("\nContents of rejected 997:")
print("-" * 50)
with open(filepath_out, "r") as f:
    print(f.read())
print("-" * 50)
# ── Test Mailbox ──────────────────────────
print("\n\nMAILBOX TEST")
print("=" * 50)

from edi.mailbox import submit_to_mailbox, get_mailbox_contents

# Submit the 850 — simulate a valid file going to SFG
with open("input/walmart_850_test.edi", "r", encoding="utf-8") as f:
    content = f.read()

data    = parse(content, "850")
success, dest, message = submit_to_mailbox(
    "input/walmart_850_test.edi", "850", data
)

if success:
    print(f"✅ Submitted to mailbox")
    print(f"   Location : {dest}")
    print(f"   Message  : {message}")
else:
    print(f"❌ {message}")

# Show mailbox contents
print("\nMailbox contents (Walmart):")
print("-" * 50)
files = get_mailbox_contents("WALMART")
for f in files:
    print(f"  {f['submitted']}  |  {f['filename']}")
print("=" * 50)