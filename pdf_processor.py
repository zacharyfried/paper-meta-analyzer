#!/usr/bin/env python
"""
PDF Processing Utilities for Research Papers
Extracts text content from academic PDF files using multiple methods.

Author: Zachary Fried
"""

import os
import logging
from typing import Optional, List, Dict
import pdfplumber
import PyPDF2
import fitz  # PyMuPDF
from pathlib import Path


class PDFProcessor:
    """
    Processes PDF files to extract text content for analysis.
    Supports multiple extraction methods with fallback options.
    """

    def __init__(self, log_file='pdf_processing.log'):
        """
        Initialize PDF processor with logging.

        Args:
            log_file: Path to log file
        """
        self.setup_logging(log_file)
        self.extraction_methods = {
            'pdfplumber': self._extract_with_pdfplumber,
            'pypdf2': self._extract_with_pypdf2,
            'pymupdf': self._extract_with_pymupdf
        }

    def setup_logging(self, log_file):
        """Set up logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def extract_text(self, pdf_path: str, method: str = 'auto') -> Optional[str]:
        """
        Extract text from PDF file.

        Args:
            pdf_path: Path to PDF file
            method: Extraction method ('pdfplumber', 'pypdf2', 'pymupdf', or 'auto')

        Returns:
            Extracted text or None if extraction fails
        """
        if not os.path.exists(pdf_path):
            self.logger.error(f"PDF file not found: {pdf_path}")
            return None

        if method == 'auto':
            # Try each method until one succeeds
            for method_name, extraction_func in self.extraction_methods.items():
                try:
                    text = extraction_func(pdf_path)
                    if text and len(text.strip()) > 100:  # Minimum viable text
                        self.logger.info(f"Successfully extracted text from {pdf_path} using {method_name}")
                        return text
                except Exception as e:
                    self.logger.warning(f"Method {method_name} failed for {pdf_path}: {e}")
                    continue

            self.logger.error(f"All extraction methods failed for {pdf_path}")
            return None

        elif method in self.extraction_methods:
            try:
                return self.extraction_methods[method](pdf_path)
            except Exception as e:
                self.logger.error(f"Extraction failed with {method} for {pdf_path}: {e}")
                return None
        else:
            self.logger.error(f"Unknown extraction method: {method}")
            return None

    def _extract_with_pdfplumber(self, pdf_path: str) -> str:
        """
        Extract text using pdfplumber (good for complex layouts).

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text
        """
        text = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)

        return '\n'.join(text)

    def _extract_with_pypdf2(self, pdf_path: str) -> str:
        """
        Extract text using PyPDF2 (fast but basic).

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text
        """
        text = []
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text.append(page.extract_text())

        return '\n'.join(text)

    def _extract_with_pymupdf(self, pdf_path: str) -> str:
        """
        Extract text using PyMuPDF (good balance of speed and accuracy).

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text
        """
        text = []
        doc = fitz.open(pdf_path)
        for page in doc:
            text.append(page.get_text())
        doc.close()

        return '\n'.join(text)

    def process_batch(self, pdf_paths: List[str], output_format: str = 'dict') -> Dict[str, str]:
        """
        Process multiple PDF files.

        Args:
            pdf_paths: List of PDF file paths
            output_format: Format for results ('dict' or 'list')

        Returns:
            Dictionary mapping file paths to extracted text
        """
        results = {}

        for pdf_path in pdf_paths:
            self.logger.info(f"Processing: {pdf_path}")
            text = self.extract_text(pdf_path)
            results[pdf_path] = text

        return results

    def check_pdf_readability(self, pdf_path: str) -> Dict[str, any]:
        """
        Check if PDF contains extractable text or is image-based.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary with readability information
        """
        info = {
            'path': pdf_path,
            'is_readable': False,
            'is_text_based': False,
            'page_count': 0,
            'text_length': 0,
            'extraction_method': None
        }

        if not os.path.exists(pdf_path):
            info['error'] = 'File not found'
            return info

        try:
            # Check with PyMuPDF (fastest for basic checks)
            doc = fitz.open(pdf_path)
            info['page_count'] = len(doc)

            text_found = False
            for page in doc:
                page_text = page.get_text()
                if page_text and len(page_text.strip()) > 50:
                    text_found = True
                    break

            doc.close()

            if text_found:
                # Try full extraction
                full_text = self.extract_text(pdf_path)
                if full_text:
                    info['is_readable'] = True
                    info['is_text_based'] = True
                    info['text_length'] = len(full_text)
                    info['extraction_method'] = 'auto'

        except Exception as e:
            info['error'] = str(e)

        return info

    def clean_text(self, text: str) -> str:
        """
        Clean extracted text for better processing.

        Args:
            text: Raw extracted text

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Remove excessive whitespace
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if line:  # Keep non-empty lines
                # Replace multiple spaces with single space
                line = ' '.join(line.split())
                cleaned_lines.append(line)

        # Join with single newline
        cleaned_text = '\n'.join(cleaned_lines)

        # Remove common artifacts
        replacements = {
            '\x00': '',  # Null bytes
            '\uf0b7': '•',  # Bullet points
            '\u2019': "'",  # Smart quotes
            '\u2018': "'",
            '\u201c': '"',
            '\u201d': '"',
            '\u2013': '-',  # En dash
            '\u2014': '--',  # Em dash
        }

        for old, new in replacements.items():
            cleaned_text = cleaned_text.replace(old, new)

        return cleaned_text


def main():
    """Example usage and testing."""
    import argparse

    parser = argparse.ArgumentParser(description='Process PDF files to extract text')
    parser.add_argument('pdf_path', help='Path to PDF file or directory')
    parser.add_argument('--method', default='auto',
                        choices=['auto', 'pdfplumber', 'pypdf2', 'pymupdf'],
                        help='Extraction method to use')
    parser.add_argument('--check', action='store_true',
                        help='Check PDF readability without full extraction')
    parser.add_argument('--output', help='Output text file (optional)')

    args = parser.parse_args()

    processor = PDFProcessor()

    if os.path.isfile(args.pdf_path):
        # Single file processing
        if args.check:
            info = processor.check_pdf_readability(args.pdf_path)
            print(f"PDF Readability Check:")
            for key, value in info.items():
                print(f"  {key}: {value}")
        else:
            text = processor.extract_text(args.pdf_path, method=args.method)
            if text:
                cleaned_text = processor.clean_text(text)
                print(f"Extracted {len(cleaned_text)} characters")

                if args.output:
                    with open(args.output, 'w', encoding='utf-8') as f:
                        f.write(cleaned_text)
                    print(f"Text saved to {args.output}")
                else:
                    # Print first 500 characters as preview
                    print("\nText preview:")
                    print(cleaned_text[:500])
                    print("...")
            else:
                print("Failed to extract text from PDF")

    elif os.path.isdir(args.pdf_path):
        # Directory processing
        pdf_files = list(Path(args.pdf_path).glob("*.pdf"))
        print(f"Found {len(pdf_files)} PDF files")

        if args.check:
            for pdf_file in pdf_files:
                info = processor.check_pdf_readability(str(pdf_file))
                status = "✓" if info['is_text_based'] else "✗"
                print(f"{status} {pdf_file.name}: {info.get('text_length', 0)} chars")
        else:
            results = processor.process_batch([str(f) for f in pdf_files])
            successful = sum(1 for text in results.values() if text)
            print(f"Successfully processed {successful}/{len(pdf_files)} files")


if __name__ == "__main__":
    main()