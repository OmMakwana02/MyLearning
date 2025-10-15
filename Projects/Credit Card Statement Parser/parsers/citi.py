# citi.py
import re
import logging
from typing import Dict, Optional, List
from .base import BaseParser
import config

logging.basicConfig(level=logging.INFO, format=config.LOG_FORMAT)
logger = logging.getLogger(__name__)


class CitiParser(BaseParser):
    """
    Parser for Citibank Credit Card Statements.
    Uses table extraction first, falls back to text extraction.
    """
    
    BANK_NAME = "citi"
    
    def parse(self, text: str, tables: Optional[List] = None) -> Dict[str, Optional[str]]:
        """Parse [BANK NAME] credit card statement."""
        self.logger.info("Parsing CITI BANK statement...")
        
        # Initialize result
        result = {
            'cardholder_name': None,
            'card_number': None,
            'credit_limit': None,
            'total_due': None,
            'payment_due_date': None,
        }
            
        # ALWAYS extract name from text first (more reliable than tables)
        result['cardholder_name'] = self._extract_cardholder_name(text)
        
        # Try table extraction for OTHER fields
        if tables:
            self.logger.info("Attempting table-based extraction...")
            table_data = self._extract_from_tables(tables)
            
            # Update result with table data (but SKIP name from tables)
            for key, value in table_data.items():
                if value and key != 'cardholder_name':  # Don't overwrite name
                    result[key] = value
            
            # Check if we got all 5 fields
            if all(result.values()):
                self.logger.info("Successfully extracted all data")
                return result

        # Fill missing fields using text extraction (name already done)
        missing_fields = [k for k, v in result.items() if not v]
        if missing_fields:
            self.logger.info(f"Extracting missing fields from text: {missing_fields}")
            
            # Don't re-extract name
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
        Extract data from CITI tables.
        
        CITI structure:
        Summary table with headers:
        - ACCOUNT CREDIT LIMIT | AVAILABLE CREDIT LIMIT | CASH ADVANCE LIMIT | ...
        - 600,000.00 | 177,490.95 | 300,000.00 | ...
        
        Another table:
        - PREVIOUS BALANCE | (+) PURCHASES & ADVANCES | (-) CREDITS | (=) TOTAL AMOUNT DUE
        - 54,958.38 | 117,901.97 | 92,302.80 | 25,597.55
        """
        extracted_data = {
            'cardholder_name': None,
            'card_number': None,
            'credit_limit': None,
            'total_due': None,
            'payment_due_date': None,
        }
        
        for table in tables:
            if not table or len(table) < 2:
                continue
            
            table_text = '\n'.join([' '.join(str(cell) for cell in row if cell) for row in table])
            
            # Extract credit limit
            if "ACCOUNT" in table_text and "CREDIT LIMIT" in table_text:
                extracted_data['credit_limit'] = self._parse_credit_limit_table(table)
            
            # Extract total due
            if "TOTAL AMOUNT DUE" in table_text or "Total Amount Due" in table_text:
                extracted_data['total_due'] = self._parse_total_due_table(table)
            
            # Extract payment due date
            if "Payment Due Date" in table_text or "PAYMENT DUE DATE" in table_text:
                extracted_data['payment_due_date'] = self._parse_payment_date_table(table)
            
            # Extract card number
            if "Card Number" in table_text or "CardNumber" in table_text:
                extracted_data['card_number'] = self._parse_card_number_table(table)
        
        return extracted_data
    
    def _parse_credit_limit_table(self, table: List) -> Optional[str]:
        """Parse credit limit from CITI table."""
        try:
            for idx, row in enumerate(table):
                row_text = ' '.join(str(cell) for cell in row if cell)
                
                if "ACCOUNT" in row_text and "CREDIT LIMIT" in row_text:
                    if idx + 1 < len(table):
                        data_row = table[idx + 1]
                        
                        # First cell is usually the account credit limit
                        if data_row and data_row[0]:
                            limit = str(data_row[0]).strip()
                            if re.match(r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?', limit):
                                limit_val = float(limit.replace(',', ''))
                                if limit_val > 50000:
                                    self.logger.info(f"Extracted credit limit: {limit}")
                                    return limit
        except Exception as e:
            self.logger.error(f"Error parsing credit limit: {str(e)}")
        
        return None
    
    def _parse_total_due_table(self, table: List) -> Optional[str]:
        """Parse total amount due from CITI table."""
        try:
            for row in table:
                row_text = ' '.join(str(cell) for cell in row if cell)
                
                if "TOTAL AMOUNT DUE" in row_text or "Total Amount Due" in row_text:
                    # Extract amount from this row
                    amounts = re.findall(r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?', row_text)
                    if amounts:
                        # Usually the last amount in the row
                        self.logger.info(f"Extracted total due: {amounts[-1]}")
                        return amounts[-1]
        except Exception as e:
            self.logger.error(f"Error parsing total due: {str(e)}")
        
        return None
    
    def _parse_payment_date_table(self, table: List) -> Optional[str]:
        """Parse payment due date from CITI table."""
        try:
            for row in table:
                row_text = ' '.join(str(cell) for cell in row if cell)
                
                if "Payment Due Date" in row_text or "PAYMENT DUE DATE" in row_text:
                    # Extract date from this row
                    date_match = re.search(r'(\d{2}/\d{2}/\d{2,4})', row_text)
                    if date_match:
                        date_str = date_match.group(1)
                        normalized = self.normalize_date(date_str)
                        if normalized:
                            self.logger.info(f"Extracted payment due date: {normalized}")
                            return normalized
        except Exception as e:
            self.logger.error(f"Error parsing payment date: {str(e)}")
        
        return None
    
    def _parse_card_number_table(self, table: List) -> Optional[str]:
        """Parse card number from CITI table."""
        try:
            for row in table:
                for cell in row:
                    if not cell:
                        continue
                    
                    cell_str = str(cell)
                    
                    # Look for 4-4-4-4 format
                    match = re.search(r'(\d{4})-(\d{4})-(\d{4})-(\d{4})', cell_str)
                    if match:
                        last_4 = match.group(4)
                        self.logger.info(f"Extracted card number: {last_4}")
                        return last_4
        except Exception as e:
            self.logger.error(f"Error parsing card number: {str(e)}")
        
        return None
    
    # TEXT FALLBACK METHODS
    
    def _extract_cardholder_name(self, text: str) -> Optional[str]:
        """Extract cardholder name from Citi statement (text only)."""
        
        # Pattern 1: Name appears after the spaced-out card number line
        # Line 17: "* 4 3 1 6 0 1 4 8 0 2 6 3 2 0 4 8 2 2 2 3 3 6 7 0 7 C*"
        # Line 18: "ANTONIETALAPININGPABANELAS"
        # Line 19: "DEP-EDNAGA..."
        pattern1 = r'\*\s*[\d\s]+\s*C\*[^\n]*\n([A-Z]{15,})\n(?:DEP-|[A-Z]{2,}-)'
        match = re.search(pattern1, text)
        if match:
            name = match.group(1).strip()
            # Name might be all concatenated, try to split it
            self.logger.info(f"Extracted name (pattern 1): {name}")
            return name
        
        # Pattern 2: Look for all-caps text before "DEP-ED" or similar address
        pattern2 = r'\n([A-Z]{15,})\n(?:DEP-ED|AT/PO|POBLACION)'
        match = re.search(pattern2, text)
        if match:
            name = match.group(1).strip()
            self.logger.info(f"Extracted name (pattern 2): {name}")
            return name
        
        # Pattern 3: Between card pattern and address markers
        pattern3 = r'C\*[^\n]*\n([A-Z\s]{10,50}?)\n[A-Z]{2,}-[A-Z]'
        match = re.search(pattern3, text)
        if match:
            name = match.group(1).strip()
            self.logger.info(f"Extracted name (pattern 3): {name}")
            return name
        
        self.logger.warning("Could not extract Citi cardholder name")
        return None
    
    def _extract_card_number(self, text: str) -> Optional[str]:
        """Extract card number (text fallback)."""
        pattern = r'CardNumber\s*:\s*(\d{4})-(\d{4})-(\d{4})-(\d{4})'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            last_4 = match.group(4)
            self.logger.info(f"Extracted card number: {last_4}")
            return last_4
        
        self.logger.warning("Could not extract Citi card number")
        return None
    
    def _extract_credit_limit(self, text: str) -> Optional[str]:
        """Extract credit limit (text fallback)."""
        
        # Pattern 1: ACCOUNT CREDITLIMIT on one line, value on next
        pattern1 = r'ACCOUNT[^\n]*?CREDIT\s*LIMIT[^\n]*?\n\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            limit = match.group(1)
            try:
                limit_val = float(limit.replace(',', ''))
                if limit_val > 50000:
                    self.logger.info(f"Extracted credit limit (pattern 1): {limit}")
                    return limit
            except ValueError:
                pass
        
        # Pattern 2: Look in the summary section
        pattern2 = r'CREDIT\s*LIMIT[^\d]*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        matches = re.findall(pattern2, text, re.IGNORECASE)
        
        # Find the largest value (likely the account credit limit)
        for match in matches:
            try:
                limit_val = float(match.replace(',', ''))
                if limit_val > 50000:
                    self.logger.info(f"Extracted credit limit (pattern 2): {match}")
                    return match
            except ValueError:
                continue
        
        self.logger.warning("Could not extract Citi credit limit")
        return None
    
    def _extract_total_due(self, text: str) -> Optional[str]:
        """Extract total due (text fallback)."""
        pattern = r'TotalAmountDue\s*\(\s*\)\s*:\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount = match.group(1)
            self.logger.info(f"Extracted total due: {amount}")
            return amount
        
        self.logger.warning("Could not extract Citi total due")
        return None
    
    def _extract_payment_due_date(self, text: str) -> Optional[str]:
        """Extract payment due date (text fallback)."""
        pattern = r'PaymentDueDate\s*:\s*(\d{2}/\d{2}/\d{2,4})'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(1)
            normalized = self.normalize_date(date_str)
            if normalized:
                self.logger.info(f"Extracted payment due date: {normalized}")
                return normalized
        
        self.logger.warning("Could not extract Citi payment due date")
        return None