
import cv2
import pytesseract
from pdf2image import convert_from_path
import numpy as np
import tempfile
import os

def extract_text_ocr_page1(pdf_path: str, dpi: int = 400) -> str:
    """Extract OCR text from the first page of a scanned PDF with image preprocessing."""
    try:
        # Convert page 1 to image
        images = convert_from_path(pdf_path, dpi=dpi, first_page=1, last_page=1)
        if not images:
            return ""

        img = np.array(images[0])

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

        # Apply threshold to clean background noise
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Optionally: dilate or erode to clean small text artifacts
        kernel = np.ones((1, 1), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

        # OCR with custom config
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(cleaned, config=custom_config)

        return text.strip()

    except Exception as e:
        print(f"OCR failed on {pdf_path}: {e}")
        return ""
