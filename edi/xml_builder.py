# ============================================
# edi/xml_builder.py
# Transforms parsed EDI dict → XML file
# Uses Python's built-in xml.etree.ElementTree
# ============================================

import os
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from config import OUTPUT_XML


def build_xml(data, transaction_code, validation_result):
    """
    Main function — builds XML from parsed data dict.
    Saves file to output/xml/ folder.
    Returns the output filepath.
    """
    try:
        # ── Root element ──────────────────────
        root = ET.Element("EDITransaction")
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        root.set("retailer", "Walmart")
        root.set("version",  "X12-004010")

        # ── Header block ──────────────────────
        _build_header(root, data, transaction_code, validation_result)

        # ── Transaction block ─────────────────
        builders = {
            "850": _build_850,
            "810": _build_810,
            "856": _build_856,
            "830": _build_830,
        }
        builder = builders.get(transaction_code)
        if builder:
            builder(root, data)

        # ── Validation block ──────────────────
        _build_validation(root, validation_result)

        # ── Format and save ───────────────────
        _indent(root)
        tree     = ET.ElementTree(root)
        filename = _get_output_filename(data, transaction_code)
        filepath = os.path.join(OUTPUT_XML, filename)

        tree.write(filepath, encoding="utf-8", xml_declaration=True)
        logging.info(f"XML file written: {filepath}")
        return filepath

    except Exception as e:
        logging.error(f"xml_builder.py failed: {e}")
        return None


# ── Header ────────────────────────────────
def _build_header(root, data, transaction_code, validation_result):
    header = ET.SubElement(root, "Header")

    _tag(header, "TransactionType",    transaction_code)
    _tag(header, "TransactionName",    data.get("transaction_name", ""))
    _tag(header, "Sender",             data["interchange"].get("sender",   ""))
    _tag(header, "Receiver",           data["interchange"].get("receiver", ""))
    _tag(header, "InterchangeDate",    data["interchange"].get("date",     ""))
    _tag(header, "ControlNumber",      data["interchange"].get("control",  ""))
    _tag(header, "ProcessedAt",        datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    _tag(header, "ValidationStatus",   "VALID" if validation_result["valid"] else "INVALID")


# ── 850 Purchase Order ────────────────────
def _build_850(root, data):
    po = ET.SubElement(root, "PurchaseOrder")

    _tag(po, "PONumber",   data.get("po_number",   ""))
    _tag(po, "PODate",     data.get("po_date",     ""))
    _tag(po, "POType",     data.get("po_type",     ""))
    _tag(po, "ShipDate",   data.get("ship_date",   ""))
    _tag(po, "CancelDate", data.get("cancel_date", ""))

    # Buyer
    buyer = ET.SubElement(po, "Buyer")
    _tag(buyer, "Name", data.get("buyer", {}).get("name", ""))
    _tag(buyer, "ID",   data.get("buyer", {}).get("id",   ""))

    # Seller
    seller = ET.SubElement(po, "Seller")
    _tag(seller, "Name", data.get("seller", {}).get("name", ""))
    _tag(seller, "ID",   data.get("seller", {}).get("id",   ""))

    # Line items
    items_el = ET.SubElement(po, "LineItems")
    for item in data.get("line_items", []):
        item_el = ET.SubElement(items_el, "Item")
        item_el.set("sequence", item.get("line_number", ""))
        _tag(item_el, "Quantity",   item.get("quantity",    ""))
        _tag(item_el, "Unit",       item.get("unit",        ""))
        _tag(item_el, "UnitPrice",  item.get("unit_price",  ""))
        _tag(item_el, "UPC",        item.get("upc",         ""))
        _tag(item_el, "VendorItem", item.get("vendor_item", ""))

        # Calculate line total
        try:
            total = float(item["quantity"]) * float(item["unit_price"])
            _tag(item_el, "LineTotal", str(round(total, 2)))
        except (ValueError, KeyError):
            _tag(item_el, "LineTotal", "")

    # Summary
    summary = ET.SubElement(po, "OrderSummary")
    _tag(summary, "TotalLineItems", data.get("total_lines",  ""))
    _tag(summary, "OrderTotal",     str(data.get("order_total", "")))


# ── 810 Invoice ───────────────────────────
def _build_810(root, data):
    inv = ET.SubElement(root, "Invoice")

    _tag(inv, "InvoiceNumber", data.get("invoice_number", ""))
    _tag(inv, "InvoiceDate",   data.get("invoice_date",   ""))
    _tag(inv, "PONumber",      data.get("po_number",      ""))
    _tag(inv, "VendorNumber",  data.get("vendor_number",  ""))

    remit = ET.SubElement(inv, "RemitTo")
    _tag(remit, "Name", data.get("remit_to", {}).get("name", ""))
    _tag(remit, "ID",   data.get("remit_to", {}).get("id",   ""))

    ship = ET.SubElement(inv, "ShipTo")
    _tag(ship, "Name", data.get("ship_to", {}).get("name", ""))
    _tag(ship, "ID",   data.get("ship_to", {}).get("id",   ""))

    items_el = ET.SubElement(inv, "LineItems")
    for item in data.get("line_items", []):
        item_el = ET.SubElement(items_el, "Item")
        item_el.set("sequence", item.get("line_number", ""))
        _tag(item_el, "Quantity",  item.get("quantity",   ""))
        _tag(item_el, "Unit",      item.get("unit",       ""))
        _tag(item_el, "UnitPrice", item.get("unit_price", ""))
        _tag(item_el, "UPC",       item.get("upc",        ""))

        try:
            total = float(item["quantity"]) * float(item["unit_price"])
            _tag(item_el, "LineTotal", str(round(total, 2)))
        except (ValueError, KeyError):
            _tag(item_el, "LineTotal", "")

    summary = ET.SubElement(inv, "InvoiceSummary")
    _tag(summary, "InvoiceTotal", str(data.get("invoice_total", "")))


# ── 856 Ship Notice ───────────────────────
def _build_856(root, data):
    asn = ET.SubElement(root, "ShipNotice")

    _tag(asn, "ShipmentID",    data.get("shipment_id",    ""))
    _tag(asn, "ShipDate",      data.get("ship_date",      ""))
    _tag(asn, "ShipTime",      data.get("ship_time",      ""))
    _tag(asn, "BOLNumber",     data.get("bol_number",     ""))
    _tag(asn, "POReference",   data.get("po_reference",   ""))
    _tag(asn, "CarrierSCAC",   data.get("carrier_scac",   ""))
    _tag(asn, "Routing",       data.get("routing",        ""))
    _tag(asn, "PackagingCode", data.get("packaging_code", ""))
    _tag(asn, "GrossWeight",   data.get("gross_weight",   ""))

    hl_el = ET.SubElement(asn, "HierarchicalLevels")
    for level in data.get("hl_levels", []):
        hl = ET.SubElement(hl_el, "Level")
        _tag(hl, "ID",     level.get("id",     ""))
        _tag(hl, "Parent", level.get("parent", ""))
        _tag(hl, "Code",   level.get("code",   ""))


# ── 830 Planning Schedule ─────────────────
def _build_830(root, data):
    ps = ET.SubElement(root, "PlanningSchedule")

    _tag(ps, "ReleaseNumber", data.get("release_number", ""))
    _tag(ps, "ScheduleDate",  data.get("schedule_date",  ""))

    buyer = ET.SubElement(ps, "Buyer")
    _tag(buyer, "Name", data.get("buyer", {}).get("name", ""))
    _tag(buyer, "ID",   data.get("buyer", {}).get("id",   ""))

    seller = ET.SubElement(ps, "Seller")
    _tag(seller, "Name", data.get("seller", {}).get("name", ""))
    _tag(seller, "ID",   data.get("seller", {}).get("id",   ""))

    items_el = ET.SubElement(ps, "LineItems")
    for item in data.get("line_items", []):
        item_el = ET.SubElement(items_el, "Item")
        item_el.set("sequence", item.get("line_number", ""))
        _tag(item_el, "UPC",        item.get("upc",         ""))
        _tag(item_el, "VendorItem", item.get("vendor_item", ""))

        forecasts_el = ET.SubElement(item_el, "Forecasts")
        for fc in item.get("forecasts", []):
            fc_el = ET.SubElement(forecasts_el, "Forecast")
            _tag(fc_el, "Quantity",  fc.get("quantity",  ""))
            _tag(fc_el, "Qualifier", fc.get("qualifier", ""))
            _tag(fc_el, "Date",      fc.get("date",      ""))


# ── Validation Summary Block ──────────────
def _build_validation(root, validation_result):
    val = ET.SubElement(root, "ValidationResult")
    _tag(val, "Status",     "VALID" if validation_result["valid"] else "INVALID")
    _tag(val, "ErrorCount", str(len(validation_result["errors"])))

    if validation_result["errors"]:
        errors_el = ET.SubElement(val, "Errors")
        for error in validation_result["errors"]:
            _tag(errors_el, "Error", error)


# ── Helper: create a sub-element with text ─
def _tag(parent, tag, text):
    el      = ET.SubElement(parent, tag)
    el.text = text
    return el


# ── Helper: pretty-print indentation ──────
def _indent(elem, level=0):
    """
    Adds whitespace to XML tree for readable output.
    Python's ET doesn't indent by default.
    """
    indent  = "\n" + "  " * level
    if len(elem):
        elem.text = indent + "  "
        elem.tail = indent
        for child in elem:
            _indent(child, level + 1)
        child.tail = indent
    else:
        elem.tail = indent + "  " if level else "\n"


# ── Helper: generate output filename ──────
def _get_output_filename(data, transaction_code):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Use the key business identifier per transaction type
    identifiers = {
        "850": data.get("po_number",      "unknown"),
        "810": data.get("invoice_number", "unknown"),
        "856": data.get("shipment_id",    "unknown"),
        "830": data.get("release_number", "unknown"),
    }
    identifier = identifiers.get(transaction_code, "unknown")
    return f"{transaction_code}_{identifier}_{timestamp}.xml"