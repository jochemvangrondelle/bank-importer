# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability within Bank Importer Thailand, please report it through [GitHub Security Advisories](https://github.com/jochemvangrondelle/bank-importer/security/advisories/new) or send an email to jochem@vangrondelle.net.

### What to Include

When reporting a vulnerability, please include:

- **Description**: A clear description of the vulnerability
- **Steps to reproduce**: Detailed steps to reproduce the issue
- **Impact**: Potential impact of the vulnerability
- **Suggested fix**: If you have any suggestions for fixing the issue

### Response Timeline

- **Initial response**: Within 48 hours
- **Status updates**: Regular updates on progress
- **Fix timeline**: Depends on severity and complexity

## Security Considerations

### Data Privacy

- **No sensitive data storage**: The application does not store bank credentials or sensitive financial information
- **Local processing**: All data processing happens locally on your machine
- **Optional API keys**: Google Translate API key is optional and only used for translation

### Best Practices

- Keep your `config.toml` file secure and never commit it to version control
- Use strong passwords for password-protected PDF files
- Regularly update dependencies for security patches
- Review exported data before importing into financial management systems

### Docker Security

- **Non-root execution**: Runs as `appuser` with minimal permissions
- **Read-only mounts**: Input files are mounted as read-only
- **Minimal attack surface**: Optimized for security and size

## Disclosure Policy

Security vulnerabilities will be disclosed through:

1. **Private disclosure**: Initial private communication via GitHub Security Advisories
2. **Public disclosure**: After a fix is available, through GitHub releases and security advisories

## Responsible Disclosure

We appreciate security researchers who:

- Report vulnerabilities privately first
- Allow reasonable time for fixes
- Work collaboratively on solutions
- Follow responsible disclosure practices
