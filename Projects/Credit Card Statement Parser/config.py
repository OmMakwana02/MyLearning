# config.py
import os
from pathlib import Path

# Base directory (project root)
BASE_DIR = Path(__file__).parent

# Directory paths
UPLOAD_FOLDER = BASE_DIR / 'uploads'
OUTPUT_FOLDER = BASE_DIR / 'output'

# Create directories if they don't exist
UPLOAD_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)

# File upload settings
ALLOWED_EXTENSIONS = {'pdf'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB in bytes
MAX_FILES = 5  # Maximum number of PDFs to upload at once

# Output file names
JSON_OUTPUT = OUTPUT_FOLDER / 'parsed_data.json'
CSV_OUTPUT = OUTPUT_FOLDER / 'parsed_data.csv'

# Supported banks
SUPPORTED_BANKS = ['axis', 'citi', 'hdfc', 'icici', 'silk']

# OCR Configuration (Tesseract & Poppler)
# Detect OS and set appropriate paths
import platform

if platform.system() == 'Windows':
    # Windows paths
    TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    POPPLER_PATH = r"C:\poppler-25.07.0\Library\bin"
else:
    # Linux/Mac paths (usually installed via package manager)
    TESSERACT_PATH = "tesseract"  # Should be in PATH
    POPPLER_PATH = None  # Not needed if installed via apt/brew

# PDF Processing settings
USE_OCR_FALLBACK = True  # Whether to use OCR if text extraction fails
MIN_TEXT_LENGTH = 50  # Minimum characters to consider extraction successful

# Logging configuration
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'