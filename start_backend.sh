#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
[[ -x .venv-backend-cpu/bin/python ]] || { echo 'Run bash install_backend.sh first.'; exit 1; }
exec .venv-backend-cpu/bin/python scripts/install_backend.py --start-only
