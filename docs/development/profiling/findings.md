# Profiling Findings Summary

**Date**: November 8, 2025  
**Profiling Tools Used**: cProfile, Python -X importtime, pyinstrument

## Executive Summary

Profiling analysis identified several performance bottlenecks, with the most significant being:

1. **Language enum generation** (109ms) - Dynamic enum creation from pycountry
2. **SQLModel imports** (1.1s) - Heavy ORM initialization
3. **Firefly client editable install** (21ms) - Import overhead
4. **Module import chain** (1.7s total for CLI import command)

## 1. Import Time Analysis

### Overall Statistics

- **Total modules imported**: 68
- **Total import time**: 126.31 ms
- **Self time**: 38.19 ms
- **Dependency time**: 88.12 ms

### Top Bottlenecks

#### By Cumulative Time (Including Dependencies)

1. **`site`** - 29.48 ms (Python site-packages initialization)
2. **`__editable___firefly_iii_api_client_6_2_21_0_finder`** - 21.24 ms ⚠️
   - **Issue**: Editable install finder adds significant overhead
   - **Recommendation**: Use regular install or lazy load Firefly client
3. **`pathlib`** - 8.68 ms
4. **`importlib.util`** - 8.53 ms
5. **`contextlib`** - 6.42 ms

#### By Self Time (Module Execution)

1. **`site`** - 5.57 ms
2. **`encodings`** - 4.01 ms
3. **`__editable___firefly_iii_api_client_6_2_21_0_finder`** - 1.39 ms
4. **`ipaddress`** - 1.34 ms
5. **`collections`** - 1.18 ms

### Key Finding: bank_importer Module

- **Self time**: Only 195µs - **excellent!**
- The main package itself is very fast to import
- Most overhead is from dependencies

## 2. CLI Command Profiling

### CLI Help Command (`--help`)

- **Total time**: 0.0009 seconds (0.9ms)
- **Function calls**: 574
- **Status**: ✅ Very fast, no issues

### CLI Import Command (`import --help`)

- **Total time**: 1.722 seconds ⚠️
- **Function calls**: 871,070
- **Primitive calls**: 852,657

#### Top Time Consumers

1. **Module Import Chain** (1.723s cumulative)

   - `bank_importer/__init__.py` - 1.721s
   - `bank_importer/banks/__init__.py` - 1.597s
   - `bank_importer/banks/amex_th_csv.py` - 1.470s
   - `bank_importer/interfaces/parser.py` - 1.334s
   - `bank_importer/models/bank_account.py` - 1.141s

2. **SQLModel Initialization** (1.131s) ⚠️

   - `sqlmodel/__init__.py` - 1.131s
   - `sqlmodel/main.py` - 0.588s
   - **Issue**: Heavy ORM initialization
   - **Recommendation**: Consider lazy loading or alternative ORM

3. **Language Enum Generation** (0.109s) 🔥 **HOT SPOT**

   - `bank_importer/models/enums.py:201(_get_all_language_codes)` - 0.109s
   - **Issue**: Dynamically generating enum from pycountry on every import
   - **Impact**: 109ms added to every import
   - **Recommendation**:
     - Cache the enum generation
     - Use a pre-generated enum
     - Lazy load language codes

4. **Other Notable Imports**
   - `bank_importer/models/database.py` - 0.171s
   - `bank_importer/banks/krungsri_pdf.py` - 0.123s
   - `bank_importer/translation_service.py` - 0.075s
   - `bank_importer/logging_config.py` - 0.055s

## 3. Top 50 Slowest Functions (CLI Import Command)

### By Cumulative Time

1. **`builtins.exec`** - 1.723s (entry point)
2. **`importlib._bootstrap._find_and_load`** - 1.723s (module loading)
3. **`importlib._bootstrap._find_and_load_unlocked`** - 1.723s
4. **`builtins.__import__`** - 1.723s
5. **`importlib._bootstrap._load_unlocked`** - 1.722s
6. **`importlib._bootstrap_external.exec_module`** - 1.722s
7. **`bank_importer/__init__.py`** - 1.721s
8. **`bank_importer/banks/__init__.py`** - 1.597s
9. **`bank_importer/banks/amex_th_csv.py`** - 1.470s
10. **`bank_importer/interfaces/parser.py`** - 1.334s

### By Self Time (Actual Work)

1. **`_get_all_language_codes()`** - 0.109s 🔥
   - Location: `bank_importer/models/enums.py:201`
   - **Critical**: This runs on every import!
2. **`builtins.__build_class__`** - 0.594s

   - Class definition overhead (expected)

3. **`importlib._bootstrap._handle_fromlist`** - 0.795s
   - Module import handling

## 4. Critical Performance Issues

### 🔥 Priority 1: Language Enum Generation (109ms)

**Location**: `src/bank_importer/models/enums.py:201`

**Problem**:

- `_get_all_language_codes()` is called during module import
- Iterates through all pycountry languages
- Creates enum dynamically on every import
- Adds 109ms to every import

**Impact**:

- 109ms × number of imports = significant overhead
- Affects CLI startup, API startup, test execution

**Solutions**:

1. **Cache the result** (recommended)

   ```python
   _language_codes_cache = None

   def _get_all_language_codes():
       global _language_codes_cache
       if _language_codes_cache is None:
           _language_codes_cache = _generate_language_codes()
       return _language_codes_cache
   ```

2. **Pre-generate enum** at build time
3. **Lazy load** - only generate when Language enum is first accessed
4. **Use a static enum** with common languages, fallback to dynamic

**Expected Improvement**: ~100ms faster imports

### ⚠️ Priority 2: SQLModel Import (1.1s)

**Location**: `sqlmodel/__init__.py` and `sqlmodel/main.py`

**Problem**:

- Heavy ORM initialization
- 1.1 seconds of import time
- Affects all database operations

**Impact**:

- Slow CLI startup
- Slow API startup
- Slow test execution

**Solutions**:

1. **Lazy import** - only import SQLModel when database is actually used
2. **Consider alternatives** - lighter ORMs or raw SQLAlchemy
3. **Module-level optimization** - check if SQLModel can be optimized

**Expected Improvement**: ~1s faster imports (if lazy loaded)

### ⚠️ Priority 3: Firefly Client Editable Install (21ms)

**Location**: `__editable___firefly_iii_api_client_6_2_21_0_finder`

**Problem**:

- Editable install adds finder overhead
- 21ms on every import

**Solutions**:

1. **Use regular install** instead of editable
2. **Lazy load** Firefly client only when needed
3. **Make Firefly client optional** - only import when actually used

**Expected Improvement**: ~20ms faster imports

## 5. Module Import Chain Analysis

The import chain shows:

1. `bank_importer/__init__.py` imports everything (1.7s)
2. This triggers imports of all submodules
3. Each submodule imports its dependencies
4. SQLModel and Language enum are the biggest contributors

**Recommendation**: Consider lazy imports for:

- Parser modules (only import when needed)
- Database models (only import when database is used)
- Translation service (only import when translation is needed)

## 6. Recommendations Summary

### Immediate Actions (High Impact, Low Effort)

1. **Cache Language Enum Generation** ⭐

   - Impact: ~100ms faster imports
   - Effort: Low (add caching)
   - Priority: **HIGH**

2. **Lazy Load SQLModel**

   - Impact: ~1s faster imports
   - Effort: Medium (refactor imports)
   - Priority: **HIGH**

3. **Lazy Load Firefly Client**
   - Impact: ~20ms faster imports
   - Effort: Low (conditional import)
   - Priority: **MEDIUM**

### Medium-Term Actions

4. **Lazy Load Parser Modules**

   - Only import parsers when actually needed
   - Impact: Faster startup, especially for CLI

5. **Optimize Module Imports**
   - Review `__init__.py` files
   - Use `__all__` to control what's imported
   - Consider splitting large modules

### Long-Term Considerations

6. **Consider Rust for Hot Paths**

   - Language enum generation (if still slow after caching)
   - PDF parsing operations (profile with real data)
   - Database operations (profile with real queries)

7. **Alternative Libraries**
   - Consider lighter ORM alternatives
   - Evaluate PDF parsing libraries (PyMuPDF vs pdfplumber)

## 7. Next Profiling Steps

To get more actionable data:

1. **Profile Real Operations**:

   ```bash
   python scripts/profile_cli.py --command "import tests/data/krungsri_valid.pdf" --tool cprofile
   ```

2. **Profile Parser Operations**:

   ```bash
   pytest tests/banks/ --profile --profile-tool=cprofile -p no:xdist -v
   ```

3. **Profile with Real Data Files**:

   - Use actual PDF files, not just help commands
   - Profile end-to-end import operations
   - Profile translation operations

4. **Line-by-Line Profiling**:
   ```bash
   python scripts/profile_cli.py --command "import file.pdf" --tool scalene
   ```

## 8. Performance Targets

Based on profiling:

- **Current import time**: ~1.7s (CLI import command)
- **Target import time**: <500ms
- **Potential improvement**: ~1.2s (70% reduction)

**Breakdown**:

- Language enum caching: -100ms
- SQLModel lazy load: -1100ms
- Firefly client lazy load: -20ms
- Other optimizations: -80ms

## 9. Files Generated

- `profiles/cli_help.prof` - CLI help command profile
- `profiles/cli_import.prof` - CLI import command profile
- `profiles/cli_help.html` - Snakeviz visualization (if generated)
- `profiles/cli_import.html` - Snakeviz visualization (if generated)
- `profiles/cli_pyinstrument.html` - PyInstrument flamegraph

## 10. Conclusion

The profiling revealed that **import time is the primary bottleneck**, not runtime execution. The main culprits are:

1. **Language enum generation** (109ms) - Easy fix with caching
2. **SQLModel initialization** (1.1s) - Can be lazy loaded
3. **Firefly client** (21ms) - Can be lazy loaded

Addressing these three issues could reduce import time by **~1.2 seconds (70% improvement)**.

For runtime performance, additional profiling with real data files is needed to identify hot paths in:

- PDF parsing
- Text processing
- Database operations
- Translation service
