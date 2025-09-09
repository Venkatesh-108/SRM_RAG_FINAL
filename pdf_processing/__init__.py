"""
PDF Extraction Toolkit
A reusable package for extracting and searching PDF documents with font-based heading detection.
"""

__version__ = "1.0.0"
__author__ = "PDF Extraction Toolkit"

from .extractor import PDFExtractor
from .searcher import PDFSearcher
from .processor import PDFProcessor

__all__ = ['PDFExtractor', 'PDFSearcher', 'PDFProcessor']
