set -euo pipefail

OUTPUT_DIR="dist"
mkdir -p "$OUTPUT_DIR"

uv venv --isolated --python 3.12

source ".venv/bin/activate"

uv pip install \
    "Nuitka[onefile]" \
    "libcst" \
    "pathspec" \

python -m nuitka \
    --standalone \
    --onefile \
    --enable-plugin=anti-bloat \
    --output-dir="$OUTPUT_DIR" \
    --report=report.xml \
    el_stripper.py
