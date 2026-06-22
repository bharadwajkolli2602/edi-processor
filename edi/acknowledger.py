# ============================================
# edi/acknowledger.py
# Generates 997 Functional Acknowledgment
# Accepted (A) or Rejected (R) per Walmart spec
# ============================================

import os
import logging
from datetime import datetime
from config import OUTPUT_ACKS, ACK_ACCEPTED, ACK_REJECTED


def generate_997(data, transaction_code, validation_result):
    """
    Builds a 997 FA EDI file and saves to output/acks/
    Returns the output filepath.

    997 structure:
    ISA  → Interchange header   (we flip sender/receiver)
    GS   → Functional group
    ST   → Transaction set header (997)
    AK1  → Functional group response
    AK2  → Transaction set response
    AK5  → Transaction set acknowledgment (A or R)
    AK9  → Functional group acknowledgment
    SE   → Transaction set trailer
    GE   → Functional group trailer
    IEA  → Interchange trailer
    """
    try:
        interchange  = data.get("interchange", {})

        # Flip sender and receiver —
        # we are now responding TO whoever sent the file
        original_sender   = interchange.get("sender",   "SUPPLIER123")
        original_receiver = interchange.get("receiver", "WALMART")
        control_number    = interchange.get("control",  "000000001")

        now      = datetime.now()
        date_str = now.strftime("%y%m%d")    # YYMMDD  e.g. 260621
        time_str = now.strftime("%H%M")      # HHMM    e.g. 1740

        # Determine accept or reject
        ack_code    = ACK_ACCEPTED if validation_result["valid"] else ACK_REJECTED
        ack_label   = "Accepted"   if validation_result["valid"] else "Rejected"
        error_count = len(validation_result["errors"])

        # ── Build 997 segments ────────────────
        segments = []

        # ISA — Interchange Control Header
        # We swap sender/receiver to respond back
        segments.append(
            f"ISA*00*          *00*          "
            f"*ZZ*{original_receiver:<15}"
            f"*ZZ*{original_sender:<15}"
            f"*{date_str}*{time_str}"
            f"*U*00401*{control_number}*0*P*>"
        )

        # GS — Functional Group Header
        # FA = Functional Acknowledgment group type
        segments.append(
            f"GS*FA"
            f"*{original_receiver.strip()}"
            f"*{original_sender.strip()}"
            f"*{now.strftime('%Y%m%d')}"
            f"*{time_str}*1*X*004010"
        )

        # ST — Transaction Set Header
        # 997 = Functional Acknowledgment
        segments.append("ST*997*0001")

        # AK1 — Functional Group Response
        # Identifies which functional group we are acknowledging
        # PO=850, IN=810, SH=856, PS=830
        gs_codes = {
            "850": "PO",
            "810": "IN",
            "856": "SH",
            "830": "PS"
        }
        gs_code = gs_codes.get(transaction_code, "XX")
        segments.append(f"AK1*{gs_code}*1")

        # AK2 — Transaction Set Response
        # Identifies the specific transaction set
        segments.append(f"AK2*{transaction_code}*0001")

        # AK3/AK4 — Error segments (only if rejected)
        # Lists each error with segment position
        if not validation_result["valid"]:
            for i, error in enumerate(validation_result["errors"], 1):
                # AK3 = segment error  (segment tag, position, loop, error code)
                # 8 = Missing mandatory segment
                # Extract segment name from error message if possible
                seg_name = _extract_segment_name(error)
                segments.append(f"AK3*{seg_name}*{i}**8")

        # AK5 — Transaction Set Acknowledgment
        # A = Accepted, R = Rejected
        if validation_result["valid"]:
            segments.append(f"AK5*{ACK_ACCEPTED}")
        else:
            segments.append(f"AK5*{ACK_REJECTED}*5")
            # Error code 5 = One or more segments in error

        # AK9 — Functional Group Acknowledgment
        # Fields: ack code, # of transaction sets included,
        #         # received, # accepted
        accepted_count = 1 if validation_result["valid"] else 0
        segments.append(
            f"AK9*{ack_code}*1*1*{accepted_count}"
        )

        # SE — Transaction Set Trailer
        # SE element 1 = segment count (ST through SE inclusive)
        segment_count = len(segments) - 2 + 1
        # -2 for ISA and GS, +1 to include SE itself
        segments.append(f"SE*{segment_count}*0001")

        # GE — Functional Group Trailer
        segments.append("GE*1*1")

        # IEA — Interchange Control Trailer
        segments.append(f"IEA*1*{control_number}")

        # ── Write to file ─────────────────────
        filename = _get_ack_filename(data, transaction_code, ack_label)
        filepath = os.path.join(OUTPUT_ACKS, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(segments))

        logging.info(f"997 FA generated: {filepath} | Status: {ack_label}")
        return filepath, ack_code, ack_label

    except Exception as e:
        logging.error(f"acknowledger.py failed: {e}")
        return None, None, None


def _extract_segment_name(error_message):
    """
    Pulls segment tag from error message.
    'Missing mandatory segment: BEG (required...)' → 'BEG'
    """
    try:
        parts = error_message.split(":")
        if len(parts) > 1:
            return parts[1].strip().split(" ")[0]
    except Exception:
        pass
    return "ZZ"


def _get_ack_filename(data, transaction_code, ack_label):
    """
    Generates a meaningful filename for the 997 FA.
    997_850_PO-78542_Accepted_20260621_174056.edi
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    identifiers = {
        "850": data.get("po_number",      "unknown"),
        "810": data.get("invoice_number", "unknown"),
        "856": data.get("shipment_id",    "unknown"),
        "830": data.get("release_number", "unknown"),
    }
    identifier = identifiers.get(transaction_code, "unknown")
    return f"997_{transaction_code}_{identifier}_{ack_label}_{timestamp}.edi"