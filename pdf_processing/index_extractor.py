#!/usr/bin/env python3
"""
Index Extractor for PDF Documents
Extracts and parses table of contents/index structures from PDF documents
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class IndexEntry:
    """Represents a single entry in the document index"""
    title: str
    page: Optional[int]
    level: int
    parent_id: Optional[str] = None
    entry_id: Optional[str] = None
    children: Optional[List['IndexEntry']] = None

    def __post_init__(self):
        if self.children is None:
            self.children = []
        if self.entry_id is None:
            self.entry_id = self._generate_id()

    def _generate_id(self) -> str:
        """Generate a unique ID for this entry"""
        clean_title = re.sub(r'[^\w\s-]', '', self.title.lower())
        clean_title = re.sub(r'\s+', '_', clean_title.strip())
        return f"idx_{clean_title}_{self.level}"

class IndexExtractor:
    """Extract and parse document index/table of contents"""

    def __init__(self):
        # Patterns for detecting table of contents sections
        self.toc_patterns = [
            r'(?i)\b(contents?|table\s+of\s+contents?)\b',
            r'(?i)^\s*(contents?|table\s+of\s+contents?)\s*$',
            r'(?i)##?\s*(contents?|table\s+of\s+contents?)\s*$'
        ]

        # Patterns for chapter/section entries
        self.chapter_patterns = [
            r'(?i)chapter\s+(\d+):\s*(.+?)\.+\s*(\d+)',
            r'(?i)(\d+)\.\s*(.+?)\.+\s*(\d+)',
            r'(?i)([IVXLCDM]+)\.\s*(.+?)\.+\s*(\d+)',  # Roman numerals
        ]

        # Patterns for subsection entries (indented lines with page numbers)
        self.section_patterns = [
            r'^[\s\|]*(.+?)\.{3,}\s*(\d+)\s*$',  # Dotted lines to page numbers
            r'^[\s\|]*(.+?)\s{3,}(\d+)\s*$',     # Multiple spaces to page numbers
            r'^[\s\|]*-\s*(.+?)\.+\s*(\d+)\s*$', # Dash prefix
            r'^[\s\|]*•\s*(.+?)\.+\s*(\d+)\s*$', # Bullet prefix
        ]

    def extract_index_structure(self, content: str, extracted_data: Dict) -> Dict[str, Any]:
        """Extract index structure from document content"""
        logger.info("Extracting index structure from document")

        try:
            # First, try to find TOC in the content
            toc_content = self._find_toc_content(content)

            if not toc_content:
                logger.warning("No clear table of contents found, attempting structure inference")
                return self._infer_structure_from_content(extracted_data)

            # Parse the found TOC content
            index_entries = self._parse_toc_content(toc_content)

            # Build hierarchical structure
            hierarchical_index = self._build_hierarchical_index(index_entries)

            return {
                'index_entries': [entry.__dict__ for entry in index_entries],
                'hierarchical_structure': hierarchical_index,
                'extraction_method': 'toc_parsing',
                'total_entries': len(index_entries),
                'max_level': max([entry.level for entry in index_entries]) if index_entries else 0,
                'has_page_numbers': any(entry.page for entry in index_entries)
            }

        except Exception as e:
            logger.error(f"Error extracting index structure: {e}")
            return self._fallback_structure_extraction(extracted_data)

    def _find_toc_content(self, content: str) -> Optional[str]:
        """Find and extract table of contents section from content"""
        lines = content.split('\n')
        toc_start = None
        toc_end = None

        # Find TOC start
        for i, line in enumerate(lines):
            for pattern in self.toc_patterns:
                if re.search(pattern, line.strip()):
                    toc_start = i
                    logger.info(f"Found TOC start at line {i}: {line.strip()}")
                    break
            if toc_start is not None:
                break

        if toc_start is None:
            return None

        # Find TOC end (next major section or end of meaningful content)
        end_patterns = [
            r'(?i)^\s*(chapter|section|introduction|overview)\s+\d+',
            r'(?i)^\s*#\s+(chapter|section|introduction)',
            r'^\s*$',  # Empty line followed by significant content
        ]

        # Look for end of TOC (usually before first chapter)
        for i in range(toc_start + 1, min(toc_start + 100, len(lines))):
            line = lines[i].strip()

            # Skip empty lines and table formatting
            if not line or line.startswith('|') or line.startswith('-'):
                continue

            # Check if this looks like the start of main content
            for pattern in end_patterns:
                if re.search(pattern, line):
                    toc_end = i
                    break

            if toc_end:
                break

        if toc_end is None:
            toc_end = min(toc_start + 50, len(lines))  # Fallback limit

        toc_content = '\n'.join(lines[toc_start:toc_end])
        logger.info(f"Extracted TOC content: {len(toc_content)} characters")
        return toc_content

    def _parse_toc_content(self, toc_content: str) -> List[IndexEntry]:
        """Parse table of contents content into structured entries"""
        entries = []
        lines = toc_content.split('\n')

        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line or line.startswith('|') or line.startswith('-') or len(line) < 3:
                continue

            # Try chapter patterns first
            for pattern in self.chapter_patterns:
                match = re.search(pattern, line)
                if match:
                    if len(match.groups()) == 3:
                        chapter_num, title, page = match.groups()
                        entries.append(IndexEntry(
                            title=title.strip(),
                            page=int(page) if page.isdigit() else None,
                            level=1
                        ))
                    break
            else:
                # Try section patterns
                for pattern in self.section_patterns:
                    match = re.search(pattern, line)
                    if match and len(match.groups()) >= 2:
                        title, page = match.groups()[:2]

                        # Determine level based on indentation
                        indent_level = len(line) - len(line.lstrip())
                        level = min(2 + (indent_level // 4), 6)  # Map indentation to levels 2-6

                        entries.append(IndexEntry(
                            title=title.strip(),
                            page=int(page) if page.isdigit() else None,
                            level=level
                        ))
                        break

        logger.info(f"Parsed {len(entries)} index entries")
        return entries

    def _build_hierarchical_index(self, entries: List[IndexEntry]) -> Dict[str, Any]:
        """Build hierarchical structure from flat list of entries"""
        if not entries:
            return {}

        # Sort entries by page number if available, otherwise by order
        entries.sort(key=lambda x: (x.page or 0, entries.index(x)))

        # Build hierarchy
        root_entries = []
        parent_stack = []

        for entry in entries:
            # Find appropriate parent
            while parent_stack and parent_stack[-1].level >= entry.level:
                parent_stack.pop()

            if parent_stack:
                parent = parent_stack[-1]
                parent.children.append(entry)
                entry.parent_id = parent.entry_id
            else:
                root_entries.append(entry)

            parent_stack.append(entry)

        return {
            'root_entries': [entry.__dict__ for entry in root_entries],
            'total_levels': max([entry.level for entry in entries]) if entries else 0,
            'structure_type': 'hierarchical'
        }

    def _infer_structure_from_content(self, extracted_data: Dict) -> Dict[str, Any]:
        """Infer structure when no clear TOC is found"""
        logger.info("Inferring structure from extracted data")

        if 'enhanced_structure' in extracted_data:
            structure = extracted_data['enhanced_structure']
            entries = []

            # Convert chapters to index entries
            for chapter in structure.get('chapters', []):
                entries.append(IndexEntry(
                    title=chapter.get('title', ''),
                    page=chapter.get('page', None),
                    level=1
                ))

                # Add sections
                for section in chapter.get('sections', []):
                    entries.append(IndexEntry(
                        title=section.get('title', ''),
                        page=section.get('page', None),
                        level=2
                    ))

            return {
                'index_entries': [entry.__dict__ for entry in entries],
                'hierarchical_structure': self._build_hierarchical_index(entries),
                'extraction_method': 'structure_inference',
                'total_entries': len(entries),
                'max_level': max([entry.level for entry in entries]) if entries else 0,
                'has_page_numbers': any(entry.page for entry in entries)
            }

        return self._empty_index_structure()

    def _fallback_structure_extraction(self, extracted_data: Dict) -> Dict[str, Any]:
        """Fallback when all other methods fail"""
        logger.warning("Using fallback structure extraction")

        # Try to extract basic structure from font analysis
        if 'font_analysis' in extracted_data:
            font_data = extracted_data['font_analysis']
            entries = []

            # Use heading map if available
            for title, info in font_data.get('heading_map', {}).items():
                if info.get('is_heading', False):
                    level = min(info.get('level', 6), 6)
                    entries.append(IndexEntry(
                        title=title,
                        page=info.get('page', None),
                        level=level
                    ))

            if entries:
                return {
                    'index_entries': [entry.__dict__ for entry in entries],
                    'hierarchical_structure': self._build_hierarchical_index(entries),
                    'extraction_method': 'font_fallback',
                    'total_entries': len(entries),
                    'max_level': max([entry.level for entry in entries]),
                    'has_page_numbers': any(entry.page for entry in entries)
                }

        return self._empty_index_structure()

    def _empty_index_structure(self) -> Dict[str, Any]:
        """Return empty structure when extraction fails"""
        return {
            'index_entries': [],
            'hierarchical_structure': {},
            'extraction_method': 'none',
            'total_entries': 0,
            'max_level': 0,
            'has_page_numbers': False
        }

    def validate_index_completeness(self, index_structure: Dict, font_structure: Dict) -> Dict[str, Any]:
        """Validate index completeness against font-based structure"""
        logger.info("Validating index completeness")

        index_titles = {entry['title'].lower().strip() for entry in index_structure.get('index_entries', [])}

        font_headings = set()
        if 'heading_map' in font_structure:
            font_headings = {title.lower().strip() for title in font_structure['heading_map'].keys()}

        # Find gaps
        missing_from_index = font_headings - index_titles
        missing_from_font = index_titles - font_headings

        overlap_ratio = len(index_titles & font_headings) / max(len(font_headings), 1)

        return {
            'index_coverage_ratio': overlap_ratio,
            'missing_from_index': list(missing_from_index),
            'missing_from_font': list(missing_from_font),
            'total_index_entries': len(index_titles),
            'total_font_headings': len(font_headings),
            'validation_score': overlap_ratio * 100
        }