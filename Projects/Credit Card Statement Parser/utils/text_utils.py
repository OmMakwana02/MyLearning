# utils/text_utils.py
import re
import logging
from datetime import datetime
from typing import Optional, Dict, List, Tuple
import config  # Add this import

logging.basicConfig(level=logging.INFO, format=config.LOG_FORMAT)
logger = logging.getLogger(__name__)

# REGEX PATTERNS FOR EXTRACTING DATA

class TextPatterns:
  """
  Collection of regex patterns to extract common credit card data.
  These patterns are generic and work across multiple banks.
  """
  
  # Card number patterns: 4-4-4-4 or 16 consecutive digits (with XXX masking)
  CARD_NUMBER = r'(?:\d{4}[-\s]?){3}\d{4}|(?:\d{4}[-\s]?){3}[Xx*]{4}'
  
  # Cardholder name: 2-4 words, all caps or title case
  # Examples: "PATNALA VINOD KUMAR", "John Doe", "ANTONIETA LAPINING PABANELAS"
  CARDHOLDER_NAME = r'(?:(?:[A-Z][a-z]*\s)+[A-Z][a-z]*|(?:[A-Z\s]+)+)'
  
  # Credit limit: Currency + number (with commas/decimals)
  # Examples: "132,000.00", "600,000", "₹30,000"
  CREDIT_LIMIT = r'(?:₹|Rs\.?|€|\$)?[\s]?(?:\d{1,3}(?:[,]\d{3})*(?:\.\d{2})?|\d+)'
  
  # Total amount due: Similar to credit limit
  TOTAL_DUE = r'(?:₹|Rs\.?|€|\$)?[\s]?(?:\d{1,3}(?:[,]\d{3})*(?:\.\d{2})?|\d+)'
  
  # Payment due date: Various date formats
  # Examples: "04/11/2021", "07/14/21", "01/04/2023", "10-Apr-2018"
  DATE_DMY = r'(?:\d{1,2})[/-](?:\d{1,2})[/-](?:\d{2,4})'
  DATE_MDY = r'(?:\d{1,2})[/-](?:\d{1,2})[/-](?:\d{2,4})'
  DATE_NAMED = r'\d{1,2}-[A-Z][a-z]{2}-\d{4}'

# TEXT CLEANING FUNCTIONS
def clean_text(text: str) -> str:
  """
  Clean and normalize extracted text.
  - Remove extra whitespace
  - Remove page markers
  - Normalize line endings
  
  Args:
      text (str): Raw extracted text
      
  Returns:
      str: Cleaned text
  """
  if not text:
      return ""
  
  # Remove page markers (e.g., "--- Page 1 ---")
  text = re.sub(r'---\s*Page\s*\d+\s*---', '', text, flags=re.IGNORECASE)
  
  # Replace multiple spaces/tabs with single space
  text = re.sub(r'[\s\t]+', ' ', text)
  
  # Replace multiple newlines with double newline
  text = re.sub(r'\n\n+', '\n', text)
  
  return text.strip()

def normalize_whitespace(text: str) -> str:
  """
  Normalize whitespace while preserving structure.
  
  Args:
      text (str): Input text
      
  Returns:
      str: Text with normalized whitespace
  """
  lines = text.split('\n')
  cleaned_lines = [line.strip() for line in lines if line.strip()]
  return '\n'.join(cleaned_lines)

# CARDHOLDER NAME EXTRACTION

def extract_cardholder_name(text: str) -> Optional[str]:
  """
  Extract cardholder name from text.
  
  Strategy:
  1. Look for "Name:" or "Cardholder:" labels
  2. Extract 2-4 words following the label
  3. Fallback to searching for all-caps name patterns
  
  Args:
      text (str): Cleaned PDF text
      
  Returns:
      Optional[str]: Cardholder name or None
  """
  if not text:
    return None
  
  # Strategy 1: Look for "Name:" or "Cardholder:" followed by name
  patterns = [
    r'(?:Cardholder[\'s]*\s*Name|Name\s*[:=])\s*([A-Z][A-Za-z\s]+)',
    r'(?:Card\s*Name|Account\s*Name|Name\s*[:=])\s*([A-Z][A-Za-z\s]+)',
  ]
  
  for pattern in patterns:
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
      name = match.group(1).strip()
      # Validate: name should have at least 2 words and not too long
      if 2 <= len(name.split()) <= 5 and len(name) < 50:
        return name
  
  # Strategy 2: Look for all-caps name patterns (common in Indian banks)
  # Find sequences of 2-4 all-caps words
  caps_pattern = r'\b([A-Z][A-Z]+(?:\s+[A-Z][A-Z]+){1,3})\b'
  matches = re.findall(caps_pattern, text)
  
  if matches:
    # Return the longest match (usually the name, not abbreviations)
    longest_name = max(matches, key=len)
    if len(longest_name.split()) <= 5:
      return longest_name
  
  logger.warning("Could not extract cardholder name")
  return None

# CARD NUMBER EXTRACTION

def extract_card_number(text: str) -> Optional[str]:
  """
  Extract credit card number from text.
  Handles both full numbers and masked numbers (with X's or *'s).
  
  Args:
    text (str): Cleaned PDF text
      
  Returns:
    Optional[str]: Card number (last 4 digits if masked) or None
  """
  if not text:
    return None
  
  # Look for patterns like: 4034-1862-0212-4383 or 533467******7381
  card_patterns = [
    r'(?:Card\s*Number|Card\s*No\.|CC\s*No\.)[:\s]+([0-9X\*\-\s]+)',
    r'(\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4})',  # Full card number
    r'(\d{4}[\s\-]?(?:[X\*]{4}|0{4})[\s\-]?(?:[X\*]{4}|0{4})[\s\-]?\d{4})',  # Masked number
  ]
  
  for pattern in card_patterns:
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
      card_num = match.group(1)
      # Clean up: remove spaces and hyphens, keep only digits and X's
      card_num = re.sub(r'[\s\-]+', '', card_num)
      
      # Return last 4 digits (or full if mostly X's)
      if 'X' in card_num.upper() or '*' in card_num:
        return card_num[-4:]
      elif len(card_num) >= 4:
        return card_num[-4:]
  
  logger.warning("Could not extract card number")
  return None

# CREDIT LIMIT EXTRACTION

def extract_credit_limit(text: str) -> Optional[str]:
  """
  Extract credit limit from text.
  Looks for "Credit Limit" label followed by amount.
  
  Args:
    text (str): Cleaned PDF text
      
  Returns:
    Optional[str]: Credit limit (as currency string) or None
  """
  if not text:
    return None
  
  # Look for "Credit Limit" followed by a number
  patterns = [
    r'(?:Credit\s*Limit|Total\s*Credit\s*Limit)[:\s=]+(?:₹|Rs\.?)?[\s]*([0-9,]+(?:\.[0-9]{2})?)',
    r'(?:Credit\s*Limit)[:\s=]+(?:\$|€)?[\s]*([0-9,]+(?:\.[0-9]{2})?)',
  ]
  
  for pattern in patterns:
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
      limit = match.group(1).strip()
      return limit
  
  logger.warning("Could not extract credit limit")
  return None

# TOTAL AMOUNT DUE EXTRACTION

def extract_total_due(text: str) -> Optional[str]:
  """
  Extract total amount due from text.
  Looks for "Total Amount Due", "Total Dues", "Total Payment Due" etc.
  
  Args:
    text (str): Cleaned PDF text
      
  Returns:
    Optional[str]: Total due amount (as currency string) or None
  """
  if not text:
    return None
  
  # Look for "Total Amount Due" or similar labels
  patterns = [
    r'(?:Total\s*(?:Amount|Payment)?\s*Due|Total\s*Dues)[:\s=]+(?:₹|Rs\.?)?[\s]*(?:\d+(?:,\d{3})*(?:\.\d{2})?|\d+\.\d{2})',
    r'(?:Amount\s*Due|Total\s*Outstanding)[:\s=]+(?:\$|€|₹|Rs\.?)?[\s]*(?:\d+(?:,\d{3})*(?:\.\d{2})?|\d+\.\d{2})',
  ]
  
  for pattern in patterns:
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
      # Extract the number from the match
      full_match = match.group(0)
      amount = re.search(r'(?:\d+(?:,\d{3})*(?:\.\d{2})?|\d+\.\d{2})', full_match)
      if amount:
        return amount.group(0)

  logger.warning("Could not extract total due amount")
  return None

# PAYMENT DUE DATE EXTRACTION

def extract_payment_due_date(text: str) -> Optional[str]:
  """
  Extract payment due date from text.
  Handles multiple date formats and normalizes to YYYY-MM-DD.
  
  Args:
    text (str): Cleaned PDF text
      
  Returns:
    Optional[str]: Payment due date (YYYY-MM-DD) or None
  """
  if not text:
    return None
  
  # Look for "Payment Due Date" or "Due Date" labels
  date_label_patterns = [
    r'(?:Payment\s*)?Due\s*Date[:\s=]+([0-9\/\-A-Za-z]+)',
    r'Due\s*Date[:\s=]+([0-9\/\-A-Za-z]+)',
    r'(?:PAYMENT\s*)?DUE\s*DATE[:\s=]+([0-9\/\-A-Za-z]+)',
  ]
  
  date_str = None
  for pattern in date_label_patterns:
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
      date_str = match.group(1).strip()
      break
  
  if date_str:
    # Try to parse and normalize the date
    normalized = normalize_date(date_str)
    if normalized:
      return normalized
  
  logger.warning("Could not extract payment due date")
  return None

def normalize_date(date_str: str) -> Optional[str]:
  """
  Normalize date string to YYYY-MM-DD format.
  Handles multiple input formats:
  - DD/MM/YYYY or DD-MM-YYYY
  - MM/DD/YYYY (US format)
  - DD-MMM-YYYY (e.g., 10-Apr-2018)
  
  Args:
    date_str (str): Date string in various formats
      
  Returns:
    Optional[str]: Normalized date (YYYY-MM-DD) or None
  """
  if not date_str:
    return None
  
  # Clean up the date string
  date_str = date_str.strip()
  
  # List of date formats to try
  date_formats = [
    '%d/%m/%Y',    # 04/11/2021
    '%d-%m-%Y',    # 04-11-2021
    '%m/%d/%Y',    # 11/04/2021 (US)
    '%m-%d-%Y',    # 11-04-2021 (US)
    '%d/%m/%y',    # 04/11/21
    '%d-%m-%y',    # 04-11-21
    '%m/%d/%y',    # 11/04/21 (US)
    '%d-%b-%Y',    # 10-Apr-2018
    '%d-%b-%y',    # 10-Apr-18
    '%B %d, %Y',   # April 10, 2018
    '%b %d, %Y',   # Apr 10, 2018
  ]
  
  for date_format in date_formats:
    try:
      parsed_date = datetime.strptime(date_str, date_format)
      return parsed_date.strftime('%Y-%m-%d')
    except ValueError:
      continue
  
  logger.warning(f"Could not normalize date: {date_str}")
  return None

# MAIN EXTRACTION FUNCTION

def extract_all_fields(text: str) -> Dict[str, Optional[str]]:
  """
  Extract all 5 required data points from credit card statement text.
  
  Args:
    text (str): Raw extracted PDF text
      
  Returns:
    Dict: Dictionary with keys:
      - cardholder_name
      - card_number (last 4 digits)
      - credit_limit
      - total_due
      - payment_due_date (YYYY-MM-DD)
  """
  # Clean text first
  cleaned_text = clean_text(text)
  normalized_text = normalize_whitespace(cleaned_text)
  
  logger.info("Extracting all fields from text...")
  
  extracted_data = {
    'cardholder_name': extract_cardholder_name(normalized_text),
    'card_number': extract_card_number(normalized_text),
    'credit_limit': extract_credit_limit(normalized_text),
    'total_due': extract_total_due(normalized_text),
    'payment_due_date': extract_payment_due_date(normalized_text),
  }
  
  return extracted_data

def validate_extracted_data(data: Dict) -> Tuple[bool, List[str]]:
  """
  Validate extracted data to ensure all required fields are present.
  
  Args:
    data (Dict): Extracted data dictionary
      
  Returns:
    Tuple[bool, List[str]]: (is_valid, list_of_errors)
  """
  errors = []
  required_fields = ['cardholder_name', 'card_number', 'credit_limit', 'total_due', 'payment_due_date']
  
  for field in required_fields:
    if field not in data or data[field] is None or data[field] == '':
      errors.append(f"Missing field: {field}")
  
  is_valid = len(errors) == 0
  return is_valid, errors
