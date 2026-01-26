#!/bin/bash
set -euo pipefail

VENV_DIR=".venv"

echo "Running all tests..."

if [ ! -d "$VENV_DIR" ]; then
	echo "Creating virtual environment..."
	python3 -m venv "$VENV_DIR"
fi

echo "Activating virtual environment..."
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "Installing development dependencies..."
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements-dev.txt

pytest tests/
