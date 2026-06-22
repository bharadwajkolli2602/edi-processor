# ============================================
# config.py
# Retail EDI Validation Portal
# Generic X12 EDI Configuration
# ============================================

# ── Project Info ──────────────────────────
PROJECT_NAME = "Retail EDI Validation Portal"
EDI_VERSION  = "00401"

# ── Folder Paths ─────────────────────────
INPUT_FOLDER = "input"
OUTPUT_XML   = "output/xml"
OUTPUT_ACKS  = "output/acks"
LOG_FOLDER   = "logs"

# ── Trading Partners & Mailboxes ─────────
TRADING_PARTNERS = {
    "WALMART": {
        "name":    "Walmart",
        "mailbox": "mailboxes/walmart/inbound"
    },
    "TARGET": {
        "name":    "Target",
        "mailbox": "mailboxes/target/inbound"
    },
    "KROGER": {
        "name":    "Kroger",
        "mailbox": "mailboxes/kroger/inbound"
    },
    "COSTCO": {
        "name":    "Costco",
        "mailbox": "mailboxes/costco/inbound"
    },
}

# ── Supported Transaction Types ──────────
TRANSACTION_TYPES = {
    "850": "Purchase Order",
    "810": "Invoice",
    "856": "Ship Notice / ASN",
    "830": "Planning Schedule"
}

# ── Mandatory Segments (X12 004010) ──────
# Standard X12 spec — applies to all partners
WALMART_MANDATORY_SEGMENTS = {
    "850": ["ISA", "GS", "ST", "BEG", "REF", "DTM", "N1", "PO1", "CTT", "SE", "GE", "IEA"],
    "810": ["ISA", "GS", "ST", "BIG", "REF", "N1", "IT1", "TDS", "SE", "GE", "IEA"],
    "856": ["ISA", "GS", "ST", "BSN", "DTM", "HL", "TD1", "TD5", "REF", "SE", "GE", "IEA"],
    "830": ["ISA", "GS", "ST", "BFR", "REF", "N1", "LIN", "FST", "SE", "GE", "IEA"]
}

# ── Field Rules (X12 004010) ──────────────
WALMART_FIELD_RULES = {
    "850": {
        "BEG": {
            "positions": [1, 2, 3, 5],
            "names":     ["Transaction Set Purpose", "PO Type", "PO Number", "PO Date"]
        },
        "PO1": {
            "positions": [1, 2, 3, 4],
            "names":     ["Line Number", "Quantity", "Unit of Measure", "Unit Price"]
        },
        "CTT": {
            "positions": [1],
            "names":     ["Total Line Item Count"]
        }
    },
    "810": {
        "BIG": {
            "positions": [1, 2, 4],
            "names":     ["Invoice Date", "Invoice Number", "PO Number"]
        },
        "IT1": {
            "positions": [2, 3, 4],
            "names":     ["Quantity Invoiced", "Unit of Measure", "Unit Price"]
        },
        "TDS": {
            "positions": [1],
            "names":     ["Total Invoice Amount"]
        }
    },
    "856": {
        "BSN": {
            "positions": [2, 3, 4],
            "names":     ["Shipment ID", "Ship Date", "Ship Time"]
        },
        "TD1": {
            "positions": [1, 7],
            "names":     ["Packaging Code", "Gross Weight"]
        },
        "TD5": {
            "positions": [2, 3],
            "names":     ["SCAC Code", "Routing"]
        }
    },
    "830": {
        "BFR": {
            "positions": [1, 2, 4],
            "names":     ["Transaction Set Purpose", "Release Number", "Schedule Date"]
        },
        "FST": {
            "positions": [1, 2, 3],
            "names":     ["Quantity", "Forecast Qualifier", "Forecast Date"]
        }
    }
}

# ── 997 Acknowledgment Codes ─────────────
ACK_ACCEPTED = "A"
ACK_REJECTED = "R"

# ── Flask Settings ────────────────────────
FLASK_SECRET_KEY  = "edi-portal-2026"
ALLOWED_EXTENSION = ".edi"