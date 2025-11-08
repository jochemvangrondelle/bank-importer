# Profiling Summary Report

Generated: $(date)

## Overview

This report summarizes profiling results from multiple profiling tools to identify performance bottlenecks in the bank-importer application.

## 1. Import Time Analysis

### Summary

- **Total modules imported**: 68
- **Total import time**: 126.31 ms
- **Total self time**: 38.19 ms
- **Total dependency time**: 88.12 ms

### Key Findings

#### Top Slow Imports (Self Time)

1. `site` - 5.57 ms (Python site module initialization)
2. `encodings` - 4.01 ms (Encoding system)
3. `__editable___firefly_iii_api_client_6_2_21_0_finder` - 1.39 ms (Firefly client editable install)
4. `ipaddress` - 1.34 ms
5. `collections` - 1.18 ms

#### Top Slow Imports (Cumulative Time)

1. `site` - 29.48 ms (includes all site-packages initialization)
2. `__editable___firefly_iii_api_client_6_2_21_0_finder` - 21.24 ms (Firefly client)
3. `pathlib` - 8.68 ms
4. `importlib.util` - 8.53 ms
5. `contextlib` - 6.42 ms

### Recommendations

- **Firefly client**: The editable install finder adds 21ms to imports. Consider using a regular install or lazy loading.
- **bank_importer itself**: Only 195µs self time - very fast!
- Most time is in Python standard library initialization, which is expected.

## 2. CLI Command Profiling

### CLI Help Command (`--help`)

Profile saved: `profiles/cli_help.prof`

Key functions to analyze:

- CLI initialization
- Command parsing
- Help text generation

### CLI Import Command (`import --help`)

Profile saved: `profiles/cli_import.prof`

Key functions to analyze:

- Import command setup
- Parser discovery
- Configuration loading

## 3. Test Profiling

### Parser Tests

Focus areas:

- PDF parsing operations
- Text processing
- Transaction extraction
- Database operations

## 4. PyInstrument Flamegraphs

HTML flamegraphs generated:

- `profiles/cli_pyinstrument.html` - CLI help command flamegraph

Open in browser to visualize call hierarchy and time distribution.

## 5. Next Steps

1. **Analyze specific profiles**:

   ```bash
   python scripts/profile_functions.py profiles/cli_help.prof --top-n 50
   python scripts/profile_functions.py profiles/cli_import.prof --top-n 50
   ```

2. **View flamegraphs**:

   ```bash
   open profiles/cli_pyinstrument.html
   ```

3. **Profile real operations**:

   ```bash
   python scripts/profile_cli.py --command "import tests/data/krungsri_valid.pdf" --tool cprofile
   ```

4. **Profile with scalene** (line-by-line):
   ```bash
   python scripts/profile_cli.py --command "import tests/data/krungsri_valid.pdf" --tool scalene
   ```

## 6. Performance Optimization Opportunities

Based on initial profiling:

1. **Import Time**:

   - Firefly client editable install adds overhead
   - Consider lazy loading for optional dependencies

2. **Parser Performance**:

   - Focus profiling on actual PDF/text parsing operations
   - Profile with real data files, not just help commands

3. **Database Operations**:

   - Profile transaction insertion and query operations
   - Check for N+1 query patterns

4. **Translation Service**:
   - Profile translation operations with real Thai text
   - Check API call overhead

## 7. Profiling Tools Used

- ✅ **cProfile**: Function-level profiling
- ✅ **pyinstrument**: HTML flamegraphs
- ✅ **Import time analysis**: Python -X importtime
- ⏳ **scalene**: Line-by-line profiling (run with real data)
- ⏳ **viztracer**: Timeline visualization (run with real data)

## Notes

- Initial profiling focused on CLI initialization and help commands
- For meaningful results, profile with actual data files and operations
- Combine multiple profiling tools for comprehensive analysis
- Focus on hot paths identified in cumulative time analysis
