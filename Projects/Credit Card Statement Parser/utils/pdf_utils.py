# utils/pdf_utils.py
from tarfile import ExtractError
import pdfplumber
import logging
from pathlib import Path
from typing import Optional, Tuple, List
import pytesseract
import config  

logging.basicConfig(level=logging.INFO, format=config.LOG_FORMAT)
logger = logging.getLogger(__name__)

def extract_text_with_pdfplumber(pdf_path: str) -> str:
    """
    Extract text from PDF using pdfplumber.
    Args: pdf_path (str)
    Returns: extracted text as string.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    extracted_text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            logger.info(f"PDF opened successfully. Total pages: {len(pdf.pages)}")

            for page_num, page in enumerate(pdf.pages, start=1):
                try:
                    page_text = page.extract_text()
                except Exception as e:
                    logger.warning(f"Error reading page {page_num}: {e}")
                    page_text = None

                if page_text:
                    extracted_text += f"\n--- Page {page_num} ---\n"
                    extracted_text += page_text
                else:
                    logger.warning(f"Page {page_num} returned empty text")

    except Exception as e:
        logger.error(f"Error extracting text with pdfplumber: {str(e)}")
        raise

    return extracted_text.strip()


def extract_text_with_ocr(pdf_path: str) -> str:
  """
  Extracts text from pdfs using OCR (for scanned/image-based PDFs).
  for this install pytesseract and pdf2image. 
  
  argument: path of pdf
  Return: string of extracted text.
  
  """
  import pytesseract
  # Use config path
  pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_PATH

  # Use config path
  POPPLER_PATH = config.POPPLER_PATH
  
  try:
    from pdf2image import convert_from_path
    import pytesseract
  except ImportError:
    logger.error("pytesseract or pdf2image not installed. Install with:")
    logger.error("pip install pytesseract pdf2image")
    raise ImportError("OCR dependencies not installed")

  try:
    logger.info("Converting PDF pages to images for OCR...")

    # Pass poppler_path only if it's set (Windows)
    if POPPLER_PATH:
      images = convert_from_path(pdf_path, poppler_path=POPPLER_PATH)
    else:
      images = convert_from_path(pdf_path)

    extracted_text = ""

    for page_num, image in enumerate(images, start=1):
      page_text = pytesseract.image_to_string(image)

      if page_text.strip():
        extracted_text += f"\n--- Page {page_num} ---\n"
        extracted_text += page_text
      else:
        logger.warning(f"Page {page_num} returned empty text")
    
    logger.info("OCR text extraction completed.")
    return extracted_text.strip()
  except Exception as e:
    logger.error(f"Error during OCR extraction: {str(e)}")
    raise

def is_text_based_pdf(pdf_path: str) -> bool:
  """
  Checks if pdf is text-based or image-based.
  
  argument: pdf_path
  Return: bool: True if based else False(if scanned/image_based)
  """

  try:
    with pdfplumber.open(pdf_path) as pdf:
      if len(pdf.pages) > 0:
        first_page = pdf.pages[0]
        text = first_page.extract_text()

      if text and len(text.strip()) > 100:
        logger.info("PDF is text-based.")
        return True
    
    logger.info("PDF detected as scanned/image-based")
    return False
  except Exception as e:
    logger.error(f"Error checking PDF type: {str(e)}")
    return False
  
def extract_text_from_pdf(pdf_path: str, use_ocr_fallback: bool = True) -> Tuple[str, str]:
  """
  This is the main funct, which extracts text from  pdf
  first it will try pdfplumber, 
  if it fails and use_ocr_fallback is True, it will try OCR method.

  Keyword arguments:
  argument: pdf_path (str), use_ocr_fallback (bool): whether to use OCR as fallback.
  Return: Tuple[str, str]: (extracted text, method used to extract text)
  """
  pdf_path = Path(pdf_path)

  if not pdf_path.exists():
    raise FileNotFoundError(f"PDF file not found: {pdf_path}")
  
  try:
    logger.info(f"Extracting text from: {pdf_path.name}")
    text = extract_text_with_pdfplumber(pdf_path)
    
    if text and len(text.strip()) > config.MIN_TEXT_LENGTH:
      logger.info("Successfully extracted text with pdfplumber")
      return text, "pdfplumber"
    else:
      logger.warning("pdfplumber returned insufficient text")

  except Exception as e:
    logger.warning(f"pdfplumber extraction failed: {str(e)}")

  if use_ocr_fallback:
    try:
        logger.info("Attempting OCR extraction as fallback...")
        text = extract_text_with_ocr(pdf_path)
        
        if text and len(text.strip()) > config.MIN_TEXT_LENGTH:
            logger.info("Successfully extracted text with OCR")
            return text, "ocr"
        else:
            logger.error("OCR also returned insufficient text")
            return "", "failed"
    
    except ImportError:
        logger.error("OCR fallback requested but dependencies not installed")
        return "", "failed"
    except Exception as e:
        logger.error(f"OCR extraction also failed: {str(e)}")
        return "", "failed"
  else:
      logger.error("PDF extraction failed and OCR fallback disabled")
      return "", "failed"

def validation_pdf(pdf_path: str) -> Tuple[bool, str]:
  """
  Validates the PDF file is readble and extractable.
  
  argument: pdf_path
  Return: Tuple[bool, str]: (is_valid, message)
  
  """

  pdf_path = Path(pdf_path)
  if not pdf_path.exists():
    return False, f"File not found: {pdf_path}"
  
  if pdf_path.suffix.lower() != '.pdf':
    return False, f"File is not a PDF: {pdf_path.suffix}"
  
  if pdf_path.stat().st_size == 0:
    return False, "PDF file is empty"
  
  try:
    with pdfplumber.open(pdf_path) as pdf:
      if len(pdf.pages) == 0:
        return False, "PDF has no pages"
      
    return True, "PDF is valid and readable"
  
  except Exception as e:
    return False, f"PDF validation failed: {str(e)}"

def extract_tables_from_pdf(pdf_path: str) -> List[List[List[str]]]:
    """
    Extract all tables from a PDF.
    
    Returns:
        List of tables, where each table is a list of rows,
        and each row is a list of cell values.
    """
    pdf_path = Path(pdf_path)
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            all_tables = []
            for page in pdf.pages:
                tables = page.extract_tables()
                if tables:
                    all_tables.extend(tables)
            return all_tables
    except Exception as e:
        logger.error(f"Error extracting tables: {str(e)}")
        return []