#!/usr/bin/env bash
# Run after moving the project folder — recreates venv with correct paths.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"

echo "Project root: $ROOT"
echo "Removing old virtualenv (if any)..."
rm -rf venv

echo "Creating fresh virtualenv..."
python3 -m venv venv
source venv/bin/activate

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Done. Start backend with: ./scripts/start-backend.sh"
