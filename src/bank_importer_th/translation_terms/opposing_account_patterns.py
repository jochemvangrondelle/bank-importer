"""Patterns for extracting opposing account information from transaction descriptions."""

import re
from typing import Tuple

# Thai financial terms to remove when extracting opposing account names
THAI_FINANCIAL_TERMS = [
    r"Bill Payment\s+",
    r"จ่ายบิล\s+",
    r"Payment\s+",
    r"Payment to\s+",
    r"โอนเงิน\s+",
    r"Transfer\s+",
    r"Withdrawal\s+",
    r"ถอนเงิน\s+",
    r"Deposit\s+",
    r"ฝากเงิน\s+",
    r"Credit\s+",
    r"Debit\s+",
    r"ATM\s+",
    r"POS\s+",
    r"CDM\s+",
    r"IB\s+",  # Internet Banking
    r"Mobile Banking\s+",
    r"Online Banking\s+",
    r"QR\s+",
    r"QR Payment\s+",
    r"QR Code\s+",
    r"Cash Withdrawal\s+",
    r"Cash Deposit\s+",
    r"Fund Transfer\s+",
    r"Interbank Transfer\s+",
    r"Domestic Transfer\s+",
    r"International Transfer\s+",
    r"รายการ Prompt-IN\s+",
    r"รายการ Prompt-OUT\s+",
    r"รายการโอนเงิน\s+",
    r"รายการฝากเงิน\s+",
    r"รายการถอนเงิน\s+",
    r"รายการชำระเงิน\s+",
    r"รายการรับเงิน\s+",
    r"รายการจ่ายเงิน\s+",
    r"รายการบัตรเครดิต\s+",
    r"รายการบัตรเดบิต\s+",
    r"รายการเอทีเอ็ม\s+",
    r"รายการอินเทอร์เน็ตแบงก์กิ้ง\s+",
    r"รายการมือถือแบงก์กิ้ง\s+",
]

# Patterns for bank transfers with account numbers
BANK_TRANSFER_PATTERNS = [
    # "Transfer to BBL x9551 MR VASAN NARDVIRIY"
    r"Transfer to (\w+)\s+x(\d+)\s+(.+)",
    # "Transfer to TTB x1863 PREEYANUT PAN"
    r"Transfer to (\w+)\s+(\d+)\s+(.+)",
    # "BAY MR.SOURAV DAS"
    r"(\w+)\s+(MR\.|MRS\.|MS\.|DR\.|PROF\.|SIR\.|MADAM\.|MR\s|MRS\s|MS\s|DR\s|PROF\s|SIR\s|MADAM\s)(.+)",
]

# Patterns for specific services
SPECIAL_SERVICE_PATTERNS = [
    # K+ shop transactions
    r"K\+\s*shop\s*\(([^)]+)\)",
    # PromptPay transactions
    r"PromptPay ID\s*:\s*([^\s]+)",
    r"PromptPay\s+ID\s*:\s*([^\s]+)",
]

# Account number patterns
ACCOUNT_NUMBER_PATTERNS = [
    r"To Acc No\.\s*:\s*([^\s]+)",
    r"From Acc No\.\s*:\s*([^\s]+)",
    r"Account\s*:\s*([^\s]+)",
    r"Acc\s*:\s*([^\s]+)",
]

# Common suffixes to remove from person names
PERSON_NAME_SUFFIXES = [
    r"\s+From\s+Acc.*$",
    r"\s+To\s+Acc.*$",
    r"\s+Account.*$",
    r"\s+Acc.*$",
]


def extract_opposing_account(description: str) -> Tuple[str, str]:
    """
    Extract opposing account name and number from transaction description.

    Args:
        description: Transaction description (can be translated or original)

    Returns:
        Tuple of (opposing_name, opposing_number)
    """
    if not description:
        return "", ""

    # Try bank transfer patterns first
    for pattern in BANK_TRANSFER_PATTERNS:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            if len(match.groups()) == 3:
                # Pattern: "Transfer to BANK x1234 NAME"
                bank_name = match.group(1)
                account_number = match.group(2)
                person_name = match.group(3).strip()
                opposing_name = f"{bank_name} {person_name}"
                return opposing_name, account_number
            elif len(match.groups()) == 2:
                # Pattern: "BANK TITLE NAME"
                bank_code = match.group(1)
                title_and_name = match.group(2).strip()
                # Clean up person name
                person_name = _clean_person_name(title_and_name)
                opposing_name = f"{bank_code} {person_name}"
                return opposing_name, ""

    # Try special service patterns
    for pattern in SPECIAL_SERVICE_PATTERNS:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            service_name = match.group(1).strip()
            return service_name, ""

    # Try account number patterns
    for pattern in ACCOUNT_NUMBER_PATTERNS:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            account_number = match.group(1).strip()
            # Extract name from remaining description
            remaining_desc = re.sub(
                pattern, "", description, flags=re.IGNORECASE
            ).strip()
            if remaining_desc and len(remaining_desc) > 3:
                return remaining_desc, account_number

    # Remove financial terms and extract merchant/store name
    cleaned_description = _remove_financial_terms(description)

    if cleaned_description and len(cleaned_description.strip()) > 3:
        merchant_name = cleaned_description.strip()
        return merchant_name, ""

    return "", ""


def _clean_person_name(name: str) -> str:
    """Clean person name by removing common suffixes."""
    cleaned = name
    for suffix in PERSON_NAME_SUFFIXES:
        cleaned = re.sub(suffix, "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def _remove_financial_terms(description: str) -> str:
    """Remove financial terms from description to extract merchant name."""
    cleaned = description.strip()
    for term in THAI_FINANCIAL_TERMS:
        cleaned = re.sub(term, "", cleaned, flags=re.IGNORECASE)
    return cleaned
