#!/bin/sh

# Build without cache and start the ocr_oneshot service
docker-compose build --no-cache
docker-compose up ocr_oneshot