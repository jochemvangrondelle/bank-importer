# Contributing to Bank Importer Thailand

Thank you for your interest in contributing to Bank Importer Thailand! This project is designed for extensibility and welcomes contributions from the community.

## Project Overview

Bank Importer Thailand is a Python application that parses Thai bank export PDFs and exports transactions to CSV format suitable for import into Firefly-III. The project is intentionally designed without a direct Firefly-III target to rely on Firefly's own robust importer.

## How to Contribute

### 🚀 **Getting Started**

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Set up the development environment**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/bank-importer.git
   cd bank-importer
   uv sync --extra dev
   ```

### 📋 **Development Workflow**

1. **Create a feature branch**:

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the coding standards below

3. **Test your changes**:

   ```bash
   uv run pytest
   uv run mypy src/
   uv run ruff check src/
   ```

4. **Commit your changes** with clear commit messages:

   ```bash
   git commit -m "feat: add support for new bank X"
   git commit -m "fix: resolve translation issue with Thai terms"
   git commit -m "docs: update README with new features"
   ```

5. **Push to your fork** and create a pull request

## 🏗️ **Architecture Overview**

The project follows a modular architecture:

```
src/bank_importer/
├── banks/           # Bank-specific parsers
├── targets/         # Export format handlers
├── models/          # Data structures
├── translation_terms/ # Thai financial terms
├── interfaces/      # Abstract base classes
└── cli.py          # Command-line interface
```

### **Key Components**

- **Parsers**: Implement `Parser` interface for new banks
- **Targets**: Implement `Target` interface for new export formats
- **Models**: Define data structures in `models/`
- **Translation**: Extend Thai terms in `translation_terms/`

## 🏦 **Adding New Banks**

To add support for a new Thai bank:

1. **Create a new parser** in `src/bank_importer/banks/`
2. **Implement the Parser interface**:

   ```python
   from ..interfaces.parser import Parser
   from ..models.transaction import Transaction

   class NewBankParser(Parser):
       def parse_file(self, file_path: Path, config: Dict[str, Any]) -> Iterator[Transaction]:
           # Your parsing logic here
           pass
   ```

3. **Add configuration examples** to `config-example.toml`
4. **Update documentation** in README.md
5. **Add tests** in `tests/banks/`

### **Parser Requirements**

- Parse transaction dates, amounts, descriptions
- Handle account-specific metadata
- Support password-protected files if needed
- Generate unique external IDs
- Handle Thai to English translation

## 📊 **Adding New Export Formats**

To add a new export format:

1. **Create a new target** in `src/bank_importer/targets/`
2. **Implement the Target interface**:

   ```python
   from ..interfaces.target import Target

   class NewFormatTarget(Target):
       def export_transactions(self, transactions: List[Transaction], config: Dict[str, Any]) -> Dict[str, Any]:
           # Your export logic here
           pass
   ```

3. **Add configuration options** to `config-example.toml`
4. **Update target manager** in `target_manager.py`
5. **Add tests** in `tests/targets/`

## 🌐 **Translation Improvements**

### **Adding Thai Financial Terms**

1. **Edit** `src/bank_importer/translation_terms/thai_terms.py`
2. **Add new terms** to the `THAI_FINANCIAL_TERMS` dictionary:
   ```python
   THAI_FINANCIAL_TERMS = {
       # ... existing terms ...
       "คำใหม่": "new term",
   }
   ```

### **Improving Translation Logic**

1. **Enhance** `src/bank_importer/translation_service.py`
2. **Add new translation services** if needed
3. **Improve caching** and performance
4. **Add support for other languages**

## 🧪 **Testing Guidelines**

### **Running Tests**

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/banks/test_krungsri_pdf.py

# Run with coverage
uv run pytest --cov=src/bank_importer

# Run type checking
uv run mypy src/
```

### **Writing Tests**

- **Test parsers** with sample bank statements
- **Test targets** with mock transaction data
- **Test translation** with Thai/English pairs
- **Test CLI** commands with various inputs

### **Test Data**

- **Bank statements**: Use anonymized sample data
- **Personal information**: Never commit real account details
- **Test files**: Keep test files small and focused

## 📝 **Code Standards**

### **Python Style**

- **Type hints**: Use type hints for all functions
- **Docstrings**: Include clear docstrings for all classes and methods
- **Error handling**: Implement proper exception handling
- **Logging**: Use the logging system for debug information

### **Code Formatting**

```bash
# Format code
uv run ruff format src/

# Check code quality
uv run ruff check src/

# Fix issues automatically
uv run ruff check --fix src/
```

### **Commit Messages**

Use conventional commit format:

```
feat: add support for new bank X
fix: resolve translation issue with Thai terms
docs: update README with new features
test: add tests for new parser
refactor: improve translation service
```

## 🐛 **Bug Reports**

When reporting bugs:

1. **Check existing issues** first
2. **Provide clear steps** to reproduce
3. **Include sample data** (anonymized)
4. **Describe expected vs actual behavior**
5. **Include system information** (OS, Python version)

## 💡 **Feature Requests**

When requesting features:

1. **Explain the use case** clearly
2. **Describe the expected behavior**
3. **Consider the impact** on existing functionality
4. **Suggest implementation** if possible

## 📚 **Documentation**

### **Code Documentation**

- **Docstrings**: Use Google-style docstrings
- **Type hints**: Include comprehensive type annotations
- **Comments**: Explain complex logic
- **Examples**: Include usage examples

### **User Documentation**

- **README.md**: Keep updated with new features
- **Configuration**: Document all config options
- **Examples**: Provide clear usage examples
- **Troubleshooting**: Include common issues and solutions

## 🔒 **Security Guidelines**

### **Personal Information**

- **Never commit** real account numbers, passwords, or personal data
- **Use placeholders** in examples: `YOUR_ACCOUNT_NUMBER`
- **Anonymize** test data and examples
- **Check** for sensitive data before committing

### **API Keys**

- **Never commit** API keys or secrets
- **Use environment variables** for sensitive configuration
- **Document** required API keys in README
- **Provide** example configuration files

## 🚀 **Release Process**

### **Beta Releases**

1. **Update version** in `pyproject.toml`
2. **Update changelog** with new features/fixes
3. **Test thoroughly** with sample data
4. **Create release** on GitHub
5. **Update documentation** if needed

### **Contributing to Releases**

- **Test** the release candidate
- **Report** any issues found
- **Suggest** improvements
- **Help** with documentation updates

## 🤝 **Community Guidelines**

### **Be Respectful**

- **Be patient** with new contributors
- **Provide constructive** feedback
- **Help others** learn and grow
- **Respect different** perspectives and approaches

### **Communication**

- **Use clear language** in issues and PRs
- **Provide context** for your suggestions
- **Ask questions** when unsure
- **Share knowledge** with the community

## 📞 **Getting Help**

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and ideas
- **Documentation**: Check README and code comments
- **Code Examples**: Look at existing parsers and targets

## 🎯 **Priority Areas**

### **High Priority**

- **New Thai banks**: Adding support for more banks
- **Bug fixes**: Resolving parsing or export issues
- **Documentation**: Improving user guides and examples
- **Testing**: Adding comprehensive test coverage

### **Medium Priority**

- **Performance**: Optimizing parsing and translation
- **New export formats**: Adding alternative export options
- **Translation improvements**: Better Thai to English translation
- **CLI enhancements**: Improving user experience

### **Low Priority**

- **UI improvements**: If a web interface is added
- **Advanced features**: Complex analysis tools
- **Integration**: Direct Firefly-III integration (intentionally excluded)

---

**Thank you for contributing to Bank Importer Thailand!** 🎉

Your contributions help make Thai bank statement processing easier for the Firefly-III community.
