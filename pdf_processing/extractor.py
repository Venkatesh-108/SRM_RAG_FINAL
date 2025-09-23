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
    import pdfplumber  # License-compliant alternative to PyMuPDF
except ImportError as e:
    print(f"Missing required library: {e}")
    print("Install with: pip install docling pdfplumber")
    raise

logger = logging.getLogger(__name__)

class PDFExtractor:
    """Extract PDF content with font-based heading detection"""
    
    def __init__(self, heading_size_threshold: float = 1.2):
        self.heading_size_threshold = heading_size_threshold
        
        # Set up models folder path
        self._setup_models_path()
        
        # Initialize converter
        self.converter = DocumentConverter()
    
    def _setup_models_path(self):
        """Set up the models folder path for offline use"""
        import os
        from pathlib import Path
        
        # Look for models folder in current directory or parent directories
        models_dir = Path("./models")
        if not models_dir.exists():
            # Try alternative locations
            alternative_paths = [
                Path("../models"),
                Path("../../models"),
                Path("/opt/models"),
                Path("/opt/SRM_AI_DOC/models")
            ]
            
            for alt_path in alternative_paths:
                if alt_path.exists():
                    models_dir = alt_path
                    break
        
        if models_dir.exists():
            # Set environment variables to use local models
            os.environ['HF_HOME'] = str(models_dir.absolute())
            os.environ['HUGGINGFACE_HUB_CACHE'] = str(models_dir.absolute())
            os.environ['HF_DATASETS_OFFLINE'] = '1'
            os.environ['TRANSFORMERS_OFFLINE'] = '1'
            logger.info(f"Using models from: {models_dir.absolute()}")
        else:
            logger.warning("Models folder not found. Will try to download models from internet.")
    
    def extract_document(self, pdf_path: str) -> Dict[str, Any]:
        """Extract document with hybrid method (Docling + PyMuPDF)"""
        logger.info(f"Starting extraction: {pdf_path}")
        
        # Step 1: Get complete content using Docling
        docling_result = self.converter.convert(pdf_path)
        document = docling_result.document
        
        # Get complete markdown with ALL content preserved
        complete_markdown = document.export_to_markdown()

        # Post-process markdown to fix table formatting issues
        complete_markdown = self._fix_table_formatting(complete_markdown)
        
        # Get structured content as dictionary
        complete_json = {
            'main_text': complete_markdown,
            'pages': getattr(document, 'pages', []),
            'metadata': getattr(document, 'metadata', {}),
            'structure': str(document)[:500] + "..." if len(str(document)) > 500 else str(document)
        }
        
        logger.info(f"Docling extracted {len(complete_markdown)} characters of content")
        
        # Step 2: Get font analysis using PyMuPDF
        font_analysis = self._analyze_fonts_with_pdfplumber(pdf_path)
        
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
    
    def _analyze_fonts_with_pdfplumber(self, pdf_path: str) -> Dict[str, Any]:
        """Use pdfplumber to analyze font patterns for heading detection (license-compliant)"""

        # Collect font information from all pages
        font_data = []

        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # Get character-level information
                chars = page.chars

                # Group characters by line (similar Y coordinates)
                lines = {}
                for char in chars:
                    y_coord = round(char['y0'], 1)  # Group by similar Y coordinates
                    if y_coord not in lines:
                        lines[y_coord] = []
                    lines[y_coord].append(char)

                # Process each line
                for y_coord, line_chars in lines.items():
                    if not line_chars:
                        continue

                    # Sort by X coordinate to get proper text order
                    line_chars.sort(key=lambda c: c['x0'])

                    # Extract line text and font information
                    line_text = ''.join(char['text'] for char in line_chars).strip()

                    if line_text and len(line_text) > 1:
                        # Get dominant font characteristics for this line
                        sizes = [char['size'] for char in line_chars if char.get('size', 0) > 0]
                        fonts = [char.get('fontname', '') for char in line_chars if char.get('fontname')]

                        if sizes:
                            avg_size = statistics.mean(sizes)
                            dominant_font = Counter(fonts).most_common(1)[0][0] if fonts else ""

                            # Detect bold text (common indicators in font names)
                            is_bold = any(bold_indicator in dominant_font.lower()
                                        for bold_indicator in ['bold', 'black', 'heavy', 'semibold'])

                            # Get bounding box
                            x0 = min(char['x0'] for char in line_chars)
                            y0 = min(char['y0'] for char in line_chars)
                            x1 = max(char['x1'] for char in line_chars)
                            y1 = max(char['y1'] for char in line_chars)

                            font_data.append({
                                'text': line_text,
                                'page': page_num,
                                'font': dominant_font,
                                'size': avg_size,
                                'is_bold': is_bold,
                                'bbox': [x0, y0, x1, y1]
                            })

        # Analyze font patterns
        all_sizes = [item['size'] for item in font_data if item['size'] > 0]
        all_fonts = [item['font'] for item in font_data if item['font']]

        if not all_sizes:
            # Fallback if no font data extracted
            logger.warning("No font data extracted, using default values")
            return {
                'body_size': 12,
                'heading_sizes': [16, 14],
                'heading_map': {},
                'font_counter': {},
                'extraction_method': 'pdfplumber_fallback'
            }

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
            'troubleshooting', 'if this fails', 'alternative',
            # Non-content pseudo-headings often extracted as headings
            'contents', 'table of contents', 'topics', 'sections in this chapter',
            'list of tables', 'list of figures'
        ]
        
        # Check if the clean text matches any procedural sub-heading
        for subheading in procedural_subheadings:
            if clean_text == subheading or clean_text.startswith(subheading + ' '):
                return True
        
        # Check for very short headings that are likely procedural sub-sections
        # But preserve legitimate content subsections
        if len(clean_text.split()) <= 3 and len(clean_text) <= 25:
            # Don't filter out legitimate content-oriented subsection headings
            content_subsection_keywords = [
                'adjusting', 'adding', 'datastores', 'configuring', 'installing',
                'deploying', 'scaling', 'modifying', 'creating', 'setting',
                'updating', 'managing', 'monitoring', 'troubleshooting',
                'backup', 'restore', 'migration', 'upgrade', 'downgrade',
                'security', 'performance', 'optimization', 'maintenance',
                'network', 'storage', 'database', 'server', 'client',
                'authentication', 'authorization', 'encryption', 'certificates',
                'logging', 'reporting', 'dashboard', 'interface', 'api',
                'integration', 'customization', 'templates', 'policies',
                'virtual', 'physical', 'cloud', 'hybrid', 'cluster',
                'containers', 'vms', 'hosts', 'endpoints', 'devices'
            ]

            # If it contains content-related keywords, keep it as a heading
            for keyword in content_subsection_keywords:
                if keyword in clean_text:
                    return False  # Don't filter out - keep as heading

            # Otherwise, filter out generic short headings
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

        # Filter out bullet point headings that are likely TOC entries or list items
        if text.strip().startswith('- '):
            # Check if it's a TOC entry (short with page numbers) or a list item
            if len(text.strip()) < 80 or re.search(r'\d+\s*$', text.strip()):
                return False
            # Also filter out bullet points that are clearly list items (not headings)
            if (re.search(r'^-\s+(ensure|identify|download|browse|select|click)', text.strip(), re.IGNORECASE) or
                re.search(r'^-\s+.*(?:as described|refer to|see|note|warning)', text.strip(), re.IGNORECASE)):
                return False

        # Filter out very short fragments that are likely artifacts
        if len(text.strip()) < 3:
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
            # Only accept bold text as heading if it's reasonably sized
            if size < body_size * 0.8:  # Too small to be a heading
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
        seen_titles = set()  # Track seen titles to avoid duplicates

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
                cleaned_title = self._clean_heading_text(line_strip)
                normalized_title = self._normalize_title_for_dedup(cleaned_title)

                # Skip duplicate titles (handle cases like "- Title" vs "Title")
                if normalized_title in seen_titles:
                    content_buffer.append(line)  # Treat as regular content
                    continue

                # Save previous section
                if current_section:
                    current_section['complete_content'] = '\n'.join(content_buffer)
                    current_section['content_length'] = len(current_section['complete_content'])
                    sections.append(current_section)

                # Start new section
                current_section = {
                    'title': cleaned_title,
                    'heading_level': heading_info['level'],
                    'font_size': heading_info.get('size', 0),
                    'is_bold': heading_info.get('is_bold', False),
                    'page': heading_info.get('page', 1),
                    'confidence': heading_info.get('confidence', 0.5),
                    'is_heading': True,
                    'raw_line': line_strip
                }
                seen_titles.add(normalized_title)
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

        # Post-process to remove duplicate sections
        sections = self._deduplicate_sections(sections)

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

    def _normalize_title_for_dedup(self, title: str) -> str:
        """Normalize title for deduplication (remove bullet points, extra spaces, etc.)"""
        normalized = title.lower().strip()
        # Remove leading bullets, dashes, numbers
        normalized = re.sub(r'^[-•\d\.\s]+', '', normalized)
        # Normalize whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized

    def _deduplicate_sections(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate sections and merge content where appropriate"""
        seen_titles = {}
        deduplicated = []

        for section in sections:
            title = section['title']
            normalized_title = self._normalize_title_for_dedup(title)

            if normalized_title in seen_titles:
                # Found duplicate - merge content with higher confidence section
                existing_idx = seen_titles[normalized_title]
                existing_section = deduplicated[existing_idx]

                # Keep the section with higher confidence and better content
                if (section['confidence'] > existing_section['confidence'] or
                    len(section.get('complete_content', '')) > len(existing_section.get('complete_content', ''))):
                    # Replace existing with current
                    deduplicated[existing_idx] = section
            else:
                # New unique section
                seen_titles[normalized_title] = len(deduplicated)
                deduplicated.append(section)

        return deduplicated
    
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

        # First pass: filter out duplicate sections (keep ones with content)
        filtered_sections = self._filter_duplicate_sections(sections)

        for section in filtered_sections:
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

    def _filter_duplicate_sections(self, sections: List[Dict]) -> List[Dict]:
        """Filter out duplicate sections, keeping the ones with actual content"""
        title_to_best_section = {}

        for section in sections:
            title = section['title']
            normalized_title = self._normalize_title_for_dedup(title)

            if normalized_title not in title_to_best_section:
                title_to_best_section[normalized_title] = section
            else:
                existing = title_to_best_section[normalized_title]
                # Prefer section with more content, higher confidence, or better font size
                current_content_len = len(section.get('complete_content', ''))
                existing_content_len = len(existing.get('complete_content', ''))

                should_replace = (
                    current_content_len > existing_content_len or
                    (current_content_len == existing_content_len and
                     section.get('confidence', 0) > existing.get('confidence', 0)) or
                    (current_content_len == existing_content_len and
                     section.get('font_size', 0) > existing.get('font_size', 0))
                )

                if should_replace:
                    title_to_best_section[normalized_title] = section

        # Return filtered sections in original order
        filtered = []
        seen_normalized = set()
        for section in sections:
            normalized_title = self._normalize_title_for_dedup(section['title'])
            if (normalized_title not in seen_normalized and
                title_to_best_section[normalized_title] == section):
                filtered.append(section)
                seen_normalized.add(normalized_title)

        logger.info(f"Filtered {len(sections)} sections down to {len(filtered)} unique sections")
        return filtered

    def _fix_table_formatting(self, markdown_content: str) -> str:
        """Fix table formatting issues in extracted markdown content using adaptive detection"""
        import re

        lines = markdown_content.split('\n')
        fixed_lines = []

        # First pass: analyze table patterns to understand the document structure
        table_patterns = self._analyze_table_patterns(lines)

        for line in lines:
            # Check if this is a problematic table line using adaptive detection
            if '|' in line and self._is_adaptive_problematic_line(line, table_patterns):
                # Split the line using learned patterns
                fixed_table_lines = self._adaptive_split_table_line(line, table_patterns)
                fixed_lines.extend(fixed_table_lines)
            else:
                fixed_lines.append(line)

        return '\n'.join(fixed_lines)

    def _analyze_table_patterns(self, lines: List[str]) -> Dict[str, Any]:
        """Analyze table patterns in the document to learn structure dynamically"""
        import re
        from collections import Counter

        patterns = {
            'separators': Counter(),  # What separates entries (dots, spaces, etc.)
            'number_patterns': Counter(),  # How numbers appear (page numbers, etc.)
            'title_patterns': Counter(),  # How titles are formatted
            'table_structures': Counter(),  # Overall table structure
            'overflow_indicators': []  # Specific overflow patterns found
        }

        table_lines = [line for line in lines if '|' in line and line.strip().startswith('|')]

        for line in table_lines:
            content = line.strip('|').strip()

            # Analyze separator patterns
            if '.' in content:
                dot_sequences = re.findall(r'\.{2,}', content)
                for seq in dot_sequences:
                    patterns['separators'][len(seq)] += 1

            # Analyze number patterns
            numbers = re.findall(r'\b\d+\b', content)
            for num in numbers:
                # Check context around numbers
                num_context = self._get_number_context(content, num)
                patterns['number_patterns'][num_context] += 1

            # Detect potential overflow (multiple distinct content blocks)
            potential_titles = re.findall(r'[A-Z][a-z]+(?:\s+[a-z]+)*', content)
            if len(potential_titles) > 1:
                # Check if they're separated by numbers or patterns
                title_positions = []
                for title in potential_titles:
                    match = re.search(re.escape(title), content)
                    if match:
                        title_positions.append((match.start(), title))

                if len(title_positions) > 1:
                    patterns['overflow_indicators'].append({
                        'line': content,
                        'titles': title_positions,
                        'separators': re.findall(r'\.{3,}\d+', content)
                    })

        return patterns

    def _get_number_context(self, content: str, number: str) -> str:
        """Get context around a number to understand its role"""
        import re

        # Find the number in content
        pattern = r'(.{0,10})\b' + re.escape(number) + r'\b(.{0,10})'
        match = re.search(pattern, content)

        if not match:
            return 'isolated'

        before, after = match.groups()

        # Classify based on context
        if before.endswith('...') or '.' in before[-3:]:
            return 'after_dots'
        elif after.startswith(' ') and re.match(r'\s+[A-Z]', after):
            return 'before_title'
        elif before.strip() == '' and after.strip() == '':
            return 'standalone'
        else:
            return 'embedded'

    def _is_adaptive_problematic_line(self, line: str, patterns: Dict[str, Any]) -> bool:
        """Adaptively detect problematic lines based on learned patterns"""
        import re

        content = line.strip('|').strip()

        # Use learned patterns to detect overflow
        overflow_indicators = patterns.get('overflow_indicators', [])

        # Check if this line matches known overflow patterns
        for indicator in overflow_indicators:
            # Check for similar structure
            if len(re.findall(r'\.{3,}\d+', content)) > 1:
                return True

            # Check for multiple titles with numbers
            titles = re.findall(r'[A-Z][a-z]+(?:\s+[a-z]+)*', content)
            numbers = re.findall(r'\b\d+\b', content)

            if len(titles) > 1 and len(numbers) > 1:
                return True

        # Fallback to heuristic detection
        return (
            len(re.findall(r'\.{3,}\d+\s+[A-Z]', content)) > 0 or  # Pattern: ...num Title
            len(re.findall(r'\d+\s+[A-Z][a-z]+.*\d+', content)) > 0  # Pattern: num Title...num
        )

    def _adaptive_split_table_line(self, line: str, patterns: Dict[str, Any]) -> List[str]:
        """Split table line using adaptive patterns learned from document"""
        import re

        content = line.strip('|').strip()

        # Use most common separator pattern
        separators = patterns.get('separators', {})
        if separators:
            most_common_dots = max(separators.keys()) if separators else 3
        else:
            most_common_dots = 3

        # Adaptive splitting based on learned patterns
        # Look for the pattern: content + dots + number + space + next_content
        split_pattern = rf'(.*?\.{{{most_common_dots},}}\d+)\s+([A-Z].*?)(?=\.{{{most_common_dots},}}\d+|$)'

        matches = list(re.finditer(split_pattern, content))

        if matches:
            fixed_lines = []

            for match in matches:
                first_entry = match.group(1).strip()
                if first_entry:
                    fixed_lines.append(f"| {first_entry} |")

                second_entry = match.group(2).strip()
                if second_entry:
                    # Look for page number at end or add adaptive dots
                    if not re.search(r'\.{3,}\d+\s*$', second_entry):
                        # Extract any trailing numbers
                        trailing_num_match = re.search(r'(\d+)\s*$', content[match.end():])
                        if trailing_num_match:
                            page_num = trailing_num_match.group(1)
                            dots = '.' * most_common_dots
                            second_entry = re.sub(r'\s*\d+\s*$', '', second_entry)
                            second_entry = f"{second_entry}{dots}{page_num}"

                    fixed_lines.append(f"| {second_entry} |")

            return fixed_lines if fixed_lines else [line]

        return [line]

    def _is_problematic_table_line(self, line: str) -> bool:
        """Check if a table line has overflow issues"""
        import re

        # Look for table of contents patterns with overflow
        patterns = [
            r'\|\s*.*\.{3,}\d+\s+[A-Z][a-z].*\d+\s*\|',  # Table row with multiple page numbers
            r'\|\s*.*\d+\s+[A-Z][a-z].*\d+\s*\|',  # Multiple entries in one table cell
        ]

        for pattern in patterns:
            if re.search(pattern, line):
                return True
        return False

    def _split_table_overflow_line(self, line: str) -> List[str]:
        """Split a table line with overflow into multiple proper table rows"""
        import re

        # Remove the outer table formatting
        content = line.strip('|').strip()

        # Look for the specific overflow pattern where content after page number should be on new line
        # Pattern: "Title...pagenum SpaceNextTitle"
        overflow_pattern = r'(.*?\.{3,}\d+)\s+([A-Z][a-zA-Z\s]+.*?)(?=\.{3,}\d+|$)'

        matches = list(re.finditer(overflow_pattern, content))

        if not matches:
            return [line]  # No overflow detected, return original

        fixed_lines = []

        for match in matches:
            first_entry = match.group(1).strip()
            if first_entry:
                fixed_lines.append(f"| {first_entry} |")

            second_entry = match.group(2).strip()
            if second_entry:
                # Check if second entry has page number at end
                if re.search(r'\.{3,}\d+\s*$', second_entry):
                    fixed_lines.append(f"| {second_entry} |")
                else:
                    # Look for page number pattern at the end of the line
                    remaining_content = content[match.end():]
                    page_match = re.search(r'\.{3,}(\d+)', remaining_content)
                    if page_match:
                        page_num = page_match.group(1)
                        # Add dots to make it look like a proper TOC entry
                        dots_needed = max(3, 50 - len(second_entry))
                        dots = '.' * dots_needed
                        fixed_lines.append(f"| {second_entry}{dots}{page_num} |")
                    else:
                        fixed_lines.append(f"| {second_entry} |")

        # If no matches but line looks problematic, try simple split
        if not fixed_lines and self._is_problematic_table_line(line):
            # Split on page numbers followed by capital letters
            parts = re.split(r'(\d+)\s+([A-Z][a-zA-Z\s]+)', content)
            if len(parts) > 1:
                # Reconstruct entries
                for i in range(0, len(parts)-2, 3):
                    if i < len(parts):
                        entry_part = parts[i]
                        if i+1 < len(parts):
                            entry_part += parts[i+1]  # Add the page number
                        if entry_part.strip():
                            fixed_lines.append(f"| {entry_part.strip()} |")

                    # Handle the title part
                    if i+2 < len(parts):
                        title_part = parts[i+2]
                        if title_part.strip():
                            # Add some dots for TOC formatting
                            dots = '.' * 50
                            # Look for page number in remaining parts
                            page_num = ""
                            if i+3 < len(parts):
                                page_match = re.search(r'\d+', parts[i+3])
                                if page_match:
                                    page_num = page_match.group(0)

                            if page_num:
                                fixed_lines.append(f"| {title_part.strip()}{dots}{page_num} |")
                            else:
                                fixed_lines.append(f"| {title_part.strip()}{dots}15 |")

        return fixed_lines if fixed_lines else [line]
