import re
import sys
import json

def extract_fields(text):
    data = {}

    # PO Number (starts with 45, 10 digits)
    po_match = re.search(r'\b(45\d{8})\b', text)
    if po_match:
        data["PO Number"] = po_match.group(1)

    # MJO NO (8+ digits, appears after Part)
    # MJO NO: Find after PART NUMBER line
    mjo_match = re.search(r'\bOP\d+\s+ASSEMBLY\s+(\d{8,})', text, re.IGNORECASE)
    if mjo_match:
        data["MJO NO"] = mjo_match.group(1)

    # QTY SHIP (decimal number before EA)
    qty_match = re.search(r'Delivery Date.*?(\d{1,5}\.\d{2})', text, re.DOTALL)
    if qty_match:
        data["QTY SHIP"] = qty_match.group(1)

    # PART NUMBER (e.g. 139038-2SA OP20 -> 139038-2SA*OP20)
    part_match = re.search(r'\b(\d{6,}-\w+)\s+(OP\d+)', text)
    if part_match:
        part = f"{part_match.group(1)}*{part_match.group(2)}"
        data["PART NUMBER"] = part

    # Delivery Date after EA or Dock Date
    date_match = re.search(r'EA\s+(\d{2}/\d{2}/\d{4})', text)
    if date_match:
        data["Promise Delivery Date"] = date_match.group(1)

    # Whittaker Shipper = same as PO
    if "PO Number" in data:
        data["Whittaker Shipper"] = data["PO Number"]

    # DPAS Rating
    dpas_match = re.findall(r'DPAS Rating[:\-]?\s*(\w+)', text, re.IGNORECASE)
    if dpas_match:
        data["DPAS Rating"] = dpas_match[0]

    # Payment Terms
    terms_match = re.search(r'Payment Terms[:\-]?\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
    if terms_match:
        terms = terms_match.group(1).strip()
        if "Ship via" not in terms:  # avoid miscapture
            data["Payment Terms"] = terms
            if '30 Days' not in terms:
                data["NonStandardTerms"] = True

    # Quality Clauses
    qcodes = re.findall(r'\bQ(\d{1,3})\b', text)
    quality_clauses = sorted(set(f"Q{q}" for q in qcodes))
    data["Quality Clauses"] = quality_clauses

    # Reference matches for notes
    known_q = {
        "Q1": "Q1 QUALITY SYSTEMS REQUIREMENTS",
        "Q2": "Q2 SURVEILLANCE BY MEGGITT AND RIGHT OF ENTRY",
        "Q5": "Q5 CERTIFICATION OF CONFORMANCE AND RECORD RETENTION",
        "Q9": "Q9 CORRECTIVE ACTION",
        "Q13": "Q13 REPORT OF DISCREPANCY # Quality Notification (QN)",
        "Q14": "Q14 FOREIGN OBJECT DAMAGE (FOD)",
        "Q15": "Q15 ANTI-TERRORIST POLICY",
        "Q26": "Q26 PACKING FOR SHIPMENT",
        "Q32": "Q32 FLOWDOWN OF REQUIREMENTS [QUALITY AND ENVIRONMENTAL]",
        "Q33": "Q33 FAR and DOD FAR SUPPLEMENTAL FLOWDOWN PROVISIONS"
    }
    notes = {}
    for q in quality_clauses:
        if q in known_q:
            notes[q] = known_q[q]
    if notes:
        data["Notes"] = notes

    return data

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python extract_fields.py ocr_pdf output_json")
        sys.exit(1)

    from pathlib import Path
    import ocrmypdf

    ocr_pdf = Path(sys.argv[1])
    txt_file = ocr_pdf.with_suffix('.txt')

    # Re-OCR with sidecar text
    ocrmypdf.ocr(str(ocr_pdf), "/dev/null", force_ocr=True, sidecar=str(txt_file))

    with open(txt_file, "r") as f:
        text = f.read()

    fields = extract_fields(text)

    with open(sys.argv[2], "w") as out:
        json.dump(fields, out, indent=2)
