# el_stripper

A small CLI utility that strips comments (and optionally docstrings) from Python files in-place, using a CST-based transformer for safe, syntax-aware edits.

## Usage

```bash
# Strip comments from a single file
el_stripper path/to/file.py

# Strip comments from all .py files in a directory
el_stripper path/to/project/

# Also strip docstrings
el_stripper path/to/project/ --doc
```

Files and directories listed in `.gitignore` (as well as common noise dirs like `.venv`, `__pycache__`, `.git`) are automatically skipped.

---

## Installation

### Option 1 — Pre-built binary
Download the binary for your platform from [Releases](../../releases).

**macOS** (`el_stripper-macos-arm64`)
```bash
# Remove macOS quarantine, rename, and install to PATH
xattr -d com.apple.quarantine el_stripper-macos-arm64
chmod +x el_stripper-macos-arm64
mv el_stripper-macos-arm64 "${XDG_BIN_HOME:-$HOME/.local/bin}/el_stripper"
```

> Make sure `~/.local/bin` is on your `PATH` (add `export PATH="$HOME/.local/bin:$PATH"` to your shell rc if needed).

**Linux** (`el_stripper-linux-x86_64`)
```bash
chmod +x el_stripper-linux-x86_64
mv el_stripper-linux-x86_64 "${XDG_BIN_HOME:-$HOME/.local/bin}/el_stripper"
```

**Windows** (`el_stripper-windows-amd64.exe`)
```powershell
$dest = "$env:LOCALAPPDATA\Programs\bin"
Move-Item el_stripper-windows-amd64.exe "$dest\el_stripper.exe"
```

> Add `$dest` to your user `PATH` if not already present (`[Environment]::SetEnvironmentVariable("PATH", "$env:PATH;$dest", "User"`)

### Option 2 — Build from source

**Prerequisites:** Python 3.10+, a C compiler, and [Nuitka](https://nuitka.net/).

```bash
# 1. Clone the repo
git clone https://github.com/your-username/el_stripper.git
cd el_stripper

# 2. Create a virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install libcst pathspec nuitka

# 3. Compile
bash compile.bash
```

The standalone binary is written to `dist/el_stripper.bin`.
