# base.py
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, List
import logging
import config
from utils import text_utils

logging.basicConfig(level=logging.INFO, format=config.LOG_FORMAT)
logger = logging.getLogger(__name__)


class BaseParser(ABC):
    """
    Abstract base class for all bank-specific credit card statement parsers.
    
    Each bank parser must inherit from this class and implement the parse() method.
    This ensures all parsers return data in a consistent format.
    """
    
    # Bank name - to be overridden by child classes
    BANK_NAME = "unknown"
    
    def __init__(self):
        """Initialize the parser."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    def parse(self, text: str, tables: Optional[List] = None) -> Dict[str, Optional[str]]:
        """
        Parse credit card statement text and extract 5 key data points.
        
        This method MUST be implemented by all child classes.
        
        Args:
            text (str): Extracted text from PDF statement
            tables (List): Optional list of extracted tables from PDF
            
        Returns:
            Dict with keys:
                - cardholder_name: str
                - card_number: str (last 4 digits)
                - credit_limit: str
                - total_due: str
                - payment_due_date: str (YYYY-MM-DD format)
        """
        pass
    
    def extract_data(self, text: str, filename: str = "", tables: Optional[List] = None) -> Dict[str, Any]:
        """
        Main extraction method that wraps parse() and adds metadata.
        
        Args:
            text (str): Extracted PDF text
            filename (str): Original PDF filename (optional)
            tables (List): Optional list of extracted tables
            
        Returns:
            Dict: Parsed data with metadata
        """
        self.logger.info(f"Parsing {self.BANK_NAME.upper()} statement...")
        
        try:
            # Call the bank-specific parse method
            parsed_data = self.parse(text, tables)
            
            # Add metadata
            result = {
                'bank': self.BANK_NAME,
                'filename': filename,
                'status': 'success',
                **parsed_data  # Unpack the 5 fields
            }
            
            # Validate that all required fields are present
            validation_result = self._validate_parsed_data(result)
            
            if not validation_result['is_valid']:
                result['status'] = 'partial'
                result['errors'] = validation_result['errors']
                self.logger.warning(f"Incomplete data: {validation_result['errors']}")
            else:
                self.logger.info(f"Successfully parsed {self.BANK_NAME.upper()} statement")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error parsing {self.BANK_NAME.upper()} statement: {str(e)}")
            return {
                'bank': self.BANK_NAME,
                'filename': filename,
                'status': 'error',
                'error_message': str(e),
                'cardholder_name': None,
                'card_number': None,
                'credit_limit': None,
                'total_due': None,
                'payment_due_date': None,
            }
    
    def _validate_parsed_data(self, data: Dict) -> Dict[str, Any]:
        """
        Validate that all required fields are present and non-empty.
        
        Args:
            data (Dict): Parsed data dictionary
            
        Returns:
            Dict with keys:
                - is_valid: bool
                - errors: list of missing/empty fields
        """
        required_fields = [
            'cardholder_name',
            'card_number',
            'credit_limit',
            'total_due',
            'payment_due_date'
        ]
        
        errors = []
        
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing field: {field}")
            elif data[field] is None or str(data[field]).strip() == '':
                errors.append(f"Empty field: {field}")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors
        }
    
    # Common utility methods that can be used by all parsers
    
    @staticmethod
    def clean_amount(amount: Optional[str]) -> Optional[str]:
        """
        Clean and format currency amounts.
        Removes currency symbols, extra spaces, etc.
        
        Args:
            amount (str): Raw amount string (e.g., "₹ 5,000.00")
            
        Returns:
            str: Cleaned amount (e.g., "5,000.00")
        """
        if not amount:
            return None
        
        import re
        # Remove currency symbols and extra spaces
        cleaned = re.sub(r'[₹$€Rs\.\s]+', '', amount)
        # Keep only numbers, commas, and decimal points
        cleaned = re.sub(r'[^\d,\.]', '', cleaned)
        
        return cleaned.strip() if cleaned else None
    
    @staticmethod
    def extract_last_4_digits(card_number: Optional[str]) -> Optional[str]:
        """
        Extract last 4 digits from card number (handles masked formats).
        
        Args:
            card_number (str): Card number in any format
            
        Returns:
            str: Last 4 digits or None
        """
        if not card_number:
            return None
        
        import re
        # Extract all digits
        digits = re.findall(r'\d', card_number)
        
        if len(digits) >= 4:
            return ''.join(digits[-4:])
        
        return None
    
    @staticmethod
    def normalize_date(date_str: Optional[str]) -> Optional[str]:
        """
        Normalize date to YYYY-MM-DD format.
        Uses the function from text_utils.
        
        Args:
            date_str (str): Date in any format
            
        Returns:
            str: Date in YYYY-MM-DD format or None
        """
        if not date_str:
            return None
        
        return text_utils.normalize_date(date_str)
    
    # NEW: Helper method for table extraction
    
    def find_table_with_header(self, tables: List, header_keywords: List[str]) -> Optional[List]:
        """
        Find a table that contains specific header keywords.
        
        Args:
            tables (List): List of tables (each table is list of rows)
            header_keywords (List[str]): Keywords to search for in headers
            
        Returns:
            Optional[List]: The matching table or None
        """
        if not tables:
            return None
        
        for table in tables:
            if not table or len(table) == 0:
                continue
            
            # Check first few rows for header keywords
            header_rows = table[:3]  # Check first 3 rows
            
            for row in header_rows:
                row_text = ' '.join(str(cell) for cell in row if cell)
                
                # Check if all keywords are present
                if all(keyword.lower() in row_text.lower() for keyword in header_keywords):
                    self.logger.info(f"Found table with headers: {header_keywords}")
                    return table
        
        return None
    
    def extract_value_from_table(self, table: List, label: str) -> Optional[str]:
        """
        Extract a value from a table by searching for a label.
        
        Args:
            table (List): Table data (list of rows)
            label (str): Label to search for
            
        Returns:
            Optional[str]: Extracted value or None
        """
        if not table:
            return None
        
        for row in table:
            row_text = ' '.join(str(cell) for cell in row if cell)
            
            if label.lower() in row_text.lower():
                # Try to extract the value after the label
                import re
                # Look for numbers with commas and decimals
                matches = re.findall(r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?', row_text)
                if matches:
                    return matches[0]
        
        return None
    
    # Convenience methods that wrap text_utils functions
    
    def extract_cardholder_name(self, text: str) -> Optional[str]:
        """Extract cardholder name using text_utils."""
        return text_utils.extract_cardholder_name(text)
    
    def extract_card_number(self, text: str) -> Optional[str]:
        """Extract card number using text_utils."""
        return text_utils.extract_card_number(text)
    
    def extract_credit_limit(self, text: str) -> Optional[str]:
        """Extract credit limit using text_utils."""
        return text_utils.extract_credit_limit(text)
    
    def extract_total_due(self, text: str) -> Optional[str]:
        """Extract total due amount using text_utils."""
        return text_utils.extract_total_due(text)
    
    def extract_payment_due_date(self, text: str) -> Optional[str]:
        """Extract payment due date using text_utils."""
        return text_utils.extract_payment_due_date(text)


class GenericParser(BaseParser):
    """
    Generic parser that uses text_utils functions directly.
    This is a fallback parser when bank-specific logic isn't needed.
    """
    
    BANK_NAME = "generic"
    
    def parse(self, text: str, tables: Optional[List] = None) -> Dict[str, Optional[str]]:
        """
        Parse using generic text_utils extraction functions.
        
        Args:
            text (str): Extracted PDF text
            tables (List): Optional tables (not used in generic parser)
            
        Returns:
            Dict: Parsed data with 5 fields
        """
        self.logger.info("Using generic parser...")
        
        # Use text_utils to extract all fields
        extracted = text_utils.extract_all_fields(text)
        
        return {
            'cardholder_name': extracted.get('cardholder_name'),
            'card_number': extracted.get('card_number'),
            'credit_limit': extracted.get('credit_limit'),
            'total_due': extracted.get('total_due'),
            'payment_due_date': extracted.get('payment_due_date'),
        }