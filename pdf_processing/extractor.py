#!/usr/bin/env python3
"""
PDF Extractor Module
Handles PDF extraction using hybrid Docling + PyMuPDF approach
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import re
from collections import Counter
import statistics

# Import libraries
try:
    from docling.document_converter import DocumentConverter
    import fitz  # PyMuPDF
except ImportError as e:
    print(f"Missing required library: {e}")
    print("Install with: pip install docling PyMuPDF")
    raise

logger = logging.getLogger(__name__)

class PDFExtractor:
    """Extract PDF content with font-based heading detection"""
    
    def __init__(self, heading_size_threshold: float = 1.2):
        self.converter = DocumentConverter()
        self.heading_size_threshold = heading_size_threshold
    
    def extract_document(self, pdf_path: str) -> Dict[str, Any]:
        """Extract document with hybrid method (Docling + PyMuPDF)"""
        logger.info(f"Starting extraction: {pdf_path}")
        
        # Step 1: Get complete content using Docling
        docling_result = self.converter.convert(pdf_path)
        document = docling_result.document
        
        # Get complete markdown with ALL content preserved
        complete_markdown = document.export_to_markdown()
        
        # Get structured content as dictionary
        complete_json = {
            'main_text': complete_markdown,
            'pages': getattr(document, 'pages', []),
            'metadata': getattr(document, 'metadata', {}),
            'structure': str(document)[:500] + "..." if len(str(document)) > 500 else str(document)
        }
        
        logger.info(f"Docling extracted {len(complete_markdown)} characters of content")
        
        # Step 2: Get font analysis using PyMuPDF
        font_analysis = self._analyze_fonts_with_pymupdf(pdf_path)
        
        # Step 3: Parse content and map to font analysis
        enhanced_structure = self._enhance_content_with_font_analysis(
            complete_markdown, complete_json, font_analysis
        )
        
        return {
            'full_text': complete_markdown,
            'structured_json': complete_json,
            'font_analysis': font_analysis,
            'enhanced_structure': enhanced_structure,
            'extraction_method': 'hybrid_docling_font',
            'content_length': len(complete_markdown)
        }
    
    def _analyze_fonts_with_pymupdf(self, pdf_path: str) -> Dict[str, Any]:
        """Use PyMuPDF to analyze font patterns for heading detection"""
        
        doc = fitz.open(pdf_path)
        
        # Collect font information from all pages
        font_data = []
        
        for page_num, page in enumerate(doc, 1):
            text_dict = page.get_text("dict")
            
            for block in text_dict.get("blocks", []):
                if "lines" not in block:
                    continue
                    
                for line in block.get("lines", []):
                    line_text = ""
                    line_fonts = []
                    
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if text:
                            line_text += text + " "
                            line_fonts.append({
                                'font': span.get("font", ""),
                                'size': span.get("size", 0),
                                'flags': span.get("flags", 0),
                                'color': span.get("color", 0)
                            })
                    
                    if line_text.strip() and line_fonts:
                        # Get dominant font for this line
                        avg_size = statistics.mean([f['size'] for f in line_fonts if f['size'] > 0])
                        dominant_font = Counter([f['font'] for f in line_fonts if f['font']]).most_common(1)[0][0] if line_fonts else ""
                        is_bold = sum(1 for f in line_fonts if f['flags'] & 16) > len(line_fonts) * 0.5
                        
                        font_data.append({
                            'text': line_text.strip(),
                            'page': page_num,
                            'font': dominant_font,
                            'size': avg_size,
                            'is_bold': is_bold,
                            'bbox': line.get("bbox", [0, 0, 0, 0])
                        })
        
        doc.close()
        
        # Analyze font patterns
        all_sizes = [item['size'] for item in font_data if item['size'] > 0]
        all_fonts = [item['font'] for item in font_data if item['font']]
        
        size_counter = Counter(all_sizes)
        font_counter = Counter(all_fonts)
        
        # Identify body text characteristics
        body_size = size_counter.most_common(1)[0][0] if all_sizes else 12
        body_font = font_counter.most_common(1)[0][0] if all_fonts else ""
        
        # Identify heading sizes
        heading_threshold = body_size * self.heading_size_threshold
        heading_sizes = sorted([size for size in set(all_sizes) if size >= heading_threshold], reverse=True)
        
        # Create heading classification mapping
        heading_map = {}
        for item in font_data:
            text = item['text']
            # Filter out TOC-like lines and procedure steps that are often bold/large
            if self._is_heading_text(text, item['size'], item['is_bold'], body_size):
                heading_level = heading_sizes.index(item['size']) + 1 if item['size'] in heading_sizes else len(heading_sizes) + 1
                heading_map[text] = {
                    'is_heading': True,
                    'level': heading_level,
                    'size': item['size'],
                    'is_bold': item['is_bold'],
                    'page': item['page'],
                    'confidence': 0.9 if item['size'] in heading_sizes else 0.7
                }
        
        logger.info(f"Font analysis: body_size={body_size}, heading_sizes={heading_sizes}, headings_found={len(heading_map)}")
        
        return {
            'body_size': body_size,
            'body_font': body_font,
            'heading_sizes': heading_sizes,
            'heading_map': heading_map,
            'font_distribution': dict(font_counter.most_common()),
            'size_distribution': dict(size_counter.most_common()),
            'total_text_elements': len(font_data)
        }
    
    def _looks_like_toc_line(self, text: str) -> bool:
        """Heuristic: detect table-of-contents lines with leaders and page numbers."""
        if not text:
            return False
        t = text.strip()
        # Common TOC artifacts: pipe separators, long dot leaders, trailing page numbers
        if '|' in t:
            return True
        if re.search(r"\.{5,}", t):
            return True
        if re.search(r"\s\d{1,4}\s*$", t) and len(t) > 25:
            return True
        # Very long single-line titles are typically TOC entries
        if len(t) > 140:
            return True
        return False

    def _looks_like_procedure_step(self, text: str) -> bool:
        """Detect numbered procedure steps such as '1. Click ...' which are not headings."""
        if not text:
            return False
        t = text.strip()
        # Stricter check for procedure steps (e.g., "1. Action...")
        if re.match(r"^\d+\.\s+[A-Z]", t):
            # If it contains verbs commonly used in steps, treat as non-heading
            verbs = [
                'click', 'select', 'open', 'browse', 'enter', 'type', 'press',
                'review', 'accept', 'next', 'previous', 'install', 'download',
                'run', 'restart', 'verify'
            ]
            tl = t.lower()
            if any(v in tl for v in verbs) and len(t.split()) > 3:
                return True
        return False

    def _is_procedural_subheading(self, text: str) -> bool:
        """Detect procedural sub-headings that should remain part of the main content."""
        if not text:
            return False
        
        text_lower = text.strip().lower()
        
        # Remove markdown formatting for checking
        clean_text = text_lower.replace('#', '').strip()
        
        # Common procedural sub-headings that should not split content
        procedural_subheadings = [
            'steps', 'procedure', 'instructions', 'process', 'method',
            'prerequisites', 'requirements', 'before you begin',
            'next steps', 'what to do next', 'continue with',
            'follow these steps', 'to do this', 'implementation',
            'example', 'examples', 'note', 'notes', 'important',
            'warning', 'caution', 'tip', 'tips', 'result', 'results',
            'outcome', 'expected result', 'verification', 'verify',
            'troubleshooting', 'if this fails', 'alternative'
        ]
        
        # Check if the clean text matches any procedural sub-heading
        for subheading in procedural_subheadings:
            if clean_text == subheading or clean_text.startswith(subheading + ' '):
                return True
        
        # Also check for very short headings that are likely sub-sections
        if len(clean_text.split()) <= 2 and len(clean_text) <= 15:
            return True
            
        return False

    def _is_heading_text(self, text: str, size: float, is_bold: bool, body_size: float) -> bool:
        """Final gate to decide whether a line should be treated as a heading.
        Filters out TOC-like lines and numbered procedure steps even if bold/large.
        """
        # More aggressive filtering for TOC lines
        if self._looks_like_toc_line(text):
            return False
        if self._looks_like_procedure_step(text):
            return False
            
        # Filter out common sub-headings that should be part of the main content
        # These are typically procedural sub-sections that shouldn't split content
        if self._is_procedural_subheading(text):
            return False
            
        is_large = size >= body_size * self.heading_size_threshold
        
        # Heading if large enough OR if it's bold and doesn't look like a sentence fragment.
        if is_large:
            return True

        if is_bold:
            # Less strict check for bold text.
            # Avoid classifying paragraphs that start with a bold word as headings.
            if len(text.split()) > 10 and text.strip().endswith('.'):
                 return False
            # Avoid notes or references
            if any(word in text.lower() for word in ['note:', 'see also', 'refer to']):
                return False
            return True
            
        return False

    def _enhance_content_with_font_analysis(self, markdown_content: str, json_content: Dict, 
                                          font_analysis: Dict) -> Dict[str, Any]:
        """Enhance content with font-based heading detection"""
        
        heading_map = font_analysis['heading_map']
        
        # Parse markdown into sections while preserving complete content
        sections = self._parse_markdown_sections(markdown_content, heading_map, font_analysis)
        
        # Build hierarchical structure
        chapters = self._build_hierarchical_structure(sections)
        
        return {
            'chapters': chapters,
            'total_chapters': len(chapters),
            'total_sections': sum(len(ch.get('sections', [])) for ch in chapters),
            'extraction_method': 'hybrid_enhanced'
        }
    
    def _parse_markdown_sections(self, markdown: str, heading_map: Dict, font_analysis: Dict) -> List[Dict[str, Any]]:
        """Parse markdown into sections with font-based heading classification"""
        
        lines = markdown.split('\n')
        sections = []
        current_section = None
        content_buffer = []
        
        for line in lines:
            line_strip = line.strip()
            if not line_strip:
                content_buffer.append("")
                continue
            
            # Check if this line is a heading based on font analysis
            is_heading = False
            heading_info = None
            
            # Look for exact match in heading map
            clean_line = self._clean_text_for_matching(line_strip)
            for heading_text, info in heading_map.items():
                clean_heading = self._clean_text_for_matching(heading_text)
                # Use a more robust matching logic
                if (clean_line == clean_heading or 
                    (clean_line in clean_heading and len(clean_line) > 10) or 
                    (clean_heading in clean_line and len(clean_heading) > 10)):
                    if self._is_heading_text(line_strip, info['size'], info['is_bold'], font_analysis['body_size']):
                        is_heading = True
                        heading_info = info
                        break
            
            # Also check markdown heading patterns (with stricter guards)
            if (not is_heading 
                and (line_strip.startswith('#'))
                and not self._looks_like_toc_line(line_strip)
                and not self._looks_like_procedure_step(line_strip)
                and not self._is_procedural_subheading(line_strip)):
                is_heading = True
                # Try to find font info for markdown headings
                md_heading_info = heading_map.get(clean_line, {
                    'is_heading': True,
                    'level': line_strip.count('#'),
                    'size': 0, 'is_bold': False, 'page': 1, 'confidence': 0.6
                })
                heading_info = md_heading_info
            
            if is_heading and heading_info:
                # Save previous section
                if current_section:
                    current_section['complete_content'] = '\n'.join(content_buffer)
                    current_section['content_length'] = len(current_section['complete_content'])
                    sections.append(current_section)
                
                # Start new section
                current_section = {
                    'title': self._clean_heading_text(line_strip),
                    'heading_level': heading_info['level'],
                    'font_size': heading_info.get('size', 0),
                    'is_bold': heading_info.get('is_bold', False),
                    'page': heading_info.get('page', 1),
                    'confidence': heading_info.get('confidence', 0.5),
                    'is_heading': True,
                    'raw_line': line_strip
                }
                content_buffer = []  # Exclude heading from content
                
            else:
                # Regular content - add to buffer
                content_buffer.append(line)
        
        # Save final section
        if current_section:
            current_section['complete_content'] = '\n'.join(content_buffer)
            current_section['content_length'] = len(current_section['complete_content'])
            sections.append(current_section)
        elif content_buffer:  # Handle content without headings
            sections.append({
                'title': 'Document Content',
                'heading_level': 999,
                'font_size': 0,
                'is_bold': False,
                'page': 1,
                'confidence': 0.3,
                'is_heading': False,
                'complete_content': '\n'.join(content_buffer),
                'content_length': len('\n'.join(content_buffer))
            })
        
        logger.info(f"Parsed {len(sections)} sections from markdown content")
        return sections
    
    def _clean_text_for_matching(self, text: str) -> str:
        """Clean text for heading matching"""
        cleaned = re.sub(r'#+\s*', '', text)  # Remove markdown headers
        cleaned = re.sub(r'\*+', '', cleaned)  # Remove bold/italic
        cleaned = re.sub(r'\s+', ' ', cleaned)  # Normalize spaces
        return cleaned.strip().lower()
    
    def _clean_heading_text(self, text: str) -> str:
        """Clean heading text for display"""
        cleaned = re.sub(r'^#+\s*', '', text)
        cleaned = re.sub(r'\*+', '', cleaned)
        return cleaned.strip()
    
    def _is_likely_heading(self, line: str) -> bool:
        """Check if line is likely a heading based on content patterns"""
        patterns = [
            r'^[A-Z][A-Z\s]{5,50}$',  # ALL CAPS
            # Exclude typical procedure steps like '1. Click ...' by requiring no verbs
            # Keep numbered section headers such as '1 Introduction'
            r'^\d+\s+[A-Z][a-z]+$',
            r'^Chapter\s+\d+',         # Chapter N
            r'Prerequisites|Steps|Configuration|Installation|Overview|Introduction'
        ]
        
        for pattern in patterns:
            if re.match(pattern, line.strip(), re.IGNORECASE):
                return True
        
        return False
    
    def _build_hierarchical_structure(self, sections: List[Dict]) -> List[Dict]:
        """Build hierarchical chapter/section structure"""
        
        chapters = []
        current_chapter = None
        
        for section in sections:
            level = section['heading_level']
            
            # Group by H1/H2 as chapters, everything else as sections
            if level <= 2:  # Chapter level
                if current_chapter:
                    chapters.append(current_chapter)
                
                current_chapter = {
                    'id': f"chapter_{len(chapters)+1:02d}",
                    'title': section['title'],
                    'complete_content': section['complete_content'],
                    'font_size': section['font_size'],
                    'is_bold': section['is_bold'],
                    'page': section['page'],
                    'heading_level': section['heading_level'],
                    'confidence': section['confidence'],
                    'type': 'chapter',
                    'sections': [],
                    'content_length': section['content_length']
                }
            
            else:  # Section level or content
                if not current_chapter:
                    # Create implicit chapter for content that appears before the first main chapter
                    current_chapter = {
                        'id': f"chapter_{len(chapters)+1:02d}",
                        'title': 'Document Introduction',
                        'complete_content': '',
                        'font_size': 0, 'is_bold': False, 'page': 1, 'heading_level': 1,
                        'confidence': 0.3, 'type': 'chapter', 'sections': [], 'content_length': 0
                    }
                
                # If it's a heading, create a new section
                if section['is_heading']:
                    section_data = {
                        'id': f"section_{len(current_chapter['sections'])+1:03d}",
                        'title': section['title'],
                        'complete_content': section['complete_content'],
                        'font_size': section['font_size'],
                        'is_bold': section['is_bold'],
                        'page': section['page'],
                        'heading_level': section['heading_level'],
                        'confidence': section['confidence'],
                        'type': 'section',
                        'content_length': section['content_length']
                    }
                    current_chapter['sections'].append(section_data)
                else:
                    # If it's content without a heading, append it to the last section or the chapter itself
                    if current_chapter['sections']:
                        current_chapter['sections'][-1]['complete_content'] += '\n\n' + section['title'] + '\n' + section['complete_content']
                        current_chapter['sections'][-1]['content_length'] += len(section['complete_content']) + len(section['title']) + 3
                    else:
                        current_chapter['complete_content'] += '\n\n' + section['title'] + '\n' + section['complete_content']
                        current_chapter['content_length'] += len(section['complete_content']) + len(section['title']) + 3
        
        # Add final chapter
        if current_chapter:
            chapters.append(current_chapter)
        
        return chapters
