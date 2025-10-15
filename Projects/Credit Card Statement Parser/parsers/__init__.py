# parsers/__init__.py
"""
Credit card statement parsers package.
Contains bank-specific parsers and bank detection logic.
"""

from .bank_detector import detect_bank, detect_bank_with_confidence, BankDetector
from .base import BaseParser, GenericParser
from .axis import AxisParser
from .citi import CitiParser
from .hdfc import HdfcParser
from .icici import IciciParser
from .silk import SilkParser

__all__ = [
    'detect_bank', 
    'detect_bank_with_confidence', 
    'BankDetector',
    'BaseParser',
    'GenericParser',
    'AxisParser',
    'CitiParser',
    'HdfcParser',
    'IciciParser',
    'SilkParser',
]