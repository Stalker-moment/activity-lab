#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
echo 'Activity Lab CPU backend: uv / Python 3.12 / dependencies / checkpoints.'
echo 'First installation needs Internet. Existing .env is preserved.'
if ! command -v uv >/dev/null 2>&1 && [[ ! -x "$HOME/.local/bin/uv" ]]; then
  command -v curl >/dev/null 2>&1 || { echo 'Install curl first (Ubuntu/Debian: sudo apt-get install curl).'; exit 1; }
  echo 'Installing uv from official https://astral.sh/uv/install.sh'
  curl --proto '=https' --tlsv1.2 -LsSf https://astral.sh/uv/install.sh | sh
fi
if command -v uv >/dev/null 2>&1; then activity_uv="$(command -v uv)"; else activity_uv="$HOME/.local/bin/uv"; fi
# MediaPipe/OpenCV need system shared libraries; install only on apt-based hosts.
if command -v apt-get >/dev/null 2>&1; then
  installed() { [[ "$(dpkg-query -W -f='${Status}' "$1" 2>/dev/null || true)" == 'install ok installed' ]]; }
  if installed libgl1 && { installed libglib2.0-0 || installed libglib2.0-0t64; }; then
    :
  else
    echo 'Installing system OpenCV/MediaPipe libraries (sudo may ask for password).'
    activity_sudo=()
    if [[ "$EUID" -ne 0 ]]; then
      command -v sudo >/dev/null 2>&1 || { echo 'Administrator must install libgl1 and GLib first.'; exit 1; }
      activity_sudo=(sudo)
    fi
    "${activity_sudo[@]}" apt-get update
    activity_glib=libglib2.0-0
    if apt-cache show libglib2.0-0t64 >/dev/null 2>&1; then activity_glib=libglib2.0-0t64; fi
    "${activity_sudo[@]}" apt-get install -y libgl1 "$activity_glib"
  fi
fi
exec "$activity_uv" run --no-project --python 3.12 python scripts/install_backend.py --uv "$activity_uv" "$@"
