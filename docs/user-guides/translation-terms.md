# Translation Terms Guide

This guide explains the new dedicated translation terms system that provides comprehensive Thai to English mapping for financial transactions.

## Overview

The translation terms system has been moved to a dedicated directory structure (`src/bank_importer/translation_terms/`) to provide better organization and extensibility for multiple languages. Currently, it includes comprehensive Thai financial terms extracted from actual transaction data.

## Directory Structure

```
src/bank_importer/translation_terms/
├── __init__.py              # Package initialization
└── thai_terms.py           # Thai financial terms mapping
```

## Features

### 🌍 **Multi-Language Ready**

- **Extensible structure**: Easy to add new languages
- **Dedicated files**: One file per language for clarity
- **Centralized management**: All terms in one place
- **Version control friendly**: Easy to track changes

### 📊 **Comprehensive Coverage**

- **Transaction types**: All common Thai financial terms
- **Merchant names**: Popular Thai businesses and services
- **Banking terms**: Financial and banking terminology
- **Common words**: Frequently used Thai words and prepositions
- **Geographic terms**: Thai locations and place names
- **Business terms**: Company types and business terminology

### 🎯 **Real-World Data**

- **Extracted from transactions**: Based on actual bank statement data
- **User-specific merchants**: Your regular merchants already included
- **Context-aware**: Terms that appear in financial contexts
- **Comprehensive mapping**: Covers all common scenarios

## Thai Terms Coverage

### Transaction Types

```python
'โอนเงิน': 'transfer',
'ฝากเงิน': 'deposit',
'ถอนเงิน': 'withdrawal',
'ชำระเงิน': 'payment',
'รับเงิน': 'receive',
'จ่ายเงิน': 'pay',
'รับโอน': 'receive transfer',
'โอนออก': 'transfer out',
'โอนเข้า': 'transfer in',
```

### Payment Methods

```python
'พร้อมเพย์': 'promptpay',
'บัตรเครดิต': 'credit card',
'บัตรเดบิต': 'debit card',
'เอทีเอ็ม': 'ATM',
'อินเทอร์เน็ตแบงก์กิ้ง': 'internet banking',
'มือถือแบงก์กิ้ง': 'mobile banking',
'Prompt-IN': 'promptpay receive',
'Prompt-OUT': 'promptpay send',
```

### Common Merchants

```python
'เซเว่น': '7-Eleven',
'เทสโก้': 'Tesco',
'บิ๊กซี': 'Big C',
'โลตัส': 'Lotus',
'แมคโดนัลด์': 'McDonald\'s',
'เคเอฟซี': 'KFC',
'สตาร์บัคส์': 'Starbucks',
'ฟู้ดแลนด์': 'Foodland',
'เซ็นทรัล': 'Central',
'สยามพารากอน': 'Siam Paragon',
```

### Banking Terms

```python
'ดอกเบี้ย': 'interest',
'ภาษี': 'tax',
'ค่าธรรมเนียม': 'fee',
'ค่าบริการ': 'service charge',
'ยอดคงเหลือ': 'balance',
'รายการ': 'transaction',
'บัญชี': 'account',
'ธนาคาร': 'bank',
```

### Business Terms

```python
'บมจ.': 'Public Company Limited',
'หจก.': 'Limited Partnership',
'บริษัท': 'Company',
'สาขา': 'Branch',
'สำนักงาน': 'Office',
'ศูนย์': 'Center',
```

### Common Words

```python
'จาก': 'from',
'ถึง': 'to',
'ผ่าน': 'via',
'โดย': 'by',
'สำหรับ': 'for',
'ของ': 'of',
'ใน': 'in',
'ที่': 'at',
'กับ': 'with',
```

### Geographic Terms

```python
'กรุงเทพ': 'Bangkok',
'เชียงใหม่': 'Chiang Mai',
'ภูเก็ต': 'Phuket',
'พัทยา': 'Pattaya',
'หาดใหญ่': 'Hat Yai',
'นครราชสีมา': 'Nakhon Ratchasima',
```

## Usage Examples

### Before Translation

```
"จ่ายบิล บมจ. ธนาคารกสิกรไทย"
"รายการ Prompt-IN/MR. TRISTAN WARREN SING"
"รับโอนจาก SCB x0912 นาย ประมวล ศรีมาศ"
```

### After Translation

```
"bill payment Public Company Limited bankKasikorn Bank"
"transaction Prompt-IN/MR. TRISTAN WARREN SING"
"receive transferfrom SCB x0912 นาย ประมวล ศรีมาศ"
```

## Adding New Terms

### For Thai Terms

Edit `src/bank_importer/translation_terms/thai_terms.py`:

```python
THAI_FINANCIAL_TERMS = {
    # ... existing terms ...

    # Add new terms
    'คำใหม่': 'new term',
    'คำเก่า': 'old term',
}
```

### For New Languages

1. Create a new file: `src/bank_importer/translation_terms/english_terms.py`
2. Define the terms dictionary:

```python
ENGLISH_FINANCIAL_TERMS = {
    'transfer': 'transfer',
    'deposit': 'deposit',
    'withdrawal': 'withdrawal',
    # ... more terms
}
```

3. Update `__init__.py` to export the new terms
4. Update the translation service to use the new language

## Benefits

### 🎯 **Improved Accuracy**

- **Context-specific**: Terms extracted from actual financial data
- **User-specific**: Includes your regular merchants and services
- **Comprehensive**: Covers all common Thai financial terms
- **Consistent**: Standardized translations across all exports

### 📈 **Better Classification**

- **English descriptions**: Easier to categorize in Firefly-III
- **Search-friendly**: English text is more searchable
- **Consistent naming**: Standardized merchant and service names
- **Reduced manual work**: Less need for manual categorization

### 🔧 **Maintainability**

- **Centralized**: All terms in one place
- **Version controlled**: Easy to track changes
- **Extensible**: Simple to add new languages
- **Documented**: Clear structure and organization

## Integration

### Translation Service

The translation service automatically uses the new terms:

```python
from bank_importer.translation_service import translate_description

# Automatically uses the comprehensive terms
translated = translate_description("จ่ายบิล 7-ELEVEN")
# Result: "bill payment 7-ELEVEN"
```

### CSV Export

CSV exports include translated descriptions:

```csv
date,description,amount
2025-03-03,bill payment Public Company Limited bankKasikorn Bank (จ่ายบิล บมจ. ธนาคารกสิกรไทย),4980.00
2025-03-10,transaction Prompt-IN/MR. TRISTAN WARREN SING (รายการ Prompt-IN/MR. TRISTAN WARREN SING),1400.00
```

### YAML Export

YAML exports show both original and translated:

```yaml
description:
  translated: bill payment Public Company Limited bankKasikorn Bank (จ่ายบิล บมจ. ธนาคารกสิกรไทย)
  original: จ่ายบิล บมจ. ธนาคารกสิกรไทย
```

## Performance

### Caching

- **Persistent cache**: Translations cached in `translation_cache.json`
- **Fast lookup**: Dictionary-based term mapping
- **Reduced API calls**: Fewer calls to Google Translate
- **Offline capability**: Works without internet for cached terms

### Optimization

- **Smart skipping**: Avoids translating numbers, codes, emails
- **Efficient matching**: Direct dictionary lookup
- **Batch processing**: Can handle multiple descriptions
- **Memory efficient**: Only loads terms when needed

## Future Enhancements

### Planned Features

1. **Additional Languages**

   - Chinese financial terms
   - Japanese financial terms
   - Korean financial terms
   - Vietnamese financial terms

2. **Advanced Features**

   - Context-aware translation
   - Machine learning improvements
   - Custom user dictionaries
   - Industry-specific terms

3. **Integration Options**
   - API endpoints for external access
   - Web interface for term management
   - Import/export functionality
   - Collaborative term sharing

## Troubleshooting

### Common Issues

1. **Missing translations**

   - Check if term exists in `thai_terms.py`
   - Add missing terms to the dictionary
   - Verify term spelling and formatting

2. **Incorrect translations**

   - Review term mapping in `thai_terms.py`
   - Update incorrect translations
   - Test with specific examples

3. **Performance issues**
   - Check translation cache
   - Verify file permissions
   - Monitor memory usage

### Best Practices

1. **Term Management**

   - Keep terms organized by category
   - Use consistent naming conventions
   - Document new terms added
   - Regular review and cleanup

2. **Testing**

   - Test new terms before deployment
   - Verify translations with real data
   - Check for conflicts or duplicates
   - Validate with native speakers

3. **Maintenance**
   - Regular updates based on new transactions
   - Monitor for new merchants or services
   - Update terms based on user feedback
   - Version control all changes

The translation terms system provides a robust foundation for accurate and comprehensive Thai to English translation of financial transactions, making it much easier to categorize and understand your bank statements in Firefly-III.
