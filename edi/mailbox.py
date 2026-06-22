# ============================================
# edi/mailbox.py
# Simulates Sterling File Gateway mailbox
# Copies validated EDI file to client mailbox
# ============================================

import os
import shutil
import logging
from datetime import datetime
from config import MAILBOX_WALMART


def submit_to_mailbox(source_filepath, transaction_code, data):
    """
    Copies the validated EDI file to the
    client's allocated SFG mailbox folder.

    In production: this would be an SFTP put
    to the actual Sterling File Gateway path.
    In portfolio:  it's a local folder copy
                   that simulates the same flow.

    Returns:
        success   : True or False
        dest_path : where the file landed
        message   : human readable status
    """
    try:
        # ── Determine destination mailbox ─────
        mailbox_path = _get_mailbox_path(data)

        # Create mailbox folder if it doesn't exist
        os.makedirs(mailbox_path, exist_ok=True)

        # ── Build destination filename ────────
        # Stamp with timestamp so files never overwrite each other
        timestamp    = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_name = os.path.basename(source_filepath)
        dest_filename = f"{timestamp}_{original_name}"
        dest_path     = os.path.join(mailbox_path, dest_filename)

        # ── Copy file to mailbox ──────────────
        shutil.copy2(source_filepath, dest_path)

        # ── Write mailbox receipt ─────────────
        # In real SFG, this would be a tracking record
        _write_receipt(dest_path, transaction_code, data)

        message = (
            f"File submitted to SFG mailbox successfully. "
            f"Mailbox: {mailbox_path}"
        )
        logging.info(f"Mailbox submission: {dest_path}")
        return True, dest_path, message

    except Exception as e:
        message = f"Mailbox submission failed: {e}"
        logging.error(message)
        return False, None, message


def _get_mailbox_path(data):
    """
    Returns the correct mailbox folder based on
    the sender/receiver in the EDI interchange.

    In production, each trading partner has their
    own allocated mailbox in Sterling File Gateway.
    """
    interchange = data.get("interchange", {})
    sender      = interchange.get("sender", "").strip()
    receiver    = interchange.get("receiver", "").strip()

    # Determine which partner is the external party
    # Walmart is the retailer — the other party is the supplier
    if "WALMART" in sender.upper():
        partner = "WALMART"
    elif "WALMART" in receiver.upper():
        partner = "WALMART"
    else:
        partner = sender if sender else "UNKNOWN"

    # Map partner to their mailbox path
    mailbox_map = {
        "WALMART":  MAILBOX_WALMART,
    }

    return mailbox_map.get(partner, f"mailboxes/unknown/{partner.lower()}/inbound")


def _write_receipt(dest_path, transaction_code, data):
    """
    Writes a small receipt file alongside the EDI file.
    Tracks who submitted what and when.
    This simulates SFG's internal tracking records.
    """
    receipt_path = dest_path.replace(".edi", "_receipt.txt")
    interchange  = data.get("interchange", {})

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
        f.write(f"  Submitted At   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"  Transaction    : {transaction_code}\n")
        f.write(f"  {id_label:<15}: {id_value}\n")
        f.write(f"  Sender         : {interchange.get('sender',   'N/A')}\n")
        f.write(f"  Receiver       : {interchange.get('receiver', 'N/A')}\n")
        f.write(f"  Control Number : {interchange.get('control',  'N/A')}\n")
        f.write(f"  File           : {os.path.basename(dest_path)}\n")
        f.write(f"  Status         : DELIVERED TO SFG MAILBOX\n")
        f.write("=" * 50 + "\n")

    logging.info(f"Receipt written: {receipt_path}")


def get_mailbox_contents(partner="WALMART"):
    """
    Lists all files currently in a partner's mailbox.
    Useful for the Flask dashboard to show what's been submitted.
    """
    mailbox_map = {
        "WALMART": MAILBOX_WALMART,
    }
    path = mailbox_map.get(partner.upper(), "")

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