import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import config

logging.basicConfig(level=logging.INFO, format=config.LOG_FORMAT)
logger = logging.getLogger(__name__)


class DataIO:
    """
    Handles saving and loading parsed credit card data in JSON and CSV formats.
    """
    
    @staticmethod
    def save_to_json(data: List[Dict[str, Any]], output_path: Optional[Path] = None) -> Tuple[bool, str]:
        """
        Save parsed data to a JSON file.
        
        Args:
            data (List[Dict]): List of parsed bank statement dictionaries
            output_path (Path): Path to save JSON file (default: config.JSON_OUTPUT)
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        if output_path is None:
            output_path = config.JSON_OUTPUT
        
        output_path = Path(output_path)
        # Validate data first
        is_valid, msg = DataIO.validate_data(data)
        if not is_valid:
            logger.error(f"Data validation failed: {msg}")
            return False, f"Invalid data: {msg}"
        
        try:
            # Ensure directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Saving {len(data)} records to JSON: {output_path}")
            
            # Convert data to JSON-serializable format
            json_data = {
                'total_records': len(data),
                'statements': data
            }
            
            # Write to file with pretty formatting
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Successfully saved JSON file: {output_path}")
            return True, f"Data saved to {output_path}"
        
        except Exception as e:
            logger.error(f"Error saving JSON: {str(e)}")
            return False, f"Failed to save JSON: {str(e)}"
    
    @staticmethod
    def save_to_csv(data: List[Dict[str, Any]], output_path: Optional[Path] = None) -> Tuple[bool, str]:
        """
        Save parsed data to a CSV file.
        
        Args:
            data (List[Dict]): List of parsed bank statement dictionaries
            output_path (Path): Path to save CSV file (default: config.CSV_OUTPUT)
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        if output_path is None:
            output_path = config.CSV_OUTPUT
        
        output_path = Path(output_path)
        # Validate data first
        is_valid, msg = DataIO.validate_data(data)
        if not is_valid:
            logger.error(f"Data validation failed: {msg}")
            return False, f"Invalid data: {msg}"
        
        try:
            # Ensure directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Saving {len(data)} records to CSV: {output_path}")
            
            # Convert list of dicts to DataFrame
            df = pd.DataFrame(data)
            
            # Reorder columns for better readability
            column_order = [
                'bank',
                'filename',
                'cardholder_name',
                'card_number',
                'credit_limit',
                'total_due',
                'payment_due_date',
                'status'
            ]
            
            # Keep only columns that exist in the dataframe
            available_columns = [col for col in column_order if col in df.columns]

            # Add any extra columns not in our order (like 'errors', 'error_message')
            extra_columns = [col for col in df.columns if col not in column_order]
            all_columns = available_columns + extra_columns

            df = df[all_columns]
            
            # Write to CSV
            df.to_csv(output_path, index=False, encoding='utf-8')
            
            logger.info(f"Successfully saved CSV file: {output_path}")
            return True, f"Data saved to {output_path}"
        
        except Exception as e:
            logger.error(f"Error saving CSV: {str(e)}")
            return False, f"Failed to save CSV: {str(e)}"
    
    @staticmethod
    def save_both(data: List[Dict[str, Any]], 
                  json_path: Optional[Path] = None, 
                  csv_path: Optional[Path] = None) -> Dict[str, Tuple[bool, str]]:
        """
        Save data to both JSON and CSV files simultaneously.
        
        Args:
            data (List[Dict]): List of parsed bank statement dictionaries
            json_path (Path): Path for JSON output (default: config.JSON_OUTPUT)
            csv_path (Path): Path for CSV output (default: config.CSV_OUTPUT)
            
        Returns:
            Dict: Results for both saves
                {
                    'json': (success, message),
                    'csv': (success, message)
                }
        """
        logger.info(f"Saving data in both JSON and CSV formats...")
        
        results = {
            'json': DataIO.save_to_json(data, json_path),
            'csv': DataIO.save_to_csv(data, csv_path)
        }
        
        json_success, json_msg = results['json']
        csv_success, csv_msg = results['csv']
        
        if json_success and csv_success:
            logger.info("Successfully saved both JSON and CSV files")
        else:
            if not json_success:
                logger.warning(f"JSON save failed: {json_msg}")
            if not csv_success:
                logger.warning(f"CSV save failed: {csv_msg}")
        
        return results
    
    @staticmethod
    def load_json(json_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
        """
        Load data from a JSON file.
        
        Args:
            json_path (Path): Path to JSON file (default: config.JSON_OUTPUT)
            
        Returns:
            Optional[Dict]: Loaded data or None if error
        """
        if json_path is None:
            json_path = config.JSON_OUTPUT
        
        json_path = Path(json_path)
        
        try:
            if not json_path.exists():
                logger.warning(f"JSON file not found: {json_path}")
                return None
            
            logger.info(f"Loading JSON file: {json_path}")
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Successfully loaded {len(data.get('statements', []))} records from JSON")
            return data
        
        except Exception as e:
            logger.error(f"Error loading JSON: {str(e)}")
            return None
    
    @staticmethod
    def load_csv(csv_path: Optional[Path] = None) -> Optional[pd.DataFrame]:
        """
        Load data from a CSV file.
        
        Args:
            csv_path (Path): Path to CSV file (default: config.CSV_OUTPUT)
            
        Returns:
            Optional[DataFrame]: Loaded data or None if error
        """
        if csv_path is None:
            csv_path = config.CSV_OUTPUT
        
        csv_path = Path(csv_path)
        
        try:
            if not csv_path.exists():
                logger.warning(f"CSV file not found: {csv_path}")
                return None
            
            logger.info(f"Loading CSV file: {csv_path}")
            
            df = pd.read_csv(csv_path, encoding='utf-8')
            
            logger.info(f"Successfully loaded {len(df)} records from CSV")
            return df
        
        except Exception as e:
            logger.error(f"Error loading CSV: {str(e)}")
            return None
    
    @staticmethod
    def export_summary(data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a summary report of the parsed data.
        
        Args:
            data (List[Dict]): List of parsed bank statement dictionaries
            
        Returns:
            Dict: Summary statistics
        """
        total = len(data)
        successful = sum(1 for d in data if d.get('status') == 'success')
        partial = sum(1 for d in data if d.get('status') == 'partial')
        errors = sum(1 for d in data if d.get('status') == 'error')
        
        # Count by bank
        banks_data = {}
        for record in data:
            bank = record.get('bank', 'unknown')
            if bank not in banks_data:
                banks_data[bank] = {'success': 0, 'partial': 0, 'error': 0}
            
            status = record.get('status', 'error')
            banks_data[bank][status] = banks_data[bank].get(status, 0) + 1
        
        summary = {
            'total_records': total,
            'successful': successful,
            'partial': partial,
            'errors': errors,
            'success_rate': f"{(successful/total*100):.2f}%" if total > 0 else "0%",
            'by_bank': banks_data
        }
        
        return summary

    @staticmethod
    def print_summary(data: List[Dict[str, Any]]) -> None:
        """
        Print a formatted summary to console.
        
        Args:
            data: List of parsed statements
        """
        summary = DataIO.export_summary(data)
        
        print("\n" + "=" * 60)
        print("PARSING SUMMARY")
        print("=" * 60)
        print(f"Total Records:   {summary['total_records']}")
        print(f"Successful:      {summary['successful']}")
        print(f"Partial:         {summary['partial']}")
        print(f"Errors:          {summary['errors']}")
        print(f"Success Rate:    {summary['success_rate']}")
        
        print("\nBy Bank:")
        print("-" * 60)
        for bank, stats in summary['by_bank'].items():
            print(f"\n  {bank.upper()}:")
            print(f"    ✓ Success: {stats.get('success', 0)}")
            print(f"    ⚠ Partial: {stats.get('partial', 0)}")
            print(f"    ✗ Error:   {stats.get('error', 0)}")
        
        print("\n" + "=" * 60)

    @staticmethod
    def validate_data(data: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """
        Validate data before saving.
        
        Args:
            data (List[Dict]): Data to validate
            
        Returns:
            Tuple[bool, str]: (is_valid, message)
        """
        if not data:
            return False, "Data list is empty"
        
        if not isinstance(data, list):
            return False, "Data must be a list"
        
        required_fields = ['bank', 'filename', 'cardholder_name', 'card_number', 
                        'credit_limit', 'total_due', 'payment_due_date']
        
        for idx, record in enumerate(data):
            if not isinstance(record, dict):
                return False, f"Record {idx} is not a dictionary"
            
            missing_fields = [field for field in required_fields if field not in record]
            if missing_fields:
                logger.warning(f"Record {idx} missing fields: {missing_fields}")
        
        return True, "Data is valid"
    
    @staticmethod
    def create_detailed_report(data: List[Dict[str, Any]], 
                              output_path: Optional[Path] = None) -> Tuple[bool, str]:
        """
        Create a detailed text report of all parsed data.
        
        Args:
            data (List[Dict]): List of parsed bank statement dictionaries
            output_path (Path): Path to save report (default: output/report.txt)
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        if output_path is None:
            output_path = config.OUTPUT_FOLDER / 'report.txt'
        
        output_path = Path(output_path)
        
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Creating detailed report: {output_path}")
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("CREDIT CARD STATEMENT PARSER - DETAILED REPORT\n")
                f.write("=" * 80 + "\n\n")
                
                # Summary section
                summary = DataIO.export_summary(data)
                f.write("SUMMARY\n")
                f.write("-" * 80 + "\n")
                f.write(f"Total Records: {summary['total_records']}\n")
                f.write(f"Successful: {summary['successful']}\n")
                f.write(f"Partial: {summary['partial']}\n")
                f.write(f"Errors: {summary['errors']}\n")
                f.write(f"Success Rate: {summary['success_rate']}\n\n")
                
                # By Bank section
                f.write("RESULTS BY BANK\n")
                f.write("-" * 80 + "\n")
                for bank, stats in summary['by_bank'].items():
                    f.write(f"\n{bank.upper()}:\n")
                    f.write(f"  Successful: {stats['success']}\n")
                    f.write(f"  Partial: {stats['partial']}\n")
                    f.write(f"  Errors: {stats['error']}\n")
                
                # Detailed records section
                f.write("\n\n" + "=" * 80 + "\n")
                f.write("DETAILED RECORDS\n")
                f.write("=" * 80 + "\n")
                
                for idx, record in enumerate(data, start=1):
                    f.write(f"\nRECORD {idx}\n")
                    f.write("-" * 80 + "\n")
                    f.write(f"Bank: {record.get('bank', 'N/A')}\n")
                    f.write(f"Filename: {record.get('filename', 'N/A')}\n")
                    f.write(f"Status: {record.get('status', 'N/A')}\n")
                    f.write(f"Cardholder Name: {record.get('cardholder_name', 'N/A')}\n")
                    f.write(f"Card Number: {record.get('card_number', 'N/A')}\n")
                    f.write(f"Credit Limit: {record.get('credit_limit', 'N/A')}\n")
                    f.write(f"Total Due: {record.get('total_due', 'N/A')}\n")
                    f.write(f"Payment Due Date: {record.get('payment_due_date', 'N/A')}\n")
                    
                    if record.get('errors'):
                        f.write("Errors:\n")
                        for error in record['errors']:
                            f.write(f"  - {error}\n")
            
            logger.info(f"Successfully created report: {output_path}")
            return True, f"Report saved to {output_path}"
        
        except Exception as e:
            logger.error(f"Error creating report: {str(e)}")
            return False, f"Failed to create report: {str(e)}"


# Convenience functions for direct import

def save_json(data: List[Dict[str, Any]], 
              output_path: Optional[Path] = None) -> Tuple[bool, str]:
    """Convenience wrapper for DataIO.save_to_json()"""
    return DataIO.save_to_json(data, output_path)


def save_csv(data: List[Dict[str, Any]], 
             output_path: Optional[Path] = None) -> Tuple[bool, str]:
    """Convenience wrapper for DataIO.save_to_csv()"""
    return DataIO.save_to_csv(data, output_path)


def save_both(data: List[Dict[str, Any]], 
              json_path: Optional[Path] = None, 
              csv_path: Optional[Path] = None) -> Dict[str, Tuple[bool, str]]:
    """Convenience wrapper for DataIO.save_both()"""
    return DataIO.save_both(data, json_path, csv_path)


def load_json(json_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Convenience wrapper for DataIO.load_json()"""
    return DataIO.load_json(json_path)


def load_csv(csv_path: Optional[Path] = None) -> Optional[pd.DataFrame]:
    """Convenience wrapper for DataIO.load_csv()"""
    return DataIO.load_csv(csv_path)