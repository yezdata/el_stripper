set -euo pipefail

OUTPUT_DIR="dist"
mkdir -p "$OUTPUT_DIR"

if [ -f ".venv/Scripts/python.exe" ]; then
    VENV_PYTHON=".venv/Scripts/python.exe"
else
    VENV_PYTHON=".venv/bin/python"
fi

"$VENV_PYTHON" -m nuitka \
    --standalone \
    --onefile \
    --enable-plugin=anti-bloat \
    --assume-yes-for-downloads \
    --output-dir="$OUTPUT_DIR" \
    el_stripper.py
