#!/bin/bash
set -euo pipefail

cd backend
ruff format app tests scripts
ruff check --fix app tests scripts
mypy --config-file mypy.ini
