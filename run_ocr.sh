#!/bin/sh
docker-compose build --no-cache
docker-compose --profile oneshot up