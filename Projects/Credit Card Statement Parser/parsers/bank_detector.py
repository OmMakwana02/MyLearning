# parsers/bank_detector.py
import re
import logging
from typing import Optional
import config

logging.basicConfig(level=logging.INFO, format=config.LOG_FORMAT)
logger = logging.getLogger(__name__)

class BankDetector:
  """
    Detects which bank a credit card statement belongs to
    by searching for bank-specific keywords in the extracted text.
  """

  BANK_PATTERNS = {
        'axis': [
            r'AXIS\s+BANK',
            r'Axis\s+Bank',
            r'AXIS\s+BANK\s+LIMITED',
            r'www\.axisbank\.com',
            r'Axis\s+Credit\s+Card',
        ],
        'citi': [
            r'CITI\s*BANK',
            r'Citibank',
            r'CITIBANK\s+N\.A\.',
            r'Citi\s+Credit\s+Card',
            r'www\.citibank\.co\.in',
            r'CITI\s+INDIA',
        ],
        'hdfc': [
            r'HDFC\s+BANK',
            r'HDFC\s+Bank',
            r'HDFC\s+BANK\s+LTD',
            r'www\.hdfcbank\.com',
            r'HDFC\s+Credit\s+Card',
            r'Housing\s+Development\s+Finance\s+Corporation',
        ],
        'icici': [
            r'ICICI\s+BANK',
            r'ICICI\s+Bank',
            r'ICICI\s+BANK\s+LIMITED',
            r'www\.icicibank\.com',
            r'ICICI\s+Credit\s+Card',
        ],
        'silk': [
            r'SILK\s+BANK',
            r'Silk\s+Bank',
            r'SILKBANK\s+LIMITED',
            r'www\.silkbank\.com',
            r'Silk\s+Credit\s+Card',
        ],
    }

  @staticmethod
  def detect_bank(text:str) -> Optional[str]:
    """
    Detecting which bank the statement belongs to...
    
    Keyword arguments:
    argument: text (str)
    Return: Optional[str]  Bank Name('axis', 'citi', 'hdfc', 'icici', 'silk') or None
    """

    if not text:
      logger.warning("Empty text provided for bank detection")
      return None
    
    text = text.strip()

    bank_scores ={}

    for bank_name, patterns in BankDetector.BANK_PATTERNS.items():
      score = 0
      matched_patterns = []

      for pattern in patterns:

        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
          score += len(matches)
          matched_patterns.append(pattern)

      if score > 0:
        bank_scores[bank_name] = score
        logger.debug(f"{bank_name}: {score} matches - {matched_patterns}")

    # Return bank with highest score
    if bank_scores:
      detected_bank = max(bank_scores, key=bank_scores.get)
      logger.info(f"Bank detected: {detected_bank.upper()} (score: {bank_scores[detected_bank]})")
      return detected_bank
    
    logger.warning("Could not detect bank from text")
    return None

  @staticmethod
  def detect_bank_with_confidence(text: str) -> tuple[Optional[str], float]:
    """
    Detect bank and return confidence score (0.0 to 1.0).
    
    Args:
      text (str): Extracted text from PDF
        
    Returns:
      tuple: (bank_name, confidence_score)
    """
    if not text:
      return None, 0.0
    
    bank_scores = {}
    max_possible_score = 0
    
    for bank_name, patterns in BankDetector.BANK_PATTERNS.items():
      score = 0
      
      for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
          score += len(matches)
      
      if score > 0:
        bank_scores[bank_name] = score
      
      # Track maximum possible score (if all patterns matched once)
      max_possible_score = max(max_possible_score, len(patterns))

    if bank_scores:
      detected_bank = max(bank_scores, key=bank_scores.get)
      confidence = min(bank_scores[detected_bank] / max_possible_score, 1.0)
      
      logger.info(f"Bank detected: {detected_bank.upper()} (confidence: {confidence:.2%})")
      return detected_bank, confidence
    
    return None, 0.0

  @staticmethod
  def validate_bank(bank_name: str) -> bool:
    """
    Check if the detected bank is in the supported banks list.
    
    Args:
      bank_name (str): Bank name to validate
        
    Returns:
      bool: True if bank is supported, False otherwise
    """
    if not bank_name:
      return False
    
    is_valid = bank_name.lower() in config.SUPPORTED_BANKS
    
    if not is_valid:
      logger.warning(f"Bank '{bank_name}' is not in supported banks: {config.SUPPORTED_BANKS}")
    
    return is_valid
  
# Convenience function for direct import
def detect_bank(text: str) -> Optional[str]:
    """
    Convenience wrapper for BankDetector.detect_bank()
    
    Args:
        text (str): Extracted text from PDF
        
    Returns:
        Optional[str]: Detected bank name or None
    """
    return BankDetector.detect_bank(text)


def detect_bank_with_confidence(text: str) -> tuple[Optional[str], float]:
    """
    Convenience wrapper for BankDetector.detect_bank_with_confidence()
    
    Args:
        text (str): Extracted text from PDF
        
    Returns:
        tuple: (bank_name, confidence_score)
    """
    return BankDetector.detect_bank_with_confidence(text)
      