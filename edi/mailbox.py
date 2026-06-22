# ============================================
# edi/mailbox.py
# Routes validated EDI files to the correct
# trading partner mailbox (simulates SFG)
# ============================================

import os
import shutil
import logging
from datetime import datetime
from config import TRADING_PARTNERS


def submit_to_mailbox(source_filepath, transaction_code, data, partner_key):
    """
    Copies validated EDI file to the selected
    trading partner's SFG mailbox folder.

    In production: SFTP put to Sterling File Gateway.
    In portfolio:  local folder simulating SFG drop.
    """
    try:
        partner      = TRADING_PARTNERS.get(partner_key.upper())
        mailbox_path = partner["mailbox"] if partner else f"mailboxes/unknown/inbound"

        os.makedirs(mailbox_path, exist_ok=True)

        timestamp     = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_name = os.path.basename(source_filepath)
        dest_filename = f"{timestamp}_{original_name}"
        dest_path     = os.path.join(mailbox_path, dest_filename)

        shutil.copy2(source_filepath, dest_path)
        _write_receipt(dest_path, transaction_code, data, partner_key)

        message = (
            f"File submitted to {partner['name']} SFG mailbox successfully. "
            f"Path: {mailbox_path}"
        )
        logging.info(f"Mailbox submission: {dest_path}")
        return True, dest_path, message

    except Exception as e:
        message = f"Mailbox submission failed: {e}"
        logging.error(message)
        return False, None, message


def _write_receipt(dest_path, transaction_code, data, partner_key):
    receipt_path = dest_path.replace(".edi", "_receipt.txt")
    interchange  = data.get("interchange", {})
    partner      = TRADING_PARTNERS.get(partner_key.upper(), {})

    identifiers = {
        "850": ("PO Number",      data.get("po_number",      "N/A")),
        "810": ("Invoice Number", data.get("invoice_number", "N/A")),
        "856": ("Shipment ID",    data.get("shipment_id",    "N/A")),
        "830": ("Release Number", data.get("release_number", "N/A")),
    }
    id_label, id_value = identifiers.get(transaction_code, ("Reference", "N/A"))

    with open(receipt_path, "w", encoding="utf-8") as f:
        f.write("=" * 50 + "\n")
        f.write("  SFG MAILBOX SUBMISSION RECEIPT\n")
        f.write("=" * 50 + "\n")
        f.write(f"  Submitted At    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"  Trading Partner : {partner.get('name', partner_key)}\n")
        f.write(f"  Transaction     : {transaction_code}\n")
        f.write(f"  {id_label:<16}: {id_value}\n")
        f.write(f"  Sender          : {interchange.get('sender',   'N/A')}\n")
        f.write(f"  Receiver        : {interchange.get('receiver', 'N/A')}\n")
        f.write(f"  Control Number  : {interchange.get('control',  'N/A')}\n")
        f.write(f"  File            : {os.path.basename(dest_path)}\n")
        f.write(f"  Status          : DELIVERED TO SFG MAILBOX\n")
        f.write("=" * 50 + "\n")


def get_mailbox_contents(partner_key="WALMART"):
    partner = TRADING_PARTNERS.get(partner_key.upper(), {})
    path    = partner.get("mailbox", "")

    if not path or not os.path.exists(path):
        return []

    files = []
    for filename in sorted(os.listdir(path)):
        filepath = os.path.join(path, filename)
        stat     = os.stat(filepath)
        files.append({
            "filename":  filename,
            "size":      f"{stat.st_size:,} bytes",
            "submitted": datetime.fromtimestamp(
                stat.st_mtime
            ).strftime("%Y-%m-%d %H:%M:%S")
        })
    return files