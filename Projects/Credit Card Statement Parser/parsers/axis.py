# axis.py
import re
import logging
from typing import Dict, Optional, List
from .base import BaseParser
import config

logging.basicConfig(level=logging.INFO, format=config.LOG_FORMAT)
logger = logging.getLogger(__name__)


class AxisParser(BaseParser):
    """
    Parser for Axis Bank Credit Card Statements.
    Uses table extraction first, falls back to text extraction.
    """
    
    BANK_NAME = "axis"
    
    def parse(self, text: str, tables: Optional[List] = None) -> Dict[str, Optional[str]]:
        """Parse Axis Bank credit card statement."""
        self.logger.info("Parsing Axis Bank statement...")
        
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
        Extract all 5 data points from AXIS tables.
        
        AXIS table structure:
        PAYMENT SUMMARY table:
        - Headers: Total Payment Due | Minimum Payment Due | Statement Period | Payment Due Date | ...
        - Values: 78,708.38 Dr | 3,936.00 Dr | 17/09/2021 - 15/10/2021 | 04/11/2021 | 15/10/2021
        
        Credit details table:
        - Headers: Credit Card Number | Credit Limit | Available Credit Limit | ...
        - Values: 533467******7381 | 132,000.00 | 30,641.86 | ...
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
            
            # Extract Payment Summary data
            if "Total Payment Due" in table_text and "Payment Due Date" in table_text:
                extracted_data.update(self._parse_payment_summary_table(table))
            
            # Extract Credit details
            if "Credit Card Number" in table_text and "Credit Limit" in table_text:
                credit_data = self._parse_credit_table(table)
                extracted_data['card_number'] = credit_data.get('card_number')
                extracted_data['credit_limit'] = credit_data.get('credit_limit')
        
        return extracted_data
    
    def _parse_payment_summary_table(self, table: List) -> Dict[str, Optional[str]]:
        """
        Parse AXIS payment summary table.
        
        Expected format:
        Row 1: "Total Payment Due | Minimum Payment Due | Statement Period | Payment Due Date | ..."
        Row 2: "78,708.38 Dr | 3,936.00 Dr | 17/09/2021 - 15/10/2021 | 04/11/2021 | ..."
        """
        result = {'total_due': None, 'payment_due_date': None}
        
        try:
            header_row_idx = None
            for idx, row in enumerate(table):
                row_text = ' '.join(str(cell) for cell in row if cell)
                if "Total Payment Due" in row_text and "Payment Due Date" in row_text:
                    header_row_idx = idx
                    break
            
            if header_row_idx is None or header_row_idx + 1 >= len(table):
                return result
            
            data_row = table[header_row_idx + 1]
            
            # Parse cells
            for i, cell in enumerate(data_row):
                if not cell:
                    continue
                
                cell_str = str(cell).strip()
                
                # Total Due: first amount with "Dr" suffix
                if "Dr" in cell_str and result['total_due'] is None:
                    amount_match = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', cell_str)
                    if amount_match:
                        result['total_due'] = amount_match.group(1)
                
                # Payment Due Date: DD/MM/YYYY format (not a date range)
                if re.match(r'^\d{2}/\d{2}/\d{4}$', cell_str):
                    result['payment_due_date'] = self.normalize_date(cell_str)
            
            self.logger.info(f"Extracted from payment summary: {result}")
        
        except Exception as e:
            self.logger.error(f"Error parsing payment summary: {str(e)}")
        
        return result
    
    def _parse_credit_table(self, table: List) -> Dict[str, Optional[str]]:
        """
        Parse AXIS credit details table.
        
        Expected format:
        Row 1: "Credit Card Number | Credit Limit | Available Credit Limit | ..."
        Row 2: "533467******7381 | 132,000.00 | 30,641.86 | ..."
        """
        result = {'card_number': None, 'credit_limit': None}
        
        try:
            header_row_idx = None
            for idx, row in enumerate(table):
                row_text = ' '.join(str(cell) for cell in row if cell)
                if "Credit Card Number" in row_text and "Credit Limit" in row_text:
                    header_row_idx = idx
                    break
            
            if header_row_idx is None or header_row_idx + 1 >= len(table):
                return result
            
            data_row = table[header_row_idx + 1]
            
            for cell in data_row:
                if not cell:
                    continue
                
                cell_str = str(cell).strip()
                
                # Card number: masked format (6 digits + ****** + 4 digits)
                if re.match(r'\d{6}\*+\d{4}', cell_str):
                    last_4 = re.findall(r'\d{4}$', cell_str)
                    if last_4:
                        result['card_number'] = last_4[0]
                
                # Credit limit: first large number (> 10,000)
                amount_match = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', cell_str)
                if amount_match and result['credit_limit'] is None:
                    limit = amount_match.group(1)
                    try:
                        if float(limit.replace(',', '')) > 10000:
                            result['credit_limit'] = limit
                    except ValueError:
                        pass
            
            self.logger.info(f"Extracted from credit table: {result}")
        
        except Exception as e:
            self.logger.error(f"Error parsing credit table: {str(e)}")
        
        return result
    
    # TEXT FALLBACK METHODS (Keep original implementations)
    
    def _extract_cardholder_name(self, text: str) -> Optional[str]:
        """Extract cardholder name from Axis statement (text fallback)."""
        pattern1 = r'Name\s+([A-Z][A-Z\s]+?)(?:\n|$)'
        match = re.search(pattern1, text)
        if match:
            name = match.group(1).strip()
            if 2 <= len(name.split()) <= 5:
                self.logger.info(f"Extracted name (pattern 1): {name}")
                return name
        
        self.logger.warning("Using generic name extraction for Axis")
        return self.extract_cardholder_name(text)
    
    def _extract_card_number(self, text: str) -> Optional[str]:
        """Extract card number from Axis statement (text fallback)."""
        patterns = [
            r'(?:Card\s+No:?\s+)?(\d{6}\*+\d{4})',
            r'Credit\s+Card\s+Number\s+.*?\s+(\d{6}\*+\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                full_card = match.group(1)
                last_4 = re.findall(r'\d{4}$', full_card)
                if last_4:
                    self.logger.info(f"Extracted card number: {last_4[0]}")
                    return last_4[0]
        
        self.logger.warning("Could not extract Axis card number")
        return None
    
    def _extract_credit_limit(self, text: str) -> Optional[str]:
        """Extract credit limit from Axis statement (text fallback)."""
        pattern = r'\d{6}\*+\d{4}\s+(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s+(?:\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s+(?:\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        match = re.search(pattern, text)
        
        if match:
            limit = match.group(1)
            limit_val = float(limit.replace(',', ''))
            if limit_val > 10000:
                self.logger.info(f"Extracted credit limit: {limit}")
                return limit
        
        self.logger.warning("Could not extract Axis credit limit")
        return None
    
    def _extract_total_due(self, text: str) -> Optional[str]:
        """Extract total payment due from Axis statement (text fallback)."""
        patterns = [
            r'Total\s+Payment\s+Due\s+Minimum\s+Payment\s+Due.*?\n\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s+Dr',
            r'Total\s+Payment\s+Due[^\d]*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s+Dr',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                amount = match.group(1)
                self.logger.info(f"Extracted total due: {amount}")
                return amount
        
        self.logger.warning("Could not extract Axis total due")
        return None
    
    def _extract_payment_due_date(self, text: str) -> Optional[str]:
        """Extract payment due date from Axis statement (text fallback)."""
        pattern = r'Payment\s+Due\s+Date[^\d]*?(\d{2}/\d{2}/\d{4})'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(1)
            normalized = self.normalize_date(date_str)
            if normalized:
                self.logger.info(f"Extracted payment due date: {normalized}")
                return normalized
        
        self.logger.warning("Could not extract Axis payment due date")
        return None