#!/bin/bash
set -e
echo "Validating build..."
# Ensure build tools are installed
pip install --quiet build twine
# Clean previous builds
rm -rf dist/ build/ *.egg-info
# Build
python3 -m build
# Validate
twine check dist/*
echo "Build valid."
