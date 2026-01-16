#!/bin/bash
set -e
echo "Running coverage check..."
pytest --cov=configurator --cov-report=term-missing --cov-report=html --cov-fail-under=90
