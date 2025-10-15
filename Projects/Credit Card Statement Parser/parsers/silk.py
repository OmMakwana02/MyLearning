# silk.py
import re
import logging
from typing import Dict, Optional, List
from .base import BaseParser
import config

logging.basicConfig(level=logging.INFO, format=config.LOG_FORMAT)
logger = logging.getLogger(__name__)


class SilkParser(BaseParser):
    """
    Parser for Silk Bank Credit Card Statements.
    Uses table extraction first, falls back to text extraction.
    """
    
    BANK_NAME = "silk"
    
    def parse(self, text: str, tables: Optional[List] = None) -> Dict[str, Optional[str]]:
        """Parse Silk Bank credit card statement."""
        self.logger.info("Parsing Silk Bank statement...")
        
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
        Extract data from SILK tables.
        
        SILK structure:
        Header table:
        - Cardholder's Name | Card Number | Statement Date | Payment Due Date
        - RIZWAN AHMED | 4588 2600 0161 4868 | 20-Mar-2018 | 10-Apr-2018
        
        Summary table:
        - Total Credit Limit | Available Credit Limit | ...
        - 35,000.00 | 19,047.78 | ...
        
        - Current Balance
        - 12,144.55
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
            
            # Extract from header table
            if "Cardholder" in table_text and "Card Number" in table_text:
                header_data = self._parse_header_table(table)
                extracted_data['cardholder_name'] = header_data.get('cardholder_name')
                extracted_data['card_number'] = header_data.get('card_number')
                extracted_data['payment_due_date'] = header_data.get('payment_due_date')
            
            # Extract credit limit
            if "Total Credit Limit" in table_text or "Credit Limit" in table_text:
                extracted_data['credit_limit'] = self._parse_credit_limit_table(table)
            
            # Extract total due (Current Balance)
            if "Current Balance" in table_text or "Minimum Amount Due" in table_text:
                extracted_data['total_due'] = self._parse_total_due_table(table)
        
        return extracted_data
    
    def _parse_header_table(self, table: List) -> Dict[str, Optional[str]]:
        """Parse SILK header table."""
        result = {'cardholder_name': None, 'card_number': None, 'payment_due_date': None}
        
        try:
            header_row_idx = None
            for idx, row in enumerate(table):
                row_text = ' '.join(str(cell) for cell in row if cell)
                if "Cardholder" in row_text and "Card Number" in row_text:
                    header_row_idx = idx
                    break
            
            if header_row_idx is None or header_row_idx + 1 >= len(table):
                return result
            
            data_row = table[header_row_idx + 1]
            
            for cell in data_row:
                if not cell:
                    continue
                
                cell_str = str(cell).strip()
                
                # Cardholder name: All caps words
                if re.match(r'^[A-Z][A-Z\s]+$', cell_str) and len(cell_str.split()) <= 5:
                    result['cardholder_name'] = cell_str
                
                # Card number: 4-4-4-4 format
                if re.match(r'\d{4}\s+\d{4}\s+\d{4}\s+\d{4}', cell_str):
                    last_4 = re.findall(r'\d{4}', cell_str)[-1]
                    result['card_number'] = last_4
                
                # Payment due date: DD-Mon-YYYY format
                if re.match(r'\d{2}-[A-Z][a-z]{2}-\d{4}', cell_str):
                    result['payment_due_date'] = self.normalize_date(cell_str)
            
            self.logger.info(f"Extracted from header: {result}")
        
        except Exception as e:
            self.logger.error(f"Error parsing header table: {str(e)}")
        
        return result
    
    def _parse_credit_limit_table(self, table: List) -> Optional[str]:
        """Parse credit limit from SILK table."""
        try:
            for idx, row in enumerate(table):
                row_text = ' '.join(str(cell) for cell in row if cell)
                
                if "Total Credit Limit" in row_text or "Credit Limit" in row_text:
                    # Credit limit could be in same row or next row
                    amounts = re.findall(r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?', row_text)
                    
                    for amount in amounts:
                        limit_val = float(amount.replace(',', ''))
                        if 5000 < limit_val < 10000000:
                            self.logger.info(f"Extracted credit limit: {amount}")
                            return amount
                    
                    # Check next row
                    if idx + 1 < len(table):
                        data_row = table[idx + 1]
                        for cell in data_row:
                            if cell:
                                cell_str = str(cell).strip()
                                if re.match(r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?', cell_str):
                                    limit_val = float(cell_str.replace(',', ''))
                                    if 5000 < limit_val < 10000000:
                                        self.logger.info(f"Extracted credit limit: {cell_str}")
                                        return cell_str
        
        except Exception as e:
            self.logger.error(f"Error parsing credit limit: {str(e)}")
        
        return None
    
    def _parse_total_due_table(self, table: List) -> Optional[str]:
        """Parse total due (Current Balance) from SILK table."""
        try:
            for idx, row in enumerate(table):
                row_text = ' '.join(str(cell) for cell in row if cell)
                
                if "Current Balance" in row_text:
                    # Extract amount from same row or next row
                    amounts = re.findall(r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?', row_text)
                    if amounts:
                        self.logger.info(f"Extracted total due: {amounts[-1]}")
                        return amounts[-1]
                    
                    # Check next row
                    if idx + 1 < len(table):
                        data_row = table[idx + 1]
                        for cell in data_row:
                            if cell:
                                cell_str = str(cell).strip()
                                if re.match(r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?', cell_str):
                                    self.logger.info(f"Extracted total due: {cell_str}")
                                    return cell_str
        
        except Exception as e:
            self.logger.error(f"Error parsing total due: {str(e)}")
        
        return None
    
    # TEXT FALLBACK METHODS
    
    def _extract_cardholder_name(self, text: str) -> Optional[str]:
        """Extract cardholder name (text fallback)."""
        pattern = r"Cardholder'?s?\s+Name[^\n]*\n\s*([A-Z][A-Z\s]+?)\s+\d{4}"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if 2 <= len(name.split()) <= 5:
                self.logger.info(f"Extracted name: {name}")
                return name
        
        self.logger.warning("Could not extract Silk cardholder name")
        return self.extract_cardholder_name(text)
    
    def _extract_card_number(self, text: str) -> Optional[str]:
        """Extract card number (text fallback)."""
        pattern = r'Card\s+Number[^\n]*\n[^\d]*?(\d{4})\s+(\d{4})\s+(\d{4})\s+(\d{4})'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            last_4 = match.group(4)
            self.logger.info(f"Extracted card number: {last_4}")
            return last_4
        
        self.logger.warning("Could not extract Silk card number")
        return None
    
    def _extract_credit_limit(self, text: str) -> Optional[str]:
        """Extract credit limit (text fallback)."""
        pattern = r'(\d{4})\s+(\d{4})\s+(\d{4})\s+(\d{4})\s+(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        match = re.search(pattern, text)
        
        if match:
            limit = match.group(5)
            try:
                limit_val = float(limit.replace(',', ''))
                if 5000 < limit_val < 10000000:
                    self.logger.info(f"Extracted credit limit: {limit}")
                    return limit
            except ValueError:
                pass
        
        self.logger.warning("Could not extract Silk credit limit")
        return None
    
    def _extract_total_due(self, text: str) -> Optional[str]:
        """Extract total due (text fallback)."""
        pattern = r'=\s*Current\s+Balance\s*\n[^\d]*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount = match.group(1)
            self.logger.info(f"Extracted total due: {amount}")
            return amount
        
        self.logger.warning("Could not extract Silk total due")
        return None
    
    def _extract_payment_due_date(self, text: str) -> Optional[str]:
        """Extract payment due date (text fallback)."""
        pattern = r'Statement\s+Date\s+Payment\s+Due\s+Date[^\n]*\n[^\d]*?\d{4}\s+(\d{2}-[A-Z][a-z]{2}-\d{4})\s+(\d{2}-[A-Z][a-z]{2}-\d{4})'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(2)  # Second date is payment due date
            normalized = self.normalize_date(date_str)
            if normalized:
                self.logger.info(f"Extracted payment due date: {normalized}")
                return normalized
        
        self.logger.warning("Could not extract Silk payment due date")
        return None