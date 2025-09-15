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

logger = logging.getLogger(__name__)

class EnhancedPDFProcessor:
    """Enhanced processor with hybrid font-index chunking"""

    def __init__(self, output_dir: str = "extracted_docs", index_dir: str = "indexes",
                 model_name: str = 'all-MiniLM-L6-v2', max_chunk_size: int = 8000,
                 enable_hybrid_chunking: bool = True):
        self.output_dir = Path(output_dir)
        self.index_dir = Path(index_dir)
        self.model_name = model_name
        self.max_chunk_size = max_chunk_size
        self.enable_hybrid_chunking = enable_hybrid_chunking

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
        """Process a single PDF document with hybrid font-index chunking"""
        logger.info(f"Processing document with hybrid chunking: {pdf_path} -> {document_id}")

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

        # Apply hybrid chunking if enabled
        if self.enable_hybrid_chunking:
            final_chunks, hybrid_metadata = self._apply_hybrid_chunking(
                font_chunks, extracted_data, self._full_markdown_content
            )
        else:
            final_chunks = font_chunks
            hybrid_metadata = {'hybrid_chunking_enabled': False}

        # Create vector index
        vector_data = self._create_vector_index(final_chunks)

        # Save all data including hybrid results
        self._save_enhanced_data(doc_dir, document_id, extracted_data, final_chunks, hybrid_metadata)

        # Save vector indexes
        self._save_vector_indexes(document_id, vector_data)

        return {
            'document_id': document_id,
            'total_chapters': len(extracted_data['enhanced_structure']['chapters']),
            'total_sections': extracted_data['enhanced_structure']['total_sections'],
            'total_chunks': len(final_chunks),
            'chunk_types': self._analyze_chunk_types(final_chunks),
            'content_length': extracted_data['content_length'],
            'vector_dimension': vector_data['embedding_model'],
            'extraction_method': 'hybrid_font_index' if self.enable_hybrid_chunking else 'enhanced_page_aware',
            'hybrid_metadata': hybrid_metadata,
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
        """Check if section appears to be a table of contents entry"""
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
        """Extract complete section content from full markdown text"""
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
        
        # Find the end of the section (next heading of same or higher level)
        start_level = len(re.match(r'^#+', lines[section_start]).group(0))
        
        # Define common boundary keywords that indicate a new, distinct section
        boundary_keywords = [
            'overview', 'introduction', 'installing', 'configuring', 
            'prerequisites', 'requirements', 'troubleshooting', 'appendix'
        ]

        for i in range(section_start + 1, len(lines)):
            line_strip = lines[i].strip()
            if line_strip.startswith('#'):
                current_level = len(re.match(r'^#+', line_strip).group(0))
                
                # Check for boundary keywords in the new heading
                heading_text = re.sub(r'^#+\s*', '', line_strip).lower()
                is_boundary = any(keyword in heading_text for keyword in boundary_keywords)

                if current_level <= start_level or is_boundary:
                    section_end = i
                    break
            
            # Also stop at common document boundaries
            if any(boundary in line_strip.lower() for boundary in [
                'documentation feedback',
                'appendix',
                'chapter',
                'references'
            ]) and line_strip.startswith('#'):
                section_end = i
                break
        
        # Extract and clean the section content
        section_lines = lines[section_start + 1:section_end]  # Skip the heading itself
        section_content = '\n'.join(section_lines).strip()
        
        return section_content

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

            # Fix procedure list formatting
            if re.match(r'^\d+\.\s', line_strip):
                # This is a numbered list item
                cleaned_lines.append(line)

                # Look ahead for NOTE and file paths that belong to this step
                j = i + 1
                additional_content = []

                # Look for NOTE that should be part of this step
                if j < len(lines):
                    next_line = lines[j].strip()
                    next_num_match = re.match(r'^(\d+)\.\s+(NOTE:.*)', next_line)
                    if next_num_match and int(next_num_match.group(1)) == int(line_strip.split('.')[0]) + 1:
                        # This is a NOTE that was incorrectly numbered as the next step
                        note_content = next_num_match.group(2)
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

        return cleaned_content.strip()

    def _create_enhanced_chapter_chunk(self, chapter: Dict) -> Dict:
        """Create enhanced chapter chunk with complete metadata"""
        content = f"# {chapter['title']}\n\n{chapter.get('complete_content', '')}"
        
        # Add section overview
        if chapter.get('sections'):
            content += "\n\n## Sections in this chapter:\n"
            for section in chapter['sections']:
                content += f"- {section['title']}\n"
        
        # Determine chunk classification
        font_size = chapter.get('font_size', 20.0)
        chunk_classification = self._classify_by_font_size(font_size)
        
        return {
            'content': content,
            'title': chapter['title'],
            'chunk_type': 'chapter_major',
            'chunk_classification': chunk_classification,
            'hierarchy_level': 'chapter',
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
    
    def _classify_by_font_size(self, font_size: float) -> str:
        """Classify chunk type based on font size"""
        for chunk_type, properties in self.font_hierarchy.items():
            size_min, size_max = properties['size_range']
            if size_min <= font_size <= size_max:
                return chunk_type
        return 'body_text'
    
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
                           chunks: List[Dict], hybrid_metadata: Optional[Dict] = None):
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
            'hybrid_metadata': hybrid_metadata
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