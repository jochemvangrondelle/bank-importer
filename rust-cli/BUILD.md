# Building the Rust CLI

## Quick Start

```bash
cd rust-cli
cargo build --release
```

The binary will be at `target/release/bank-importer-cli`.

## Requirements

1. **Rust**: Install via [rustup](https://rustup.rs/)

   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   ```

2. **Python 3.11+**: The Python interpreter must be available

   - PyO3 will automatically find and embed Python
   - Ensure Python development headers are installed:
     - macOS: `brew install python3`
     - Ubuntu/Debian: `sudo apt-get install python3-dev`
     - Fedora: `sudo dnf install python3-devel`

3. **Bank Importer Python Package**: The Python code must be importable
   - The Rust CLI automatically adds `src/` to Python's path
   - Ensure you're building from the project root

## Development

```bash
# Build debug version
cargo build

# Run tests (if any)
cargo test

# Run with cargo
cargo run -- status

# Format code
cargo fmt

# Check for issues
cargo clippy
```

## Release Build

```bash
# Optimized release build
cargo build --release

# The binary is at:
# - Linux/macOS: target/release/bank-importer-cli
# - Windows: target/release/bank-importer-cli.exe
```

## Troubleshooting

### Python Not Found

If PyO3 can't find Python, set the `PYTHON_SYS_EXECUTABLE` environment variable:

```bash
export PYTHON_SYS_EXECUTABLE=/usr/bin/python3
cargo build --release
```

### Import Errors

If you get import errors when running the binary:

1. Ensure you're running from the project root
2. Check that `src/bank_importer/` exists
3. Verify Python can import the module:
   ```bash
   python3 -c "import sys; sys.path.insert(0, 'src'); import bank_importer"
   ```

### Cross-Compilation

For cross-compilation, you'll need to set up Python for the target platform. PyO3 supports cross-compilation but requires additional setup.

## Distribution

The compiled binary embeds Python, so it:

- Requires Python libraries to be available at runtime
- Is not fully standalone (depends on Python runtime)
- Can be distributed as a single binary (but Python must be installed)

For a fully standalone binary, consider using tools like:

- [PyInstaller](https://pyinstaller.org/) (for Python)
- [maturin](https://maturin.rs/) (for Rust-Python projects)
