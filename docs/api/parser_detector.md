# Parser Detector

The `ParserDetector` class automatically determines the best parser for a given file.

## Overview

The parser detector analyzes files using multiple strategies:

1. **File Extension Matching**: Filters parsers by supported file extensions
2. **Filename Pattern Matching**: Uses parser-defined filename patterns
3. **Parent Folder Hints**: Prioritizes parsers based on folder names (e.g., "SCB", "Krungsri")
4. **Content Validation**: Validates file content to ensure parser compatibility

## Usage

```python
from bank_importer import detect_parser
from pathlib import Path

# Detect parser for a file
parser_name = detect_parser(Path("statement.pdf"))
if parser_name:
    print(f"Detected parser: {parser_name}")
```

## Reference

::: bank_importer.parser_detector.ParserDetector
