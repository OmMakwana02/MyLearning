# hdfc.py
import re
import logging
from typing import Dict, Optional, List
from .base import BaseParser
import config

logging.basicConfig(level=logging.INFO, format=config.LOG_FORMAT)
logger = logging.getLogger(__name__)


class HdfcParser(BaseParser):
    """
    Parser for HDFC Bank Credit Card Statements.
    Uses table extraction first, falls back to text extraction.
    """
    
    BANK_NAME = "hdfc"
    
    def parse(self, text: str, tables: Optional[List] = None) -> Dict[str, Optional[str]]:
        """Parse HDFC Bank credit card statement."""
        self.logger.info("Parsing HDFC Bank statement...")
        
        # Initialize result
        result = {
            'cardholder_name': None,
            'card_number': None,
            'credit_limit': None,
            'total_due': None,
            'payment_due_date': None,
        }

        # ALWAYS extract name from text first (more reliable)
        result['cardholder_name'] = self._extract_cardholder_name(text)
        
        # Try table extraction for other fields
        if tables:
            self.logger.info("Attempting table-based extraction...")
            table_data = self._extract_from_tables(tables)
            
            # Update result with table data (but don't overwrite name)
            for key, value in table_data.items():
                if value and key != 'cardholder_name':  # Skip name from tables
                    result[key] = value
            
            # Check if we got all 5 fields
            if all(result.values()):
                self.logger.info("Successfully extracted all data")
                return result

        # Fill missing fields using text extraction
        missing_fields = [k for k, v in result.items() if not v]
        if missing_fields:
            self.logger.info(f"Extracting missing fields from text: {missing_fields}")
            
            # Skip name since we already extracted it
            if not result['card_number']:
                result['card_number'] = self._extract_card_number(text)
            if not result['credit_limit']:
                result['credit_limit'] = self._extract_credit_limit(text)
            if not result['total_due']:
                result['total_due'] = self._extract_total_due(text)
            if not result['payment_due_date']:
                result['payment_due_date'] = self._extract_payment_due_date(text)

        return result
    
    def _extract_from_tables(self, tables: List) -> Dict[str, Optional[str]]:
        """
        Extract all 5 data points from HDFC tables.
        
        HDFC tables typically have this structure:
        Row 1: Headers (Payment Due Date | Total Dues | Minimum Amount Due)
        Row 2: Values  (01/04/2023 | 22,935.00 | 22,935.00)
        
        Another table:
        Row 1: Headers (Credit Limit | Available Credit Limit | Available Cash Limit)
        Row 2: Values  (30,000 | 0.00 | 0.00)
        """
        extracted_data = {
            'cardholder_name': None,
            'card_number': None,
            'credit_limit': None,
            'total_due': None,
            'payment_due_date': None,
        }
        
        # Strategy: Look for specific header patterns in tables
        for table in tables:
            if not table or len(table) < 2:
                continue
            
            # Convert table to string for easier searching
            table_text = '\n'.join([' '.join(str(cell) for cell in row if cell) for row in table])
            
            # Extract Payment Due Date and Total Dues
            if "Payment Due Date" in table_text and "Total Dues" in table_text:
                extracted_data.update(self._parse_payment_table(table))
            
            # Extract Credit Limit
            if "Credit Limit" in table_text and "Available Credit" in table_text:
                extracted_data['credit_limit'] = self._parse_credit_limit_table(table)
            
            # Extract Card Number
            if "Card No" in table_text:
                extracted_data['card_number'] = self._parse_card_number_table(table)
        
        # Cardholder name is usually not in tables, extract from text
        # (will be filled by fallback if None)
        
        return extracted_data
    
    def _parse_payment_table(self, table: List) -> Dict[str, Optional[str]]:
        """
        Parse the payment summary table.
        
        Expected format:
        Row 1: "Payment Due Date | Total Dues | Minimum Amount Due"
        Row 2: "01/04/2023 | 22,935.00 | 22,935.00"
        """
        result = {'total_due': None, 'payment_due_date': None}
        
        try:
            # Find header row
            header_row_idx = None
            for idx, row in enumerate(table):
                row_text = ' '.join(str(cell) for cell in row if cell)
                if "Payment Due Date" in row_text and "Total Dues" in row_text:
                    header_row_idx = idx
                    break
            
            if header_row_idx is None or header_row_idx + 1 >= len(table):
                return result
            
            # Get the data row (next row after header)
            data_row = table[header_row_idx + 1]
            
            # Extract date and amounts
            for cell in data_row:
                if not cell:
                    continue
                
                cell_str = str(cell).strip()
                
                # Check if it's a date (DD/MM/YYYY format)
                if re.match(r'\d{2}/\d{2}/\d{4}', cell_str):
                    result['payment_due_date'] = self.normalize_date(cell_str)
                
                # Check if it's an amount (with commas)
                elif re.match(r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?', cell_str):
                    if result['total_due'] is None:  # First amount is total dues
                        result['total_due'] = cell_str
            
            self.logger.info(f"Extracted from payment table: {result}")
        
        except Exception as e:
            self.logger.error(f"Error parsing payment table: {str(e)}")
        
        return result
    
    def _parse_credit_limit_table(self, table: List) -> Optional[str]:
        """
        Parse the credit limit table.
        
        Expected format:
        Row 1: "Credit Limit | Available Credit Limit | Available Cash Limit"
        Row 2: "30,000 | 0.00 | 0.00"
        """
        try:
            # Find header row
            header_row_idx = None
            for idx, row in enumerate(table):
                row_text = ' '.join(str(cell) for cell in row if cell)
                if "Credit Limit" in row_text:
                    header_row_idx = idx
                    break
            
            if header_row_idx is None or header_row_idx + 1 >= len(table):
                return None
            
            # Get the data row
            data_row = table[header_row_idx + 1]
            
            # First cell should be the credit limit
            if data_row and data_row[0]:
                limit = str(data_row[0]).strip()
                # Validate it's a number
                if re.match(r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?', limit):
                    self.logger.info(f"Extracted credit limit from table: {limit}")
                    return limit
        
        except Exception as e:
            self.logger.error(f"Error parsing credit limit table: {str(e)}")
        
        return None
    
    def _parse_card_number_table(self, table: List) -> Optional[str]:
        """
        Parse card number from table.
        
        Expected format somewhere in table:
        "Card No: 4695 25XX XXXX 3458"
        """
        try:
            for row in table:
                for cell in row:
                    if not cell:
                        continue
                    
                    cell_str = str(cell)
                    if "Card No" in cell_str:
                        # Extract last 4 digits
                        match = re.search(r'(\d{4})(?:\s|$)', cell_str)
                        if match:
                            last_4 = match.group(1)
                            self.logger.info(f"Extracted card number from table: {last_4}")
                            return last_4
        
        except Exception as e:
            self.logger.error(f"Error parsing card number table: {str(e)}")
        
        return None
    
        # Keep the original text-based extraction methods as fallbacks
    def _extract_cardholder_name(self, text: str) -> Optional[str]:
        """Extract cardholder name from HDFC statement (text only)."""
        
        # Pattern 1: Look for "Name : FIRSTNAME LASTNAME" in the jumbled line
        # Line 8: "000Paytm H N DF a C m Ban e k Credit Ca : rd NIKHIL KHANDELWAL Statement"
        pattern1 = r'[Nn]ame\s*:\s*([A-Z][A-Z\s]+?)(?:\s+Statement)'
        match = re.search(pattern1, text)
        if match:
            name = match.group(1).strip()
            words = name.split()
            if 2 <= len(words) <= 5 and all(len(w) > 1 for w in words):
                self.logger.info(f"Extracted name (pattern 1): {name}")
                return name
        
        # Pattern 2: Look for pattern with "rd : NAME Statement"
        pattern2 = r'rd\s*:\s*([A-Z][A-Z\s]+?)\s+Statement'
        match = re.search(pattern2, text)
        if match:
            name = match.group(1).strip()
            words = name.split()
            if 2 <= len(words) <= 5:
                self.logger.info(f"Extracted name (pattern 2): {name}")
                return name
        
        # Pattern 3: Look for "000" prefix followed by jumbled text with name
        # Extract capital words between "rd" and "Statement"
        pattern3 = r'000.*?rd[^A-Z]*([A-Z]+\s+[A-Z]+)\s+Statement'
        match = re.search(pattern3, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            words = name.split()
            if 2 <= len(words) <= 5:
                self.logger.info(f"Extracted name (pattern 3): {name}")
                return name
        
        # Pattern 4: More aggressive - look for 2-4 capitalized words before "Statement"
        pattern4 = r'\b([A-Z]{3,}\s+[A-Z]{3,}(?:\s+[A-Z]{3,})?)\s+Statement\s+for\s+HDFC'
        match = re.search(pattern4, text)
        if match:
            name = match.group(1).strip()
            words = name.split()
            if 2 <= len(words) <= 5:
                self.logger.info(f"Extracted name (pattern 4): {name}")
                return name
        
        self.logger.warning("Could not extract HDFC cardholder name")
        return None
    
    def _extract_credit_limit(self, text: str) -> Optional[str]:
        """Extract credit limit from HDFC statement (text fallback)."""
        # ... (keep the original implementation)
        pattern = r'Credit\s+Limit\s+Available\s+Credit\s+Limit[^\n]*\n[^\d]*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            limit = match.group(1)
            self.logger.info(f"Extracted credit limit: {limit}")
            return limit
        
        self.logger.warning("Could not extract HDFC credit limit")
        return None
    
    def _extract_total_due(self, text: str) -> Optional[str]:
        """Extract total due from HDFC statement (text fallback)."""
        # ... (keep the original implementation)
        pattern = r'Payment\s+Due\s+Date\s+Total\s+Dues\s+Minimum\s+Amount\s+Due[^\n]*\n[^\d]*?(\d{2}/\d{2}/\d{4})\s+(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount = match.group(2)
            self.logger.info(f"Extracted total due: {amount}")
            return amount
        
        self.logger.warning("Could not extract HDFC total due")
        return None

    def _extract_payment_due_date(self, text: str) -> Optional[str]:
        """Extract payment due date from HDFC statement (text fallback)."""
        # ... (keep the original implementation)
        pattern = r'Payment\s+Due\s+Date\s+Total\s+Dues[^\n]*\n[^\d]*?(\d{2}/\d{2}/\d{4})'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(1)
            normalized = self.normalize_date(date_str)
            if normalized:
                self.logger.info(f"Extracted payment due date: {normalized}")
                return normalized
        
        self.logger.warning("Could not extract HDFC payment due date")
        return None