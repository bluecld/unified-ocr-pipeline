#!/bin/bash

set -e

INPUT="$1"
if [[ -z "$INPUT" ]]; then
  echo "Usage: dev_test_runner.sh /full/path/to/input.pdf"
  exit 1
fi

PO_OUT="${INPUT%.pdf}_PO.pdf"
ROUTER_OUT="${INPUT%.pdf}_ROUTER.pdf"

echo "[INFO] Splitting PDF: $INPUT"
echo "[INFO] PO will be saved to: $PO_OUT"
echo "[INFO] Router will be saved to: $ROUTER_OUT"

python3 /app/split_po_router_basic.py "$INPUT" "$PO_OUT" "$ROUTER_OUT"

if [[ $? -eq 0 ]]; then
  echo "[SUCCESS] Split completed: $(basename "$INPUT")" >> /app/logs/dev_test_runner.log
else
  echo "[ERROR] Split failed for: $(basename "$INPUT")" >> /app/logs/dev_test_runner.log
fi

PO_OCR="${PO_OUT%.pdf}_OCR.pdf"
ROUTER_OCR="${ROUTER_OUT%.pdf}_OCR.pdf"

echo "[INFO] Running OCR on PO (all pages)"
ocrmypdf --force-ocr "$PO_OUT" "$PO_OCR"

if [ -f "$ROUTER_OUT" ]; then
  echo "[INFO] Running OCR on first page of Router"
  TMP_ROUTER="/tmp/router_page1.pdf"
  TMP_ROUTER_OCR="/tmp/router_page1_ocr.pdf"

  python3 - <<EOF
import fitz
doc = fitz.open("$ROUTER_OUT")
if len(doc) > 0:
    first_page_doc = fitz.open()
    first_page_doc.insert_pdf(doc, from_page=0, to_page=0)
    first_page_doc.save("$TMP_ROUTER")
EOF

  ocrmypdf --force-ocr "$TMP_ROUTER" "$TMP_ROUTER_OCR"
  mv "$TMP_ROUTER_OCR" "$ROUTER_OCR"
  echo "[INFO] Saved Router OCR (1st page) to: $ROUTER_OCR"
else
  echo "[INFO] No Router file found to OCR"
fi
