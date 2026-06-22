# ============================================
# edi/validator.py
# Validates EDI file against Walmart specs
# Checks mandatory segments AND field values
# ============================================

import logging
from config import WALMART_MANDATORY_SEGMENTS, WALMART_FIELD_RULES


def validate(content, transaction_code):
    """
    Main validation function.
    Returns a result dict:
    {
        "valid":    True or False,
        "errors":   [ list of error messages ],
        "warnings": [ list of warning messages ],
        "segments_found": [ list of segment tags found in file ]
    }
    """
    result = {
        "valid":          True,
        "errors":         [],
        "warnings":       [],
        "segments_found": []
    }

    try:
        lines = content.strip().split("\n")

        # ── Step 1: Collect all segment tags found in file ──
        for line in lines:
            elements = line.strip().split("*")
            tag = elements[0].strip()
            if tag and tag not in result["segments_found"]:
                result["segments_found"].append(tag)

        logging.info(f"Segments found in file: {result['segments_found']}")

        # ── Step 2: Check mandatory segments ────────────────
        _check_mandatory_segments(result, transaction_code)

        # ── Step 3: Check mandatory field values ────────────
        if result["valid"]:
            # Only check fields if all segments are present
            # No point checking fields inside a missing segment
            _check_mandatory_fields(result, lines, transaction_code)

        # ── Step 4: Final status ─────────────────────────────
        if result["errors"]:
            result["valid"] = False
            logging.warning(f"Validation FAILED — {len(result['errors'])} error(s) found")
        else:
            logging.info("Validation PASSED — all Walmart mandatory checks satisfied")

        return result

    except Exception as e:
        logging.error(f"validator.py failed: {e}")
        result["valid"]  = False
        result["errors"].append(f"Unexpected validation error: {e}")
        return result


def _check_mandatory_segments(result, transaction_code):
    """
    Checks that every required segment tag exists in the file.
    Missing segment → added to errors list.
    """
    required = WALMART_MANDATORY_SEGMENTS.get(transaction_code, [])

    for segment in required:
        if segment not in result["segments_found"]:
            error_msg = (
                f"Missing mandatory segment: {segment} "
                f"(required by Walmart {transaction_code} spec)"
            )
            result["errors"].append(error_msg)
            logging.warning(error_msg)


def _check_mandatory_fields(result, lines, transaction_code):
    """
    For each segment with field rules, checks that
    mandatory element positions are not empty.

    Example: BEG*00*SA*PO-78542**20260620
    Position 3 = PO Number = "PO-78542" ✅
    If position 3 is empty → error
    """
    field_rules = WALMART_FIELD_RULES.get(transaction_code, {})

    for line in lines:
        elements = line.strip().split("*")
        tag      = elements[0].strip()

        if tag in field_rules:
            rules     = field_rules[tag]
            positions = rules["positions"]
            names     = rules["names"]

            for pos, name in zip(positions, names):
                # Check if element exists at this position
                if pos >= len(elements):
                    error_msg = (
                        f"Segment {tag}: missing element at position {pos} "
                        f"({name}) — required by Walmart spec"
                    )
                    result["errors"].append(error_msg)
                    logging.warning(error_msg)

                # Check if element is empty
                elif elements[pos].strip() == "":
                    error_msg = (
                        f"Segment {tag}: empty value at position {pos} "
                        f"({name}) — required by Walmart spec"
                    )
                    result["errors"].append(error_msg)
                    logging.warning(error_msg)


def format_validation_report(transaction_code, result):
    """
    Returns a clean human-readable validation summary.
    Used by the Flask dashboard and logs.
    """
    lines = []
    lines.append("=" * 50)
    lines.append(f"  WALMART EDI VALIDATION REPORT")
    lines.append(f"  Transaction : {transaction_code}")
    lines.append(f"  Status      : {'✅ VALID' if result['valid'] else '❌ INVALID'}")
    lines.append(f"  Errors      : {len(result['errors'])}")
    lines.append(f"  Warnings    : {len(result['warnings'])}")
    lines.append("=" * 50)

    if result["errors"]:
        lines.append("  ERRORS:")
        for i, error in enumerate(result["errors"], 1):
            lines.append(f"  {i}. {error}")

    if result["warnings"]:
        lines.append("  WARNINGS:")
        for warning in result["warnings"]:
            lines.append(f"  - {warning}")

    lines.append("=" * 50)
    return "\n".join(lines)