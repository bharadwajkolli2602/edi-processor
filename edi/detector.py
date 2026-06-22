# ============================================
# edi/detector.py
# Detects EDI transaction type from file
# Returns: "850", "810", "856", "830", or None
# ============================================

import logging
from config import TRANSACTION_TYPES

def detect_transaction_type(content):
    """
    Reads the ST segment from EDI content
    and returns the transaction type code.

    ST*850*0001  →  returns "850"
    ST*810*0001  →  returns "810"
    ST*856*0001  →  returns "856"
    ST*830*0001  →  returns "830"
    """
    try:
        lines = content.strip().split("\n")

        for line in lines:
            elements = line.strip().split("*")

            # ST segment is always: ST * transaction_code * control_number
            if elements[0] == "ST":
                transaction_code = elements[1].strip()

                if transaction_code in TRANSACTION_TYPES:
                    tx_name = TRANSACTION_TYPES[transaction_code]
                    logging.info(f"Detected transaction type: {transaction_code} - {tx_name}")
                    return transaction_code
                else:
                    logging.error(f"Unknown transaction type in ST segment: {transaction_code}")
                    return None

        # If we looped through everything and found no ST segment
        logging.error("No ST segment found in file — cannot detect transaction type")
        return None

    except Exception as e:
        logging.error(f"detector.py failed: {e}")
        return None


def get_transaction_name(code):
    """
    Returns human-readable name for a transaction code.
    get_transaction_name("850") → "Purchase Order"
    """
    return TRANSACTION_TYPES.get(code, "Unknown Transaction Type")