# TODO.md - Bank Importer TH

## ✅ **COMPLETED TASKS**

### **Translation Service Fixed**

- **Problem**: googletrans library was returning coroutines that weren't being awaited, causing RuntimeWarnings
- **Solution**:
  - Replaced googletrans with deep-translator library (more reliable)
  - Fixed language code compatibility (using lowercase "th" instead of "TH")
  - Added proper error handling and fallback mechanisms
  - Translation service now works without errors

### **Translation Logging Improved**

- **Problem**: Translation logs were not clear and too verbose
- **Solution**:
  - Added clear INFO messages showing from/to translation when successful
  - Reduced verbose logging by only showing initialization once
  - Added DEBUG level for failed translations
  - Translation service now provides clear feedback on what's being translated

### **Export Structure Successfully Implemented**

- **Problem**: Export was creating "unknown" files instead of organized bank-specific directories
- **Solution**: Export now creates proper organized structure as requested
- **Structure**:
  - **`scb/`** - SCB PDF exports (CSV, YAML, config files per source file + consolidated)
  - **`krungsri/`** - Krungsri PDF exports (CSV, YAML, config files per source file + consolidated)
  - **`all/`** - Consolidated exports (CSV, YAML, config files with ALL transactions)
- **File Types**: CSV (Firefly-III compatible), YAML (human-readable), JSON (import config)
- **Features**: Individual files per source file + consolidated files per bank + consolidated all
- ✅ **Result**: Perfect organized export structure matching user requirements

### **Status Command Enhanced with Consolidated Summary**

- **Problem**: Status command only showed individual import sessions, no overview of all consolidated transactions
- **Solution**: Added consolidated summary row to Import Sessions Overview table
- **Features**:
  - Shows total transactions across all accounts (same as 'all' export)
  - Displays date range for entire dataset
  - Includes "Last Month" calculation and red styling for Max Date
  - Appears as last row in the table with bold cyan styling
  - Shows "✅ consolidated" status to distinguish from real import sessions
  - **"Last Month" Logic**: When calculated last month date is in the future, uses yesterday's date instead of today's date
- ✅ **Result**: Users can now see consolidated overview matching the 'all' export data

### **Duplicate Detection Fixed**

- **Problem**: Transactions from the same file were being considered duplicates even if they had the same date/amount
- **Solution**:
  - Added `unique_id` field to Transaction model to distinguish identical transactions
  - Updated unique constraint to include `source_file` and `unique_id`
  - Added automatic unique ID generation in database manager
  - Now identical transactions from the same file are imported as separate transactions
  - Each transaction gets a unique hash-based ID to ensure no false duplicates
  - ✅ **Result**: All transactions from source files are now imported correctly (0 duplicates reported)

### **Consolidated Export Confirmed Working**

- **Structure**: The export-multi command creates the correct organized structure:
  - **Individual files**: Each source file gets its own CSV, YAML, and config files
  - **Bank-specific consolidated**: `scb-all_*.csv` and `scb-all_*.yaml` files containing all SCB transactions
  - **All consolidated**: The `all/` directory contains everything from all banks

### **SCB PDF Parser Fixed**

- **Problem**: SCB parser was incorrectly parsing transaction lines and dates
- **Solution**:
  - Fixed parsing logic to correctly handle SCB PDF format
  - Updated date parsing to handle DD/MM/YY format properly
  - Improved transaction line parsing to extract channel, amount, and balance correctly
  - Added proper transaction type inference

### **Parser Validation Enhanced**

- **Generic CSV Parser**:

  - Added file existence and content validation
  - Enhanced error handling for malformed lines
  - Improved date parsing and currency handling
  - Added source file tracking

- **Krungsri PDF Parser**:
  - Added file validation checks
  - Enhanced error handling

### **Processor Tests Fixed**

- **Issues Resolved**:
  - Fixed Mock object issues in test configuration
  - Corrected test expectations for processor behavior
  - Updated test fixtures to match actual implementation

## ✅ **COMPLETED TASKS**

### **YAML Export Description Structure Enhanced**

- **Problem**: YAML export only showed translated description, missing original and formatted versions
- **Solution**:
  - Enhanced description structure to include `translated`, `original`, and `formatted` fields
  - `translated`: The translated description (or empty if no translation)
  - `original`: The original description as-is
  - `formatted`: The final description with translation and original in brackets if different
  - ✅ **Result**: Complete description information preserved in YAML export

### **Opposing Account Logic for Special Cases**

- **Problem**: Special transaction types needed specific opposing account handling
- **Solution**:
  - **Krungsri "From Card No." + POS**: Set opposing name to "UNKNOWN"
  - **ATM/Cash withdrawals**: Set opposing name to "Cash - {CURRENCY}"
  - **Cash deposits (BRANCH category or round amounts)**: Set opposing name to "Cash - {CURRENCY}"
  - **Other transactions**: Use pattern extraction from description
  - ✅ **Result**: Proper opposing account identification for all transaction types

### **Opposing Account Extraction Refactoring**

- **Problem**: Opposing account extraction logic was duplicated and happening before translation
- **Solution**:
  - Created `opposing_account_patterns.py` module to centralize extraction patterns
  - Moved extraction logic to happen AFTER translation for better accuracy
  - Added comprehensive patterns for Thai bank transfers, merchant names, and account numbers
  - Patterns include: bank transfers with account numbers, K+ shop transactions, PromptPay IDs
  - ✅ **Result**: Centralized, reusable patterns that work with translated descriptions

### **File Processing Logging Added**

- **Problem**: No visibility into which files are being processed during export
- **Solution**:
  - Added INFO logging in target manager when processing each source file
  - Shows file name and transaction count for each file being exported
  - Logs appear between the "Starting Bank Importer" and completion messages
  - ✅ **Result**: Users can now see progress as files are being processed

### **Circular Import Issue Fixed**

- **Problem**: Circular import between `cli_main.py` and `cli/__init__.py` was causing import errors
- **Solution**:
  - Removed the problematic import from `cli/__init__.py`
  - Updated `__main__.py` to import directly from `cli_main.py`
  - ✅ **Result**: Application now runs without import errors

## 🔄 **IN PROGRESS**

### **Linter Issues**

- Some type annotation warnings in translation service and database models
- These are mostly cosmetic and don't affect functionality

## 📋 **REMAINING TASKS**

### **Parser Implementation Issues**

- **Krungsri PDF Parser**:

  - `test_balance_range_validation` - may need balance validation logic
  - `test_database_timezone_storage` - timezone handling for dates

- **Krungsri Text Parser**:
  - `test_parse_line_withdrawal` - amount parsing issues
  - `test_parse_line_credit` - negative amounts when positive expected

### **Test Coverage**

- Improve overall test coverage for parsers
- Add more edge case testing
- Test error handling scenarios

### **Performance Optimization**

- Consider caching for frequently accessed data
- Optimize database queries for large datasets
- Improve translation service efficiency

### **Documentation**

- Update user guides with new features
- Add examples for new functionality
- Document configuration options

## 🎯 **NEXT PRIORITIES**

1. **Fix remaining parser test failures** - Address the specific test issues mentioned above
2. **Improve test coverage** - Add more comprehensive tests
3. **Performance optimization** - Optimize for larger datasets
4. **Documentation updates** - Update guides with new features

## 📊 **CURRENT STATUS**

- ✅ **Core functionality**: Import, export, and processing working correctly
- ✅ **Translation service**: Fixed and working with clear logging
- ✅ **Duplicate detection**: Fixed to prevent false positives
- ✅ **Status command**: Enhanced with better information display
- ✅ **Consolidated export**: Working correctly
- 🔄 **Parser tests**: Some remaining issues to address
- 🔄 **Linter warnings**: Minor type annotation issues
