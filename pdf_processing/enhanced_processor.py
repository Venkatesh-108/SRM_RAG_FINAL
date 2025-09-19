#!/usr/bin/env python3
"""
Enhanced PDF Processor with Page-Aware Chunking
Implements multi-level chunking based on font hierarchy and page breaks
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import re

# Import required libraries
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    import numpy as np
except ImportError as e:
    print(f"Missing required library: {e}")
    print("Install with: pip install sentence-transformers faiss-cpu numpy")
    raise

from .extractor import PDFExtractor
from .index_extractor import IndexExtractor
from .chunk_validator import ChunkValidator
from .chunking_config import DocumentTypeConfigs, validate_chunking_quality

logger = logging.getLogger(__name__)

class EnhancedPDFProcessor:
    """Enhanced processor with hybrid font-index chunking"""

    def __init__(self, output_dir: str = "extracted_docs", index_dir: str = "indexes",
                 model_name: str = 'all-MiniLM-L6-v2', max_chunk_size: int = 8000,
                 enable_hybrid_chunking: bool = True, document_type: str = "auto"):
        self.output_dir = Path(output_dir)
        self.index_dir = Path(index_dir)
        self.model_name = model_name
        self.max_chunk_size = max_chunk_size
        self.enable_hybrid_chunking = enable_hybrid_chunking
        self.document_type = document_type

        # Create directories
        self.output_dir.mkdir(exist_ok=True)
        self.index_dir.mkdir(exist_ok=True)

        # Initialize components
        self.extractor = PDFExtractor()
        self.model = SentenceTransformer(model_name)

        # Initialize hybrid chunking components
        if self.enable_hybrid_chunking:
            self.index_extractor = IndexExtractor()
            self.chunk_validator = ChunkValidator()

        # Chunking configuration will be set per document
        self.chunking_config = None
        
        # Font hierarchy mapping (based on analysis)
        self.font_hierarchy = {
            'document_title': {'size_range': (22, 28), 'level': 1},
            'chapter_major': {'size_range': (20, 21.9), 'level': 2},
            'section_standard': {'size_range': (16, 19.9), 'level': 3},
            'subsection_minor': {'size_range': (11.5, 15.9), 'level': 4},
            'table_figure': {'size_range': (10, 11.4), 'level': 5},
            'body_text': {'size_range': (8, 9.9), 'level': 6}
        }
    
    def process_document(self, pdf_path: str, document_id: str) -> Dict[str, Any]:
        """Process a single PDF document with adaptive chunking based on document type"""
        logger.info(f"Processing document with hybrid chunking: {pdf_path} -> {document_id}")

        # Detect document type and set configuration
        detected_type = self.document_type
        if detected_type == "auto":
            detected_type = DocumentTypeConfigs.detect_document_type(pdf_path)

        self.chunking_config = DocumentTypeConfigs.get_config(detected_type)
        logger.info(f"Using chunking configuration for document type: {detected_type}")

        # Create document directory
        doc_dir = self.output_dir / document_id
        doc_dir.mkdir(exist_ok=True)

        # Extract with hybrid method
        extracted_data = self.extractor.extract_document(pdf_path)

        # Store full markdown content for section extraction
        self._full_markdown_content = extracted_data.get('full_text', '')

        logger.info(f"Extracted content length: {extracted_data['content_length']} characters")
        logger.info(f"Found {len(extracted_data['enhanced_structure']['chapters'])} chapters")

        # Create base font-based chunks
        font_chunks = self._create_enhanced_chunks(extracted_data['enhanced_structure'], extracted_data['font_analysis'])

        # CRITICAL FIX: Validate and fix structural problems before chunking
        font_chunks = self._validate_and_fix_structure(font_chunks, extracted_data['enhanced_structure'])

        # Apply hybrid chunking if enabled
        if self.enable_hybrid_chunking:
            final_chunks, hybrid_metadata = self._apply_hybrid_chunking(
                font_chunks, extracted_data, self._full_markdown_content
            )
        else:
            final_chunks = font_chunks
            hybrid_metadata = {'hybrid_chunking_enabled': False}

        # Validate chunking quality
        quality_report = validate_chunking_quality(final_chunks, self.chunking_config)
        logger.info(f"Chunking quality: {quality_report['status']} ({quality_report['over_inclusion_ratio']:.1%} over-inclusion)")

        # Create vector index
        vector_data = self._create_vector_index(final_chunks)

        # Save all data including hybrid results and quality report
        self._save_enhanced_data(doc_dir, document_id, extracted_data, final_chunks, hybrid_metadata, quality_report)

        # Save vector indexes
        self._save_vector_indexes(document_id, vector_data)

        return {
            'document_id': document_id,
            'document_type': detected_type,
            'total_chapters': len(extracted_data['enhanced_structure']['chapters']),
            'total_sections': extracted_data['enhanced_structure']['total_sections'],
            'total_chunks': len(final_chunks),
            'chunk_types': self._analyze_chunk_types(final_chunks),
            'content_length': extracted_data['content_length'],
            'vector_dimension': vector_data['embedding_model'],
            'extraction_method': 'hybrid_font_index' if self.enable_hybrid_chunking else 'enhanced_page_aware',
            'hybrid_metadata': hybrid_metadata,
            'quality_report': quality_report,
            'processing_time': datetime.now().isoformat()
        }
    
    def _create_enhanced_chunks(self, structure: Dict, font_analysis: Dict) -> List[Dict]:
        """Create enhanced chunks with multi-level hierarchy and page awareness"""
        chunks = []
        seen_titles = set()  # Track processed titles to avoid duplicates

        for chapter in structure['chapters']:
            # Determine chunk strategy based on size and content
            chapter_size = len(chapter.get('complete_content', ''))

            if chapter_size > self.max_chunk_size:
                # Split large chapters into sub-chunks
                sub_chunks = self._split_large_chapter(chapter, font_analysis)
                chunks.extend(sub_chunks)
            else:
                # Keep as single chapter chunk
                chapter_chunk = self._create_enhanced_chapter_chunk(chapter)
                chunks.append(chapter_chunk)

            # Process individual sections with enhanced metadata, avoiding duplicates
            for section in chapter.get('sections', []):
                section_title = section.get('title', '')
                normalized_title = self._normalize_section_title(section_title)

                # Skip if we've already processed this section or if it's empty/too short
                if (normalized_title in seen_titles or
                    len(section.get('complete_content', '').strip()) < 50 or
                    self._is_toc_like_section(section_title)):
                    continue

                section_chunk = self._create_enhanced_section_chunk(section, chapter, font_analysis)
                chunks.append(section_chunk)
                seen_titles.add(normalized_title)

        # Add document-level chunks for exact title matching
        doc_overview_chunk = self._create_document_overview_chunk(structure, font_analysis)
        chunks.insert(0, doc_overview_chunk)

        logger.info(f"Created {len(chunks)} enhanced chunks with page awareness")
        return chunks

    def _normalize_section_title(self, title: str) -> str:
        """Normalize section title for deduplication"""
        normalized = title.lower().strip()
        # Remove leading bullets, dashes, numbers
        normalized = re.sub(r'^[-•\d\.\s]+', '', normalized)
        # Normalize whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized

    def _is_toc_like_section(self, title: str) -> bool:
        """Check if section appears to be a table of contents entry or bullet point reference"""
        if not title:
            return True
        
        # TOC-like patterns
        toc_patterns = [
            r'^\s*[-•]\s*',  # Bullet points
            r'\.{3,}',       # Dot leaders
            r'\s+\d+\s*$',   # Ending with page numbers
        ]
        for pattern in toc_patterns:
            if re.search(pattern, title):
                return True
        
        # CRITICAL FIX: Detect bullet point references that mention other sections
        # These should not be treated as standalone sections
        bullet_reference_patterns = [
            r'^-\s+.*installing on.*',
            r'^-\s+.*complete the steps.*',
            r'^-\s+.*described in.*',
            r'^-\s+.*as described in.*',
            r'^-\s+.*refer to.*',
            r'^-\s+.*see.*',
        ]
        
        for pattern in bullet_reference_patterns:
            if re.search(pattern, title, re.IGNORECASE):
                return True
                
        return False

    def _split_large_chapter(self, chapter: Dict, font_analysis: Dict) -> List[Dict]:
        """Split large chapters into smaller chunks based on subsections"""
        chunks = []
        content = chapter.get('complete_content', '')
        
        # Try to split by subsections (16pt and smaller headings)
        subsection_pattern = r'^#{2,4}\s+(.+)$'
        lines = content.split('\n')
        current_subsection = []
        current_title = "Introduction"
        
        for line in lines:
            if re.match(subsection_pattern, line):
                # Save previous subsection if it exists
                if current_subsection:
                    chunk = self._create_subsection_chunk(
                        current_subsection, current_title, chapter, font_analysis
                    )
                    chunks.append(chunk)
                
                # Start new subsection
                current_title = re.match(subsection_pattern, line).group(1)
                current_subsection = [line]
            else:
                current_subsection.append(line)
        
        # Save final subsection
        if current_subsection:
            chunk = self._create_subsection_chunk(
                current_subsection, current_title, chapter, font_analysis
            )
            chunks.append(chunk)
        
        return chunks
    
    def _extract_complete_section_from_markdown(self, section_title: str, parent_chapter: Dict) -> str:
        """Extract complete section content from full markdown text with improved boundary detection"""
        if not hasattr(self, '_full_markdown_content'):
            return ""

        # Get the full markdown content
        full_content = getattr(self, '_full_markdown_content', '')
        if not full_content:
            return ""

        lines = full_content.split('\n')
        section_start = -1
        section_end = len(lines)

        # Find the start of our section
        for i, line in enumerate(lines):
            line_strip = line.strip()
            # Look for the section heading (could be ## or ###, etc.)
            if line_strip.startswith('#') and section_title.lower() in line_strip.lower():
                # More precise matching
                import re
                heading_match = re.match(r'^#+\s*(.+)', line_strip)
                if heading_match and heading_match.group(1).strip().lower() == section_title.lower():
                    section_start = i
                    break

        if section_start == -1:
            return ""

        # Find the end of the section with improved boundary detection
        section_end = self._find_section_end_boundary(lines, section_start, section_title)

        # Extract and clean the section content
        section_lines = lines[section_start + 1:section_end]  # Skip the heading itself
        section_content = '\n'.join(section_lines).strip()

        return section_content

    def _find_section_end_boundary(self, lines: List[str], section_start: int, section_title: str) -> int:
        """Find the precise end boundary of a section using multiple heuristics"""
        import re

        start_level = len(re.match(r'^#+', lines[section_start]).group(0))
        section_end = len(lines)

        # Use configurable section boundary patterns
        boundary_patterns = {
            'strong_boundaries': self.chunking_config.strong_boundary_patterns if self.chunking_config else [
                r'^#+\s+(?:Chapter|Appendix)\s+\d+',
                r'^#+\s+(?:Prerequisites|Before you begin|Next steps|What to do next)',
                r'^#+\s+(?:Results|Outcome|Summary)',
                r'^#+\s+(?:About this task|Steps|Procedure)',
                r'^#+\s+(?:Configuring|Installing|Creating|Adding|Removing)',
            ],
            'weak_boundaries': self.chunking_config.weak_boundary_patterns if self.chunking_config else [
                r'^#+\s+(?:Update|Configure|Install|Setup|Create|Delete|Add|Remove)',
                r'^#+\s+\w+\s+(?:Discovery|Configuration|Installation)',
            ],
            'transition_markers': self.chunking_config.transition_markers if self.chunking_config else [
                'About this task', 'Before you begin', 'Prerequisites',
                'What to do next', 'Next steps', 'Results', 'Troubleshooting'
            ]
        }

        content_lines_found = 0
        last_content_line = section_start
        table_content_found = False

        for i in range(section_start + 1, len(lines)):
            line = lines[i]
            line_strip = line.strip()

            # Track content to avoid stopping too early
            if line_strip and not line_strip.startswith('#'):
                content_lines_found += 1
                last_content_line = i
                
                # Check if this line contains table content
                if '|' in line_strip and ('Option' in line_strip or 'Description' in line_strip or 
                                         'Linux' in line_strip or 'Windows' in line_strip or
                                         'UNIX' in line_strip or 'Command' in line_strip):
                    table_content_found = True

            if line_strip.startswith('#'):
                current_level = len(re.match(r'^#+', line_strip).group(0))
                heading_text = re.sub(r'^#+\s*', '', line_strip)

                # Check for strong boundaries (always stop)
                for pattern in boundary_patterns['strong_boundaries']:
                    if re.match(pattern, line_strip, re.IGNORECASE):
                        return i

                # Check for same or higher level headings
                if current_level <= start_level:
                    # Additional check: don't stop too early if we haven't found much content
                    if content_lines_found >= 3 or i > section_start + 10:
                        return i

                # Check for weak boundaries at same level
                if current_level == start_level:
                    for pattern in boundary_patterns['weak_boundaries']:
                        if re.match(pattern, line_strip, re.IGNORECASE):
                            return i

            # Check for transition markers in content
            for marker in boundary_patterns['transition_markers']:
                if line_strip == marker or line_strip.startswith(f'## {marker}'):
                    # Only stop if we have reasonable content before this
                    if content_lines_found >= 5:
                        return i

            # CRITICAL FIX: Don't stop at "Steps" headings - they are subheadings within the same section
            # Steps headings should be included as part of the current section content
            # Only stop if Steps appears as a major section (same level as the starting section)
            if (line_strip.startswith('#') and 
                re.match(r'^#+\s+Steps\s*$', line_strip) and 
                current_level <= start_level and 
                content_lines_found >= 10):  # Only stop if we have substantial content
                return i

            # CRITICAL FIX: Stop at new major sections that should be separate chunks
            # Look for common section patterns that indicate a new topic
            major_section_patterns = [
                r'^#+\s+(?:Verifying|Troubleshooting|Logging|Connecting|Editing|Updating)',
                r'^#+\s+(?:Operating system|Command|Option|Description)',
                r'^#+\s+(?:Prerequisites|Steps|About this task)'
            ]
            
            for pattern in major_section_patterns:
                if re.match(pattern, line_strip, re.IGNORECASE):
                    # Only stop if we have substantial content and this looks like a new major section
                    if content_lines_found >= 10 or (table_content_found and content_lines_found >= 5):
                        return i

            # CRITICAL FIX: Detect and ignore bullet points that contain section references
            # These should not be treated as new sections
            if (line_strip.startswith('- ') and 
                ('installing on' in line_strip.lower() or 
                 'complete the steps' in line_strip.lower() or
                 'described in' in line_strip.lower())):
                # This is a bullet point reference, not a new section - continue
                continue

            # Avoid extremely long sections (safety net)
            max_lines = self.chunking_config.max_section_lines if self.chunking_config else 100
            if i > section_start + max_lines:
                return last_content_line + 1

        return section_end

    def _clean_section_content(self, content: str, section_title: str) -> str:
        """Clean section content to remove redundant title headers and fix list formatting"""
        if not content:
            return content

        import re
        lines = content.split('\n')
        cleaned_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]
            line_strip = line.strip()

            # Skip lines that are exact duplicates of the section title
            if line_strip.startswith('#') and section_title.lower() in line_strip.lower():
                # Check if this is an exact title match
                heading_match = re.match(r'^#+\s*(.+)', line_strip)
                if heading_match and heading_match.group(1).strip().lower() == section_title.lower():
                    i += 1
                    continue  # Skip this redundant title

            # Fix table overflow issues in TOC-like content
            if '|' in line and self._is_table_overflow_line(line):
                fixed_lines = self._fix_table_overflow(line)
                cleaned_lines.extend(fixed_lines)
                i += 1
                continue

            # CRITICAL FIX: Preserve table formatting better
            if '|' in line and self._is_structured_table_line(line):
                # This is a structured table line - preserve it exactly
                cleaned_lines.append(line)
                i += 1
                continue

            # Fix procedure list formatting
            if re.match(r'^\d+\.\s', line_strip):
                # This is a numbered list item
                cleaned_lines.append(line)

                # Look ahead for NOTE and file paths that belong to this step
                j = i + 1
                additional_content = []

                # Look for NOTE that should be part of this step (but not standalone numbered NOTEs)
                if j < len(lines):
                    next_line = lines[j].strip()
                    next_num_match = re.match(r'^(\d+)\.\s+(NOTE:.*)', next_line)
                    if next_num_match:
                        current_step_num = int(line_strip.split('.')[0])
                        note_step_num = int(next_num_match.group(1))
                        note_content = next_num_match.group(2)

                        # Only treat as sub-note if it's not a consecutive numbered step
                        # AND if the note content seems to belong to the current step
                        is_consecutive_step = (note_step_num == current_step_num + 1)
                        is_standalone_note = (
                            is_consecutive_step and
                            ('multiple' in note_content.lower() or
                             'can be' in note_content.lower() or
                             'recommends' in note_content.lower() or
                             len(note_content) > 50)  # Substantial standalone content
                        )

                        # Only attach as sub-note if it's clearly not a standalone numbered step
                        if not is_standalone_note and note_step_num == current_step_num + 1:
                            additional_content.append('')  # Empty line for spacing
                            additional_content.append(f'   **{note_content}**')  # Indent and format NOTE
                            j += 1

                # Look for file paths that should be bullet points
                file_path_lines = []
                while j < len(lines):
                    next_line = lines[j].strip()

                    # Check if this looks like a file path entry that was incorrectly numbered
                    if (re.match(r'^\d+\.\s+…/', next_line) or
                        (re.match(r'^\d+\.\s+', next_line) and 'conf/' in next_line) or
                        (re.match(r'^\d+\.\s+', next_line) and next_line.endswith('.xml'))):

                        # Convert numbered file path to bullet point
                        file_content = re.sub(r'^\d+\.\s+', '', next_line)
                        file_path_lines.append(f'   - {file_content}')  # Indent as sub-item
                        j += 1
                    else:
                        break

                # Add additional content and file paths
                if additional_content:
                    cleaned_lines.extend(additional_content)
                if file_path_lines:
                    if not additional_content:  # Add spacing if no NOTE was added
                        cleaned_lines.append('')
                    cleaned_lines.extend(file_path_lines)

                i = j
            else:
                cleaned_lines.append(line)
                i += 1

        # Join lines back and clean up any excessive whitespace
        cleaned_content = '\n'.join(cleaned_lines)

        # Remove multiple consecutive empty lines
        cleaned_content = re.sub(r'\n\n\n+', '\n\n', cleaned_content)

        # Fix NOTE formatting - ensure NOTE: is properly formatted
        cleaned_content = re.sub(r'^(\d+\.)\s+(NOTE:)', r'\1 **\2**', cleaned_content, flags=re.MULTILINE)

        # Fix numbering sequence: renumber steps after NOTEs are processed
        cleaned_content = self._fix_step_numbering(cleaned_content)

        return cleaned_content.strip()

    def _fix_step_numbering(self, content: str) -> str:
        """Fix numbering sequence by renumbering steps after NOTEs are processed"""
        import re

        lines = content.split('\n')
        fixed_lines = []
        step_counter = 1

        for line in lines:
            line_strip = line.strip()

            # Check if this is a numbered step (but not a NOTE)
            step_match = re.match(r'^(\d+)\.\s+(?!NOTE:)(.+)', line_strip)
            if step_match:
                # Renumber this step
                step_content = step_match.group(2)
                fixed_line = line.replace(line_strip, f"{step_counter}. {step_content}")
                fixed_lines.append(fixed_line)
                step_counter += 1
            else:
                # Keep line as is (including NOTEs, which should not be numbered)
                fixed_lines.append(line)

        return '\n'.join(fixed_lines)

    def _is_structured_table_line(self, line: str) -> bool:
        """Check if a line is part of a structured table (not TOC overflow)"""
        import re
        
        # Look for structured table patterns
        structured_patterns = [
            r'^\|.*\|.*\|',  # Multiple columns with pipes
            r'^\|.*Option.*\|',  # Option column
            r'^\|.*Description.*\|',  # Description column
            r'^\|.*Linux.*\|',  # Linux entries
            r'^\|.*Windows.*\|',  # Windows entries
            r'^\|.*UNIX.*\|',  # UNIX entries
            r'^\|.*Command.*\|',  # Command entries
            r'^\|.*Operating system.*\|',  # Operating system entries
        ]
        
        for pattern in structured_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return True
                
        return False

    def _is_table_overflow_line(self, line: str) -> bool:
        """Check if a line contains table overflow where multiple entries are concatenated"""
        import re
        # Look for patterns where page numbers are followed by titles without proper line breaks
        # Example: "...15 Modifying the start order..."
        patterns = [
            r'\.{3,}\d+\s+[A-Z][a-z]+',  # Dots followed by page number and title
            r'\d+\s+[A-Z][a-z]+.*\d+\s*\|',  # Page number, title, then another page number at end
        ]

        for pattern in patterns:
            if re.search(pattern, line):
                return True
        return False

    def _fix_table_overflow(self, line: str) -> List[str]:
        """Fix table overflow by splitting concatenated entries into separate lines"""
        import re

        # Pattern to find where entries are concatenated
        # Look for: "...pagenum Text" where Text starts with capital letter
        split_pattern = r'(\.{3,}\d+)\s+([A-Z][^|]*?)(?=\s*\d+\s*\||\s*$)'

        # Find all matches
        matches = list(re.finditer(split_pattern, line))

        if not matches:
            return [line]  # No overflow detected, return original

        # Split the line into proper table rows
        fixed_lines = []

        # Handle the beginning of the line (before first match)
        start_content = line[:matches[0].start()].strip()
        if start_content and start_content != '|':
            # Extract the main entry before overflow
            main_entry_match = re.search(r'^([^|]*?)(\.{3,}\d+)', start_content)
            if main_entry_match:
                entry_name = main_entry_match.group(1).strip()
                page_info = main_entry_match.group(2)
                fixed_lines.append(f"| {entry_name} {page_info} |")

        # Process each overflow entry
        for match in matches:
            page_dots = match.group(1)  # e.g., "...15"
            entry_title = match.group(2).strip()  # e.g., "Modifying the start order of the vApps"

            # Clean up the title to remove any trailing page numbers or pipes
            entry_title = re.sub(r'\s*\d+\s*\|?\s*$', '', entry_title)

            if entry_title:
                fixed_lines.append(f"| {entry_title} {page_dots} |")

        return fixed_lines

    def _create_enhanced_chapter_chunk(self, chapter: Dict) -> Dict:
        """Create enhanced chapter chunk with complete metadata"""
        content = f"# {chapter['title']}\n\n{chapter.get('complete_content', '')}"
        
        # Add section overview
        if chapter.get('sections'):
            content += "\n\n## Sections in this chapter:\n"
            for section in chapter['sections']:
                content += f"- {section['title']}\n"
        
        # Determine chunk classification and hierarchy level
        font_size = chapter.get('font_size', 20.0)
        chunk_classification = self._classify_by_font_size(font_size)

        # Intelligently determine if this should be treated as a chapter or section
        is_true_chapter = self._is_chapter_level_content(chapter['title'], font_size, chapter)
        chunk_type = 'complete_chapter' if is_true_chapter else 'complete_section'
        hierarchy_level = 'chapter' if is_true_chapter else 'section'

        return {
            'content': content,
            'title': chapter['title'],
            'chunk_type': chunk_type,
            'chunk_classification': chunk_classification,
            'hierarchy_level': hierarchy_level,
            'font_size': font_size,
            'is_bold': chapter.get('is_bold', False),
            'heading_level': chapter.get('heading_level', 1),
            'page_start': chapter.get('page', 1),
            'page_end': chapter.get('page', 1),
            'page_count': 1,
            'spans_multiple_pages': False,
            'confidence': chapter.get('confidence', 0.5),
            'word_count': len(content.split()),
            'content_length': len(content),
            'has_complete_content': True,
            'is_heading_chunk': True,
            'exact_title_match': chapter['title'].lower().strip(),
            'searchable_titles': [chapter['title']],
            'extraction_method': 'enhanced_page_aware'
        }
    
    def _create_enhanced_section_chunk(self, section: Dict, parent_chapter: Dict, font_analysis: Dict) -> Dict:
        """Create enhanced section chunk with page awareness"""
        # Start with metadata only - don't duplicate the section title
        content = f"*Chapter: {parent_chapter['title']}*\n"
        content += f"*Page: {section.get('page', 'N/A')}*\n\n"

        # Get complete section content - fallback to extracting from full markdown if needed
        section_content = section.get('complete_content', '')
        if not section_content or len(section_content.strip()) < 100:
            # Try to extract complete section from full markdown
            section_content = self._extract_complete_section_from_markdown(section['title'], parent_chapter)

        # Clean up section content to remove any redundant title headers
        section_content = self._clean_section_content(section_content, section['title'])

        content += section_content
        
        # Determine chunk classification
        font_size = section.get('font_size', 16.0)
        chunk_classification = self._classify_by_font_size(font_size)
        
        # Check if content contains procedures
        has_procedures = self._detect_procedures(content)
        
        return {
            'content': content,
            'title': section['title'],
            'chunk_type': 'section_standard',
            'chunk_classification': chunk_classification,
            'hierarchy_level': 'section',
            'chapter_title': parent_chapter['title'],
            'font_size': font_size,
            'is_bold': section.get('is_bold', False),
            'heading_level': section.get('heading_level', 2),
            'page_start': section.get('page', 1),
            'page_end': section.get('page', 1),
            'page_count': 1,
            'spans_multiple_pages': False,
            'confidence': section.get('confidence', 0.5),
            'word_count': len(content.split()),
            'content_length': len(content),
            'has_complete_content': True,
            'has_procedures': has_procedures,
            'is_heading_chunk': True,
            'exact_title_match': section['title'].lower().strip(),
            'searchable_titles': [section['title'], parent_chapter['title']],
            'extraction_method': 'enhanced_page_aware'
        }
    
    def _create_subsection_chunk(self, content_lines: List[str], title: str, chapter: Dict, font_analysis: Dict) -> Dict:
        """Create subsection chunk from split content"""
        content = '\n'.join(content_lines)
        
        return {
            'content': content,
            'title': title,
            'chunk_type': 'subsection_minor',
            'chunk_classification': 'subsection_minor',
            'hierarchy_level': 'subsection',
            'chapter_title': chapter['title'],
            'font_size': 14.0,  # Estimated for subsections
            'is_bold': True,
            'heading_level': 3,
            'page_start': chapter.get('page', 1),
            'page_end': chapter.get('page', 1),
            'page_count': 1,
            'spans_multiple_pages': False,
            'confidence': 0.8,
            'word_count': len(content.split()),
            'content_length': len(content),
            'has_complete_content': True,
            'has_procedures': self._detect_procedures(content),
            'is_heading_chunk': True,
            'exact_title_match': title.lower().strip(),
            'searchable_titles': [title, chapter['title']],
            'extraction_method': 'enhanced_page_aware'
        }
    
    def _create_document_overview_chunk(self, structure: Dict, font_analysis: Dict) -> Dict:
        """Create document overview chunk for exact title matching"""
        all_chapters = structure['chapters']
        
        # Create comprehensive overview
        content = "# Document Overview\n\n"
        content += "This document contains the following chapters:\n\n"
        
        for chapter in all_chapters:
            content += f"## {chapter['title']}\n"
            if chapter.get('sections'):
                for section in chapter['sections']:
                    content += f"- {section['title']}\n"
            content += "\n"
        
        return {
            'content': content,
            'title': 'Document Overview',
            'chunk_type': 'document_overview',
            'chunk_classification': 'document_title',
            'hierarchy_level': 'document',
            'font_size': 24.0,
            'is_bold': True,
            'heading_level': 0,
            'page_start': 1,
            'page_end': max([ch.get('page', 1) for ch in all_chapters]),
            'page_count': len(set([ch.get('page', 1) for ch in all_chapters])),
            'spans_multiple_pages': True,
            'confidence': 1.0,
            'word_count': len(content.split()),
            'content_length': len(content),
            'has_complete_content': True,
            'is_heading_chunk': True,
            'exact_title_match': 'document overview',
            'searchable_titles': ['Document Overview'] + [ch['title'] for ch in all_chapters],
            'extraction_method': 'enhanced_page_aware'
        }
    
    def _is_chapter_level_content(self, title: str, font_size: float, chapter_info: Dict) -> bool:
        """Intelligently determine if content should be treated as chapter or section level"""
        title_lower = title.lower().strip()

        # Strong indicators for chapter-level content
        chapter_indicators = [
            'chapter', 'getting started', 'installation', 'configuration',
            'troubleshooting', 'overview', 'introduction', 'preface',
            'appendix', 'solutionpack for', 'deployment', 'upgrade guide',
            'discovery center', 'device config wizard'
        ]

        # Strong indicators for section-level content
        section_indicators = [
            'add new', 'adding', 'configure', 'configuring', 'install', 'installing',
            'update', 'updating', 'create', 'creating', 'modify', 'modifying',
            'enable', 'enabling', 'disable', 'disabling', 'setup', 'setting up',
            'remove', 'removing', 'delete', 'deleting', 'export', 'importing',
            'running the', 'view', 'viewing', 'edit', 'editing', 'verify', 'verifying'
        ]

        # CRITICAL FIX: Check for suspicious chapter characteristics
        sections = chapter_info.get('sections', [])

        # If this "chapter" has too many sections, it's likely a misclassification
        if len(sections) > 20:
            logger.warning(f"Chapter '{title}' has {len(sections)} sections - likely misclassified")
            return False

        # If sections span too many pages, it's suspicious
        if sections:
            section_pages = [s.get('page', 0) for s in sections if s.get('page', 0) > 0]
            if section_pages and (max(section_pages) - min(section_pages) > 50):
                logger.warning(f"Chapter '{title}' spans {max(section_pages) - min(section_pages)} pages - likely misclassified")
                return False

        # Check for chapter-level indicators
        for indicator in chapter_indicators:
            if indicator in title_lower:
                return True

        # Check for section-level indicators
        for indicator in section_indicators:
            if indicator in title_lower:
                return False

        # Font size based decision for ambiguous cases
        # If font size is 0 (unknown), default to section to avoid over-classification
        if font_size <= 0:
            return False
        elif font_size >= 20:
            return True
        else:
            return False

    def _classify_by_font_size(self, font_size: float) -> str:
        """Classify chunk type based on font size with better edge case handling"""
        # Handle special cases where font size is 0 or unknown
        if font_size <= 0:
            # Default to section level for unknown font sizes to avoid chapter misclassification
            return 'section_standard'

        # Find the best match in font hierarchy
        for chunk_type, properties in self.font_hierarchy.items():
            size_min, size_max = properties['size_range']
            if size_min <= font_size <= size_max:
                return chunk_type

        # Fallback logic based on font size ranges
        if font_size >= 22:
            return 'document_title'
        elif font_size >= 20:
            return 'chapter_major'
        elif font_size >= 16:
            return 'section_standard'
        elif font_size >= 11.5:
            return 'subsection_minor'
        elif font_size >= 10:
            return 'table_figure'
        else:
            return 'body_text'

    def _validate_and_fix_structure(self, chunks: List[Dict], structure: Dict) -> List[Dict]:
        """Validate and fix structural problems in chunks"""
        logger.info("Validating and fixing structural problems...")

        fixed_chunks = []
        problematic_chapters = []

        for chunk in chunks:
            # Check for problematic chapters (like "Add new VMware vCenter")
            if (chunk.get('chunk_type') == 'complete_chapter' and
                chunk.get('hierarchy_level') == 'chapter'):

                # Count sections in the original structure
                chapter_title = chunk.get('title', '')
                original_chapter = None

                for ch in structure.get('chapters', []):
                    if ch.get('title', '') == chapter_title:
                        original_chapter = ch
                        break

                if original_chapter:
                    section_count = len(original_chapter.get('sections', []))

                    # Flag suspicious chapters
                    if section_count > 20:
                        logger.warning(f"Fixing problematic chapter: '{chapter_title}' with {section_count} sections")
                        problematic_chapters.append(chapter_title)

                        # Convert to section instead of chapter
                        chunk['chunk_type'] = 'complete_section'
                        chunk['hierarchy_level'] = 'section'

                        # Extract only the relevant content (first part)
                        content = chunk.get('content', '')
                        if content:
                            lines = content.split('\n')
                            # Keep only the first logical section (stop at next major heading)
                            clean_content = []
                            for line in lines:
                                if (line.startswith('## ') and
                                    'post-install' in line.lower() and
                                    len(clean_content) > 5):
                                    break
                                clean_content.append(line)

                            # Update chunk with cleaned content
                            chunk['content'] = '\n'.join(clean_content)
                            chunk['content_length'] = len(chunk['content'])
                            chunk['word_count'] = len(chunk['content'].split())

            fixed_chunks.append(chunk)

        if problematic_chapters:
            logger.info(f"Fixed {len(problematic_chapters)} problematic chapters: {problematic_chapters}")

        return fixed_chunks
    
    def _detect_procedures(self, content: str) -> bool:
        """Detect if content contains step-by-step procedures"""
        procedure_patterns = [
            r'^\d+\.\s+\w+',  # Numbered steps
            r'Step \d+',      # Step indicators
            r'Follow these steps',  # Procedure indicators
            r'To \w+.*:$',    # Action instructions
        ]
        
        for pattern in procedure_patterns:
            if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                return True
        return False
    
    def _analyze_chunk_types(self, chunks: List[Dict]) -> Dict[str, int]:
        """Analyze distribution of chunk types"""
        type_counts = {}
        for chunk in chunks:
            chunk_type = chunk.get('chunk_type', 'unknown')
            type_counts[chunk_type] = type_counts.get(chunk_type, 0) + 1
        return type_counts
    
    def _create_vector_index(self, chunks: List[Dict]) -> Dict[str, Any]:
        """Create vector index from enhanced chunks"""
        logger.info(f"Creating vector index for {len(chunks)} enhanced chunks")
        
        # Extract text content for embedding
        texts = [chunk['content'] for chunk in chunks]
        
        # Generate embeddings
        embeddings = self.model.encode(texts, show_progress_bar=True)
        
        # Normalize embeddings
        faiss.normalize_L2(embeddings)
        
        # Create FAISS index
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)  # Inner product for normalized vectors
        index.add(embeddings.astype('float32'))
        
        # Prepare enhanced metadata
        metadata = []
        for chunk in chunks:
            metadata.append({
                'title': chunk['title'],
                'chunk_type': chunk['chunk_type'],
                'chunk_classification': chunk.get('chunk_classification', 'unknown'),
                'hierarchy_level': chunk['hierarchy_level'],
                'font_size': chunk.get('font_size', 0),
                'is_bold': chunk.get('is_bold', False),
                'heading_level': chunk.get('heading_level', 0),
                'page_start': chunk.get('page_start', 1),
                'page_end': chunk.get('page_end', 1),
                'page_count': chunk.get('page_count', 1),
                'spans_multiple_pages': chunk.get('spans_multiple_pages', False),
                'confidence': chunk.get('confidence', 0.5),
                'has_procedures': chunk.get('has_procedures', False),
                'is_heading_chunk': chunk.get('is_heading_chunk', False),
                'exact_title_match': chunk.get('exact_title_match', ''),
                'extraction_method': chunk.get('extraction_method', 'enhanced_page_aware')
            })
        
        return {
            'index': index,
            'metadata': metadata,
            'chunks': [chunk['content'] for chunk in chunks],
            'enhanced_chunks': chunks,  # Include full chunk data
            'embedding_model': self.model_name,
            'dimension': dimension
        }

    def _apply_hybrid_chunking(self, font_chunks: List[Dict], extracted_data: Dict,
                              full_content: str) -> Tuple[List[Dict], Dict[str, Any]]:
        """Apply hybrid chunking by validating font chunks against index structure"""
        logger.info("Applying hybrid font-index chunking")

        try:
            # Extract index structure
            index_structure = self.index_extractor.extract_index_structure(
                full_content, extracted_data
            )

            # Validate font chunks against index
            validation_result = self.chunk_validator.validate_chunks(
                font_chunks, index_structure, extracted_data.get('font_analysis', {})
            )

            # Start with validated font chunks
            final_chunks = validation_result.validated_chunks

            # Create chunks for missing sections if they have recoverable content
            if validation_result.missing_sections:
                logger.info(f"Creating chunks for {len(validation_result.missing_sections)} missing sections")
                recovered_chunks = self.chunk_validator.create_missing_section_chunks(
                    validation_result.missing_sections, full_content
                )
                final_chunks.extend(recovered_chunks)

            # Prepare hybrid metadata
            hybrid_metadata = {
                'hybrid_chunking_enabled': True,
                'index_extraction': index_structure,
                'validation_results': {
                    'validation_score': validation_result.validation_score,
                    'missing_sections_count': len(validation_result.missing_sections),
                    'orphaned_chunks_count': len(validation_result.orphaned_chunks),
                    'recovered_chunks_count': len(recovered_chunks) if validation_result.missing_sections else 0,
                    'enriched_metadata': validation_result.enriched_metadata
                },
                'final_chunk_count': len(final_chunks),
                'original_chunk_count': len(font_chunks)
            }

            logger.info(f"Hybrid chunking complete. Score: {validation_result.validation_score:.2f}")
            logger.info(f"Final chunks: {len(final_chunks)} (was {len(font_chunks)})")

            return final_chunks, hybrid_metadata

        except Exception as e:
            logger.error(f"Hybrid chunking failed: {e}")
            return self._fallback_to_font_chunking(font_chunks)

    def _fallback_to_font_chunking(self, font_chunks: List[Dict]) -> Tuple[List[Dict], Dict[str, Any]]:
        """Fallback to original font-based chunking when hybrid fails"""
        logger.warning("Falling back to font-based chunking only")

        fallback_metadata = {
            'hybrid_chunking_enabled': True,
            'hybrid_chunking_failed': True,
            'fallback_reason': 'hybrid_processing_error',
            'final_chunk_count': len(font_chunks),
            'original_chunk_count': len(font_chunks)
        }

        return font_chunks, fallback_metadata

    def _save_enhanced_data(self, doc_dir: Path, document_id: str, extracted_data: Dict,
                           chunks: List[Dict], hybrid_metadata: Optional[Dict] = None,
                           quality_report: Optional[Dict] = None):
        """Save enhanced extracted data and chunks"""
        
        # Save complete markdown content
        with open(doc_dir / "complete_content.md", 'w', encoding='utf-8') as f:
            f.write(extracted_data['full_text'])
        
        # Save enhanced chunks with full metadata
        with open(doc_dir / "enhanced_chunks_v2.json", 'w', encoding='utf-8') as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)

        # Save hybrid chunks separately if using hybrid mode
        if hybrid_metadata and hybrid_metadata.get('hybrid_chunking_enabled'):
            with open(doc_dir / "enhanced_chunks_v3_hybrid.json", 'w', encoding='utf-8') as f:
                json.dump(chunks, f, indent=2, ensure_ascii=False)
        
        # Save font analysis
        with open(doc_dir / "font_analysis.json", 'w', encoding='utf-8') as f:
            json.dump(extracted_data['font_analysis'], f, indent=2, ensure_ascii=False)
        
        # Save enhanced structure
        with open(doc_dir / "enhanced_structure.json", 'w', encoding='utf-8') as f:
            json.dump(extracted_data['enhanced_structure'], f, indent=2, ensure_ascii=False)
        
        # Create chunk analysis summary
        chunk_analysis = {
            'total_chunks': len(chunks),
            'chunk_types': self._analyze_chunk_types(chunks),
            'size_distribution': {
                'small': len([c for c in chunks if c['content_length'] < 2000]),
                'medium': len([c for c in chunks if 2000 <= c['content_length'] < 8000]),
                'large': len([c for c in chunks if c['content_length'] >= 8000])
            },
            'page_distribution': {
                'single_page': len([c for c in chunks if not c.get('spans_multiple_pages', False)]),
                'multi_page': len([c for c in chunks if c.get('spans_multiple_pages', False)])
            },
            'procedure_chunks': len([c for c in chunks if c.get('has_procedures', False)]),
            'exact_title_matches': [c['exact_title_match'] for c in chunks if c.get('exact_title_match')]
        }
        
        with open(doc_dir / "chunk_analysis.json", 'w', encoding='utf-8') as f:
            json.dump(chunk_analysis, f, indent=2, ensure_ascii=False)
        
        # Save processing summary
        summary = {
            'document_id': document_id,
            'processing_date': datetime.now().isoformat(),
            'extraction_method': 'hybrid_font_index' if hybrid_metadata and hybrid_metadata.get('hybrid_chunking_enabled') else 'enhanced_page_aware',
            'total_content_length': extracted_data['content_length'],
            'total_chunks': len(chunks),
            'chunk_analysis': chunk_analysis,
            'font_hierarchy_used': self.font_hierarchy,
            'hybrid_metadata': hybrid_metadata,
            'quality_report': quality_report
        }

        with open(doc_dir / "processing_summary_v2.json", 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        # Save hybrid-specific summary if applicable
        if hybrid_metadata and hybrid_metadata.get('hybrid_chunking_enabled'):
            hybrid_summary = {
                **summary,
                'processing_version': 'v3_hybrid',
                'hybrid_details': hybrid_metadata
            }
            with open(doc_dir / "processing_summary_v3_hybrid.json", 'w', encoding='utf-8') as f:
                json.dump(hybrid_summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Enhanced data saved to {doc_dir}")
    
    def _save_vector_indexes(self, document_id: str, vector_data: Dict):
        """Save enhanced vector indexes"""
        
        # Save FAISS index
        index_path = self.index_dir / f"{document_id}_v2.faiss"
        faiss.write_index(vector_data['index'], str(index_path))
        
        # Save enhanced metadata
        metadata_path = self.index_dir / f"{document_id}_v2_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': vector_data['metadata'],
                'chunks': vector_data['chunks'],
                'enhanced_chunks': vector_data['enhanced_chunks'],
                'embedding_model': vector_data['embedding_model'],
                'processing_timestamp': datetime.now().isoformat(),
                'chunk_count': len(vector_data['chunks']),
                'enhancement_version': '2.0'
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Enhanced vector indexes saved to {self.index_dir}")