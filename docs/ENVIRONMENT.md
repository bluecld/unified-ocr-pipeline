# Unified OCR Pipeline - Environment Setup

## Python Environment
- Recommended: Python 3.10+
- Install dependencies:

```bash
pip install -r requirements.txt
```

## Docker Environment
- Build and run with Docker Compose:

```bash
docker-compose build
docker-compose up -d
```

## Environment Variables
- Copy `.env.example` to `.env` and fill in your values.
- Key variables:
  - `FM_ENABLED`, `FM_HOST`, `FM_DB`, `FM_USERNAME`, `FM_PASSWORD`
  - `OCR_LOG_LEVEL`, `OCR_TIMEOUT`, etc.

## Updating Dependencies
- To add new Python packages:

```bash
pip install <package>
pip freeze > requirements.txt
```
