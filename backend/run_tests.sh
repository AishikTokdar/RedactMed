#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Running Agent tests..."
cd "$SCRIPT_DIR/agent" && uv run pytest tests/ -v

echo -e "\nRunning Deidentification tests..."
cd "$SCRIPT_DIR/deidentification" && uv run pytest tests/ -v

echo -e "\nRunning Lambda API tests..."
cd "$SCRIPT_DIR/lambda/api" && uv run pytest tests/ -v

echo -e "\nRunning Lambda Ingestion tests..."
cd "$SCRIPT_DIR/lambda/ingestion" && uv run pytest tests/ -v

echo -e "\nRunning Lambda Worker tests..."
cd "$SCRIPT_DIR/lambda/worker" && uv run pytest tests/ -v

echo -e "\nAll tests passed!"
