# ============================================
# edi/parser.py
# Parses EDI content into structured Python dict
# One parser function per transaction type
# ============================================

import logging


def parse(content, transaction_code):
    """
    Routes to the correct parser based on transaction type.
    Returns a clean Python dict with all business data.
    Returns None if parsing fails.
    """
    parsers = {
        "850": _parse_850,
        "810": _parse_810,
        "856": _parse_856,
        "830": _parse_830,
    }

    parser_func = parsers.get(transaction_code)

    if not parser_func:
        logging.error(f"No parser available for transaction type: {transaction_code}")
        return None

    try:
        lines  = content.strip().split("\n")
        result = parser_func(lines)
        logging.info(f"Parsed {transaction_code} successfully")
        return result

    except Exception as e:
        logging.error(f"parser.py failed for {transaction_code}: {e}")
        return None


# ── 850 Purchase Order ────────────────────
def _parse_850(lines):
    data = {
        "transaction_type": "850",
        "transaction_name": "Purchase Order",
        "interchange": {},
        "po_number":   "",
        "po_date":     "",
        "po_type":     "",
        "ship_date":   "",
        "cancel_date": "",
        "buyer":       {},
        "seller":      {},
        "line_items":  [],
        "total_lines": ""
    }

    for line in lines:
        seg = line.strip().split("*")
        tag = seg[0]

        if tag == "ISA":
            data["interchange"] = {
                "sender":   _get(seg, 6),
                "receiver": _get(seg, 8),
                "date":     _get(seg, 9),
                "control":  _get(seg, 13)
            }

        elif tag == "BEG":
            data["po_number"] = _get(seg, 3)
            data["po_type"]   = _get(seg, 2)
            data["po_date"]   = _format_date(_get(seg, 5))

        elif tag == "DTM":
            qualifier = _get(seg, 1)
            date_val  = _format_date(_get(seg, 2))
            if qualifier == "010":
                data["ship_date"]   = date_val
            elif qualifier == "001":
                data["cancel_date"] = date_val

        elif tag == "N1":
            qualifier = _get(seg, 1)
            name      = _get(seg, 2)
            id_val    = _get(seg, 4)
            if qualifier == "BY":
                data["buyer"]  = {"name": name, "id": id_val}
            elif qualifier == "ST":
                data["seller"] = {"name": name, "id": id_val}

        elif tag == "PO1":
            item = {
                "line_number": _get(seg, 1),
                "quantity":    _get(seg, 2),
                "unit":        _get(seg, 3),
                "unit_price":  _get(seg, 4),
                "upc":         _get(seg, 7),
                "vendor_item": _get(seg, 9)
            }
            data["line_items"].append(item)

        elif tag == "CTT":
            data["total_lines"] = _get(seg, 1)

    # Calculate order total
    data["order_total"] = _calculate_total(data["line_items"])
    return data


# ── 810 Invoice ───────────────────────────
def _parse_810(lines):
    data = {
        "transaction_type":  "810",
        "transaction_name":  "Invoice",
        "interchange":       {},
        "invoice_number":    "",
        "invoice_date":      "",
        "po_number":         "",
        "vendor_number":     "",
        "remit_to":          {},
        "ship_to":           {},
        "line_items":        [],
        "invoice_total":     ""
    }

    for line in lines:
        seg = line.strip().split("*")
        tag = seg[0]

        if tag == "ISA":
            data["interchange"] = {
                "sender":   _get(seg, 6),
                "receiver": _get(seg, 8),
                "date":     _get(seg, 9),
                "control":  _get(seg, 13)
            }

        elif tag == "BIG":
            data["invoice_date"]   = _format_date(_get(seg, 1))
            data["invoice_number"] = _get(seg, 2)
            data["po_number"]      = _get(seg, 4)

        elif tag == "REF":
            if _get(seg, 1) == "VN":
                data["vendor_number"] = _get(seg, 2)

        elif tag == "N1":
            qualifier = _get(seg, 1)
            name      = _get(seg, 2)
            id_val    = _get(seg, 4)
            if qualifier == "RE":
                data["remit_to"] = {"name": name, "id": id_val}
            elif qualifier == "ST":
                data["ship_to"]  = {"name": name, "id": id_val}

        elif tag == "IT1":
            item = {
                "line_number": _get(seg, 1),
                "quantity":    _get(seg, 2),
                "unit":        _get(seg, 3),
                "unit_price":  _get(seg, 4),
                "upc":         _get(seg, 7)
            }
            data["line_items"].append(item)

        elif tag == "TDS":
            raw   = _get(seg, 1)
            # TDS amount is in cents — divide by 100
            data["invoice_total"] = str(int(raw) / 100) if raw.isdigit() else raw

    return data


# ── 856 Ship Notice / ASN ─────────────────
def _parse_856(lines):
    data = {
        "transaction_type": "856",
        "transaction_name": "Ship Notice / ASN",
        "interchange":      {},
        "shipment_id":      "",
        "ship_date":        "",
        "ship_time":        "",
        "bol_number":       "",
        "po_reference":     "",
        "carrier_scac":     "",
        "routing":          "",
        "packaging_code":   "",
        "gross_weight":     "",
        "hl_levels":        []
    }

    for line in lines:
        seg = line.strip().split("*")
        tag = seg[0]

        if tag == "ISA":
            data["interchange"] = {
                "sender":   _get(seg, 6),
                "receiver": _get(seg, 8),
                "date":     _get(seg, 9),
                "control":  _get(seg, 13)
            }

        elif tag == "BSN":
            data["shipment_id"] = _get(seg, 2)
            data["ship_date"]   = _format_date(_get(seg, 3))
            data["ship_time"]   = _get(seg, 4)

        elif tag == "TD1":
            data["packaging_code"] = _get(seg, 1)
            data["gross_weight"]   = _get(seg, 7)

        elif tag == "TD5":
            data["carrier_scac"] = _get(seg, 3)
            data["routing"]      = _get(seg, 4)

        elif tag == "REF":
            qualifier = _get(seg, 1)
            if qualifier == "BM":
                data["bol_number"]   = _get(seg, 2)
            elif qualifier == "PO":
                data["po_reference"] = _get(seg, 2)

        elif tag == "HL":
            level = {
                "id":     _get(seg, 1),
                "parent": _get(seg, 2),
                "code":   _get(seg, 3)
            }
            data["hl_levels"].append(level)

    return data


# ── 830 Planning Schedule ─────────────────
def _parse_830(lines):
    data = {
        "transaction_type": "830",
        "transaction_name": "Planning Schedule",
        "interchange":      {},
        "release_number":   "",
        "schedule_date":    "",
        "buyer":            {},
        "seller":           {},
        "line_items":       []
    }

    current_item = None

    for line in lines:
        seg = line.strip().split("*")
        tag = seg[0]

        if tag == "ISA":
            data["interchange"] = {
                "sender":   _get(seg, 6),
                "receiver": _get(seg, 8),
                "date":     _get(seg, 9),
                "control":  _get(seg, 13)
            }

        elif tag == "BFR":
            data["release_number"] = _get(seg, 2)
            data["schedule_date"]  = _format_date(_get(seg, 4))

        elif tag == "N1":
            qualifier = _get(seg, 1)
            name      = _get(seg, 2)
            id_val    = _get(seg, 4)
            if qualifier == "BY":
                data["buyer"]  = {"name": name, "id": id_val}
            elif qualifier == "SE":
                data["seller"] = {"name": name, "id": id_val}

        elif tag == "LIN":
            # Save previous item if exists
            if current_item:
                data["line_items"].append(current_item)
            current_item = {
                "line_number": _get(seg, 1),
                "upc":         _get(seg, 3),
                "vendor_item": _get(seg, 5),
                "forecasts":   []
            }

        elif tag == "FST":
            if current_item is not None:
                forecast = {
                    "quantity":   _get(seg, 1),
                    "qualifier":  _get(seg, 2),
                    "date":       _format_date(_get(seg, 3))
                }
                current_item["forecasts"].append(forecast)

    # Don't forget the last item
    if current_item:
        data["line_items"].append(current_item)

    return data


# ── Helper Functions ──────────────────────
def _get(elements, index, default=""):
    """
    Safely gets element at index.
    Returns default if index is out of range.
    Prevents IndexError on short segments.
    """
    try:
        return elements[index].strip()
    except IndexError:
        return default


def _format_date(raw):
    """
    Converts EDI date format to readable format.
    20260620  →  2026-06-20
    260620    →  2026-06-20
    """
    raw = raw.strip()
    if len(raw) == 8:
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:]}"
    elif len(raw) == 6:
        return f"20{raw[:2]}-{raw[2:4]}-{raw[4:]}"
    return raw


def _calculate_total(line_items):
    """
    Calculates order total from line items.
    quantity × unit_price for each item.
    """
    total = 0.0
    for item in line_items:
        try:
            qty   = float(item.get("quantity",   0))
            price = float(item.get("unit_price", 0))
            total += qty * price
        except (ValueError, TypeError):
            pass
    return round(total, 2)