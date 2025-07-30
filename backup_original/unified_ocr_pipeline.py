import os
import fitz
import subprocess
import logging
import re

logging.basicConfig(
    filename="/mnt/logs/pipeline.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def split_po_router(input_pdf, po_pdf, router_pdf):
    doc = fitz.open(input_pdf)
    po_doc = fitz.open()
    router_doc = fitz.open()

    for i, page in enumerate(doc):
        if page.rect.width < page.rect.height:
            po_doc.insert_pdf(doc, from_page=i, to_page=i)
        else:
            break

    if po_doc.page_count > 0:
        po_doc.save(po_pdf)
    if i < len(doc):
        for j in range(i, len(doc)):
            router_doc.insert_pdf(doc, from_page=j, to_page=j)
        router_doc.save(router_pdf)

def extract_po_number_from_first_page(po_pdf_path):
    # Only OCR the FIRST page of the PO PDF
    page1 = "/tmp/po_page1.pdf"
    ocr1 = "/tmp/po_page1_ocr.pdf"

    # Extract first page only
    subprocess.run(["qpdf", po_pdf_path, "--pages", ".", "1", "--", page1], check=True)

    # OCR just that one page
    subprocess.run([
        "ocrmypdf", "--force-ocr", "--rotate-pages", "--tesseract-timeout", "10",
        page1, ocr1
    ], check=True)

    # Extract PO number
    result = subprocess.run(["pdftotext", ocr1, "-"], stdout=subprocess.PIPE, text=True)
    match = re.search(r'4551\d{6}', result.stdout)
    if match:
        return match.group(0)
    else:
        logging.error(f"❌ Could not extract PO from {po_pdf_path}")
        return None

def run_ocr(full_pdf, output_pdf):
    if not os.path.exists(full_pdf):
        return
    subprocess.run([
        "ocrmypdf", "--force-ocr", "--rotate-pages", "--tesseract-timeout", "10",
        full_pdf, output_pdf
    ], check=True)

def main():
    in_dir = "/mnt/incoming"
    out_dir = "/mnt/processed"
    for fname in os.listdir(in_dir):
        if not fname.lower().endswith(".pdf"):
            continue

        logging.info(f"🔍 Processing: {fname}")
        in_path = os.path.join(in_dir, fname)
        tmp_po = os.path.join(out_dir, "_tmp_po.pdf")
        tmp_router = os.path.join(out_dir, "_tmp_router.pdf")

        # Split input PDF
        split_po_router(in_path, tmp_po, tmp_router)

        # OCR only page 1 to extract PO number
        po_number = extract_po_number_from_first_page(tmp_po)
        if not po_number:
            continue

        # Rename files based on extracted PO
        final_po = os.path.join(out_dir, f"{po_number}_PO.pdf")
        final_router = os.path.join(out_dir, f"{po_number}_ROUTER.pdf")
        os.rename(tmp_po, final_po)
        os.rename(tmp_router, final_router)

        logging.info(f"✅ Renamed outputs with PO: {po_number}")

if __name__ == "__main__":
    logging.info("=== Unified OCR Pipeline Starting ===")
    main()
