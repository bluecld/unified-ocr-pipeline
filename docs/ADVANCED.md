# Unified OCR Pipeline - Advanced Documentation

## Architecture Overview
- Modular pipeline for PDF splitting, OCR, field extraction, and FileMaker integration.
- Docker-based deployment for reliability and portability.

## API Reference
- Main entry: `scripts/unified_ocr_pipeline.py`
- Field extraction: `scripts/extract_fields.py`
- PDF splitting: `scripts/split_po_router_basic.py`, `scripts/enhanced_pdf_splitter.py`, `scripts/improved_pdf_splitting.py`

## Customization
- Add new regex patterns in `extract_fields.py` for custom fields.
- Extend business logic in `unified_ocr_pipeline.py`.
- Update Docker Compose for new services.

## Troubleshooting
- See README.md for common issues.
- For advanced debugging, check logs in `logs/` and error folders in `OCR_PROCESSED/`.

## Contact
- For support, open an issue or contact the maintainer listed in README.md.
