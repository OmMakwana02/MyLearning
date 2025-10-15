# icici.py
import re
import logging
from typing import Dict, Optional, List
from .base import BaseParser
import config

logging.basicConfig(level=logging.INFO, format=config.LOG_FORMAT)
logger = logging.getLogger(__name__)


class IciciParser(BaseParser):
    """
    Parser for ICICI Bank Credit Card Statements.
    Uses table extraction first, falls back to text extraction.
    """
    
    BANK_NAME = "icici"
    
    def parse(self, text: str, tables: Optional[List] = None) -> Dict[str, Optional[str]]:
        """Parse ICICI Bank credit card statement."""
        self.logger.info("Parsing ICICI Bank statement...")
        
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
        Extract data from ICICI tables.
        
        ICICI structure:
        Credit summary:
        - Credit Limit (Including cash) | Available Credit | Cash Limit | Available Cash
        - `60,000.00 | `46,503.20 | `6,000.00 | `0.00
        
        Statement summary (with rupee symbol `)
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
            if "Credit Limit" in table_text and "Including cash" in table_text:
                extracted_data['credit_limit'] = self._parse_credit_limit_table(table)
            
            # Extract total due
            if "Total Amount due" in table_text or "Total Dues" in table_text:
                extracted_data['total_due'] = self._parse_total_due_table(table)
            
            # Extract payment due date
            if "PAYMENT DUE DATE" in table_text or "Payment Due Date" in table_text:
                extracted_data['payment_due_date'] = self._parse_payment_date_table(table)
        
        return extracted_data
    
    def _parse_credit_limit_table(self, table: List) -> Optional[str]:
        """Parse credit limit from ICICI table."""
        try:
            for idx, row in enumerate(table):
                row_text = ' '.join(str(cell) for cell in row if cell)
                
                if "Credit Limit" in row_text and "Including cash" in row_text:
                    if idx + 1 < len(table):
                        data_row = table[idx + 1]
                        
                        # First cell is credit limit (with ` symbol)
                        if data_row and data_row[0]:
                            limit = str(data_row[0]).strip()
                            # Remove rupee symbol
                            limit = limit.replace('`', '').strip()
                            
                            if re.match(r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?', limit):
                                self.logger.info(f"Extracted credit limit: {limit}")
                                return limit
        except Exception as e:
            self.logger.error(f"Error parsing credit limit: {str(e)}")
        
        return None
    
    def _parse_total_due_table(self, table: List) -> Optional[str]:
        """Parse total amount due from ICICI table."""
        try:
            for row in table:
                row_text = ' '.join(str(cell) for cell in row if cell)
                
                if "Total Amount due" in row_text:
                    # Extract amounts (with ` symbol)
                    amounts = re.findall(r'`(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', row_text)
                    if amounts:
                        self.logger.info(f"Extracted total due: {amounts[0]}")
                        return amounts[0]
        except Exception as e:
            self.logger.error(f"Error parsing total due: {str(e)}")
        
        return None
    
    def _parse_payment_date_table(self, table: List) -> Optional[str]:
        """Parse payment due date from ICICI table."""
        try:
            for row in table:
                row_text = ' '.join(str(cell) for cell in row if cell)
                
                if "PAYMENT DUE DATE" in row_text or "Payment Due Date" in row_text:
                    # ICICI uses format like "September 5, 2022"
                    date_match = re.search(r'([A-Z][a-z]+\s+\d{1,2},\s+\d{4})', row_text)
                    if date_match:
                        date_str = date_match.group(1)
                        normalized = self.normalize_date(date_str)
                        if normalized:
                            self.logger.info(f"Extracted payment due date: {normalized}")
                            return normalized
        except Exception as e:
            self.logger.error(f"Error parsing payment date: {str(e)}")
        
        return None
    
    # TEXT FALLBACK METHODS
    
    def _extract_cardholder_name(self, text: str) -> Optional[str]:
        """Extract cardholder name (text fallback)."""
        pattern = r'^(?:MR|MS|MRS|DR)\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        match = re.search(pattern, text, re.MULTILINE)
        if match:
            name = match.group(0).strip()
            self.logger.info(f"Extracted name: {name}")
            return name
        
        self.logger.warning("Could not extract ICICI cardholder name")
        return self.extract_cardholder_name(text)
    
    def _extract_card_number(self, text: str) -> Optional[str]:
        """Extract card number (text fallback)."""
        pattern = r'\b(\d{4}X{8}\d{4})\b'
        match = re.search(pattern, text)
        if match:
            full_card = match.group(1)
            last_4 = full_card[-4:]
            self.logger.info(f"Extracted card number: {last_4}")
            return last_4
        
        self.logger.warning("Could not extract ICICI card number")
        return None
    
    def _extract_credit_limit(self, text: str) -> Optional[str]:
        """Extract credit limit (text fallback)."""
        pattern = r'Credit\s+Limit\s+\(Including\s+cash\)[^\n]*\n[^\d]*?`(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            limit = match.group(1)
            self.logger.info(f"Extracted credit limit: {limit}")
            return limit
        
        self.logger.warning("Could not extract ICICI credit limit")
        return None
    
    def _extract_total_due(self, text: str) -> Optional[str]:
        """Extract total due (text fallback)."""
        pattern = r'Total\s+Amount\s+due\s*\n[^\d]*?`(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount = match.group(1)
            self.logger.info(f"Extracted total due: {amount}")
            return amount
        
        self.logger.warning("Could not extract ICICI total due")
        return None
    
    def _extract_payment_due_date(self, text: str) -> Optional[str]:
        """Extract payment due date (text fallback)."""
        pattern = r'P+A+Y+M+E+N+T+\s+D+U+E+\s+D+A+T+E+[^\n]*\n\s*([A-Z][a-z]+\s+\d{1,2},\s+\d{4})'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(1)
            normalized = self.normalize_date(date_str)
            if normalized:
                self.logger.info(f"Extracted payment due date: {normalized}")
                return normalized
        
        self.logger.warning("Could not extract ICICI payment due date")
        return None