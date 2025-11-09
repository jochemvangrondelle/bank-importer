# Profiling Guide

This guide explains how to use the integrated profiling tools to identify performance bottlenecks in the bank-importer application.

## Overview

The profiling infrastructure includes:

- **Import Time Analysis**: Identify slow module imports using Python's built-in `-X importtime`
- **Function Profiling**: Use `cProfile` to find the slowest functions
- **Flamegraph Visualization**: Use `pyinstrument` for HTML flamegraphs
- **Line-by-Line Profiling**: Use `scalene` for detailed line-level analysis
- **Timeline Visualization**: Use `viztracer` for Chrome-style timeline views

## Quick Start

### Install Profiling Dependencies

```bash
uv sync --group profiling
```

### Profile Import Time

Analyze how long each module takes to import:

```bash
# Profile bank_importer imports
poe profile-import-time

# Or manually:
python -X importtime -c 'import bank_importer' 2>&1 | python scripts/profile_import_time.py
```

This will show:

- Top 50 modules by self time (time spent in the module itself)
- Top 50 modules by cumulative time (including dependencies)
- Time breakdown by package

### Profile Test Execution

Profile all tests to identify slow functions:

```bash
# Profile with cProfile (default)
poe test-profile

# Profile with pyinstrument (flamegraph)
poe test-profile-pyinstrument

# Profile specific test file
pytest tests/banks/test_krungsri_pdf.py --profile
```

Profiles are saved to the `profiles/` directory.

### Profile CLI Commands

Profile specific CLI commands:

```bash
# Profile a CLI command with cProfile
python scripts/profile_cli.py --command "import --help" --tool cprofile

# Profile with pyinstrument (HTML flamegraph)
python scripts/profile_cli.py --command "import file.pdf" --tool pyinstrument

# Profile with scalene (line-by-line)
python scripts/profile_cli.py --command "import file.pdf" --tool scalene

# Profile with viztracer (timeline)
python scripts/profile_cli.py --command "import file.pdf" --tool viztracer
```

### Profile Parsers Specifically

Focus on parser performance:

```bash
poe profile-parsers
```

This runs parser tests with profiling enabled.

## Analyzing Results

### cProfile Output

After running with cProfile, analyze the results:

```bash
python scripts/profile_functions.py profiles/cli_import_help.prof --top-n 50
```

This shows:

- Top 50 functions by cumulative time
- Top 50 functions by self time
- Time breakdown by file

For visual analysis:

```bash
python -m snakeviz profiles/cli_import_help.prof
```

This opens an interactive HTML visualization in your browser.

### PyInstrument Output

PyInstrument generates HTML files directly. Open them in your browser to see:

- Flamegraph showing call hierarchy
- Time spent in each function
- Function call counts

### Scalene Output

Scalene generates HTML reports with:

- Line-by-line CPU time
- Memory usage per line
- GPU usage (if applicable)

### VizTracer Output

View timeline visualizations:

```bash
python -m viztracer --view profiles/cli_import_help.json
```

This opens a Chrome-style timeline view showing:

- Function call timeline
- Call stack depth
- Time spent in each function

## Finding the Top 50 Slowest Functions

### From Test Profiles

After running tests with profiling:

1. Check the summary report:

   ```bash
   cat profiles/summary.txt
   ```

2. Or use the combined profile:
   ```bash
   python scripts/profile_functions.py profiles/combined.prof --top-n 50
   ```

### From CLI Profiles

```bash
python scripts/profile_functions.py profiles/cli_import_help.prof --top-n 50
```

### From Parser Profiles

```bash
# After running profile-parsers
python scripts/profile_functions.py profiles/combined.prof --top-n 50 --sort-by time
```

## Interpreting Results

### High Cumulative Time

Functions with high cumulative time (including called functions) indicate:

- Functions that call many other functions
- Entry points that orchestrate complex operations
- Good candidates for optimization if they're called frequently

### High Self Time

Functions with high self time (excluding called functions) indicate:

- Functions doing heavy computation
- Good candidates for optimization or porting to Rust
- Potential bottlenecks

### Import Time

Slow imports suggest:

- Heavy module-level code execution
- Large dependencies
- Opportunities for lazy loading

## Best Practices

1. **Profile Realistic Workloads**: Use actual data files and commands, not just `--help`

2. **Profile Multiple Times**: Run profiles multiple times and average results to account for variance

3. **Focus on Hot Paths**: Prioritize optimizing functions that:

   - Are called frequently
   - Have high self time
   - Are in critical paths (parsers, CLI)

4. **Compare Before/After**: Keep profile results to compare before and after optimizations

5. **Use Appropriate Tools**:
   - **cProfile**: General function-level profiling
   - **pyinstrument**: Understanding call flow
   - **scalene**: Finding specific slow lines
   - **viztracer**: Understanding timing relationships

## Integration with CI/CD

Profiling can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions step
- name: Profile tests
  run: |
    uv sync --group profiling
    pytest tests/ --profile --profile-tool=cprofile
    python scripts/profile_functions.py profiles/combined.prof --top-n 50 --output profiles/report.txt
```

## Troubleshooting

### Import Errors

If profiling tools aren't found:

```bash
uv sync --group profiling
```

### No Profile Output

Ensure the `profiles/` directory exists and is writable:

```bash
mkdir -p profiles
```

### Slow Profiling

Profiling adds overhead. For very fast operations, results may be less accurate. Consider:

- Profiling longer-running operations
- Using statistical profiling (sampling) instead of deterministic profiling
- Focusing on specific modules/functions

## Next Steps

After identifying slow functions:

1. **Review the code**: Understand what the function does
2. **Check for obvious optimizations**: Look for inefficient algorithms, unnecessary work
3. **Consider alternatives**: Research faster libraries or approaches
4. **Port to Rust**: For critical hot paths, consider Rust implementations
5. **Measure improvements**: Re-profile after changes to verify improvements
