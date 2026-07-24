#!/bin/bash
set -e
echo "Starting Image Accuracy Finder on port ${PORT:-5000}"
exec gunicorn app:app --bind 0.0.0.0:${PORT:-5000} --access-logfile -
