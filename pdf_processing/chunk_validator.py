#!/usr/bin/env python3
"""
Chunk Validator for Hybrid Chunking System
Cross-references font-based chunks with index structure and detects gaps
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from difflib import SequenceMatcher
import re

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Results of chunk validation"""
    validated_chunks: List[Dict]
    missing_sections: List[Dict]
    orphaned_chunks: List[Dict]
    enriched_metadata: Dict[str, Any]
    validation_score: float

@dataclass
class ChunkMatch:
    """Represents a match between font chunk and index entry"""
    chunk_id: str
    index_entry_id: str
    match_score: float
    match_type: str  # 'exact', 'partial', 'inferred'

class ChunkValidator:
    """Validates and enriches font-based chunks using index structure"""

    def __init__(self, similarity_threshold: float = 0.6):
        self.similarity_threshold = similarity_threshold
        self.match_patterns = {
            # Common title variations
            'chapter_variations': [
                r'chapter\s+(\d+):?\s*(.*)',
                r'(\d+)\.\s*(.*)',
                r'section\s+(\d+):?\s*(.*)'
            ],
            'cleanup_patterns': [
                r'\s*\.{3,}\s*\d+\s*$',  # Remove dotted leaders and page numbers
                r'\s*-{3,}\s*\d+\s*$',   # Remove dashed leaders and page numbers
                r'^\s*[-•]\s*',          # Remove bullet points
                r'\s+', ' '              # Normalize whitespace
            ]
        }

    def validate_chunks(self, font_chunks: List[Dict], index_structure: Dict,
                       font_analysis: Dict) -> ValidationResult:
        """Validate font chunks against index structure"""
        logger.info(f"Validating {len(font_chunks)} font chunks against index structure")

        try:
            # Clean and prepare data
            cleaned_chunks = self._prepare_chunks(font_chunks)
            index_entries = index_structure.get('index_entries', [])

            # Find matches between chunks and index entries
            matches = self._find_chunk_matches(cleaned_chunks, index_entries)

            # Detect gaps and missing sections
            missing_sections = self._detect_missing_sections(
                cleaned_chunks, index_entries, matches
            )

            # Identify orphaned chunks (no index match)
            orphaned_chunks = self._identify_orphaned_chunks(
                cleaned_chunks, matches
            )

            # Enrich chunk metadata
            enriched_chunks = self._enrich_chunk_metadata(
                cleaned_chunks, matches, index_entries
            )

            # Calculate validation score
            validation_score = self._calculate_validation_score(
                enriched_chunks, missing_sections, orphaned_chunks
            )

            # Generate enriched metadata
            enriched_metadata = self._generate_enriched_metadata(
                matches, missing_sections, orphaned_chunks, validation_score
            )

            result = ValidationResult(
                validated_chunks=enriched_chunks,
                missing_sections=missing_sections,
                orphaned_chunks=orphaned_chunks,
                enriched_metadata=enriched_metadata,
                validation_score=validation_score
            )

            logger.info(f"Validation complete. Score: {validation_score:.2f}")
            return result

        except Exception as e:
            logger.error(f"Error during chunk validation: {e}")
            return self._fallback_validation_result(font_chunks)

    def _prepare_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """Clean and prepare chunks for validation"""
        cleaned_chunks = []

        for chunk in chunks:
            # Create a copy to avoid modifying original
            cleaned_chunk = chunk.copy()

            # Clean title for comparison
            title = chunk.get('title', '')
            cleaned_title = self._clean_title(title)
            cleaned_chunk['cleaned_title'] = cleaned_title
            cleaned_chunk['original_title'] = title

            cleaned_chunks.append(cleaned_chunk)

        return cleaned_chunks

    def _clean_title(self, title: str) -> str:
        """Clean title for better matching"""
        cleaned = title.strip()

        # Apply cleanup patterns
        for pattern in self.match_patterns['cleanup_patterns']:
            cleaned = re.sub(pattern, ' ' if pattern == r'\s+' else '', cleaned)

        return cleaned.strip().lower()

    def _find_chunk_matches(self, chunks: List[Dict],
                           index_entries: List[Dict]) -> List[ChunkMatch]:
        """Find matches between chunks and index entries"""
        matches = []

        for chunk in chunks:
            chunk_title = chunk.get('cleaned_title', '')
            if not chunk_title:
                continue

            best_match = None
            best_score = 0

            for entry in index_entries:
                entry_title = self._clean_title(entry.get('title', ''))
                if not entry_title:
                    continue

                # Calculate similarity score
                score = self._calculate_title_similarity(chunk_title, entry_title)

                if score > best_score and score >= self.similarity_threshold:
                    best_score = score
                    best_match = entry

            if best_match:
                match_type = 'exact' if best_score > 0.9 else 'partial'
                matches.append(ChunkMatch(
                    chunk_id=chunk.get('title', ''),
                    index_entry_id=best_match.get('entry_id', ''),
                    match_score=best_score,
                    match_type=match_type
                ))

        logger.info(f"Found {len(matches)} chunk-to-index matches")
        return matches

    def _calculate_title_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two titles"""
        # Use sequence matcher for basic similarity
        similarity = SequenceMatcher(None, title1, title2).ratio()

        # Boost score for exact word matches
        words1 = set(title1.split())
        words2 = set(title2.split())

        if words1 and words2:
            word_overlap = len(words1 & words2) / max(len(words1), len(words2))
            # Combine similarity scores with word overlap weighted more heavily
            similarity = (similarity * 0.4) + (word_overlap * 0.6)

        return similarity

    def _detect_missing_sections(self, chunks: List[Dict], index_entries: List[Dict],
                                matches: List[ChunkMatch]) -> List[Dict]:
        """Detect sections that appear in index but not in chunks"""
        matched_entry_ids = {match.index_entry_id for match in matches}
        missing_sections = []

        for entry in index_entries:
            entry_id = entry.get('entry_id', '')
            if entry_id not in matched_entry_ids:
                # This is a missing section
                missing_sections.append({
                    'title': entry.get('title', ''),
                    'page': entry.get('page'),
                    'level': entry.get('level', 1),
                    'entry_id': entry_id,
                    'reason': 'missing_from_chunks'
                })

        logger.info(f"Detected {len(missing_sections)} missing sections")
        return missing_sections

    def _identify_orphaned_chunks(self, chunks: List[Dict],
                                 matches: List[ChunkMatch]) -> List[Dict]:
        """Identify chunks that don't match any index entry"""
        matched_chunk_ids = {match.chunk_id for match in matches}
        orphaned_chunks = []

        for chunk in chunks:
            chunk_id = chunk.get('title', '')
            if chunk_id not in matched_chunk_ids:
                orphaned_chunks.append({
                    'title': chunk.get('title', ''),
                    'chunk_type': chunk.get('chunk_type', ''),
                    'page_start': chunk.get('page_start'),
                    'word_count': chunk.get('word_count', 0),
                    'reason': 'no_index_match'
                })

        logger.info(f"Identified {len(orphaned_chunks)} orphaned chunks")
        return orphaned_chunks

    def _enrich_chunk_metadata(self, chunks: List[Dict], matches: List[ChunkMatch],
                              index_entries: List[Dict]) -> List[Dict]:
        """Enrich chunks with index-derived metadata"""
        # Create lookup for matches and index entries
        match_lookup = {match.chunk_id: match for match in matches}
        entry_lookup = {entry.get('entry_id', ''): entry for entry in index_entries}

        enriched_chunks = []

        for chunk in chunks:
            enriched_chunk = chunk.copy()
            chunk_id = chunk.get('title', '')

            # Add match information if available
            if chunk_id in match_lookup:
                match = match_lookup[chunk_id]
                entry = entry_lookup.get(match.index_entry_id, {})

                enriched_chunk.update({
                    'index_match': {
                        'matched': True,
                        'match_score': match.match_score,
                        'match_type': match.match_type,
                        'index_title': entry.get('title', ''),
                        'index_page': entry.get('page'),
                        'index_level': entry.get('level')
                    }
                })
            else:
                enriched_chunk['index_match'] = {
                    'matched': False,
                    'reason': 'no_suitable_match'
                }

            # Add validation status
            enriched_chunk['validation'] = {
                'validated': chunk_id in match_lookup,
                'validation_method': 'hybrid_index_font'
            }

            enriched_chunks.append(enriched_chunk)

        return enriched_chunks

    def _calculate_validation_score(self, enriched_chunks: List[Dict],
                                   missing_sections: List[Dict],
                                   orphaned_chunks: List[Dict]) -> float:
        """Calculate overall validation score"""
        total_chunks = len(enriched_chunks)
        if total_chunks == 0:
            return 0.0

        # Count validated chunks
        validated_count = sum(1 for chunk in enriched_chunks
                             if chunk.get('validation', {}).get('validated', False))

        # Calculate base score
        base_score = validated_count / total_chunks

        # Apply penalties for missing sections and orphaned chunks
        missing_penalty = len(missing_sections) * 0.05  # 5% penalty per missing section
        orphaned_penalty = len(orphaned_chunks) * 0.02  # 2% penalty per orphaned chunk

        # Calculate final score (0-100 scale)
        final_score = max(0, (base_score - missing_penalty - orphaned_penalty) * 100)

        return final_score

    def _generate_enriched_metadata(self, matches: List[ChunkMatch],
                                   missing_sections: List[Dict],
                                   orphaned_chunks: List[Dict],
                                   validation_score: float) -> Dict[str, Any]:
        """Generate enriched metadata for validation results"""
        return {
            'validation_summary': {
                'total_matches': len(matches),
                'exact_matches': len([m for m in matches if m.match_type == 'exact']),
                'partial_matches': len([m for m in matches if m.match_type == 'partial']),
                'missing_sections': len(missing_sections),
                'orphaned_chunks': len(orphaned_chunks),
                'validation_score': validation_score
            },
            'match_distribution': {
                match_type: len([m for m in matches if m.match_type == match_type])
                for match_type in ['exact', 'partial', 'inferred']
            },
            'validation_timestamp': logging.Formatter().formatTime(logging.LogRecord(
                '', 0, '', 0, '', (), None
            )),
            'validation_method': 'hybrid_font_index'
        }

    def create_missing_section_chunks(self, missing_sections: List[Dict],
                                     document_content: str) -> List[Dict]:
        """Create chunks for missing sections found in index"""
        created_chunks = []

        for section in missing_sections:
            # Try to find content for this section in the document
            section_content = self._extract_section_content(
                section, document_content
            )

            if section_content:
                chunk = {
                    'title': section['title'],
                    'content': section_content,
                    'chunk_type': 'section_recovered',
                    'chunk_classification': 'recovered_from_index',
                    'hierarchy_level': 'section',
                    'font_size': None,  # Unknown from index
                    'is_bold': None,
                    'heading_level': section.get('level', 3),
                    'page_start': section.get('page'),
                    'page_end': section.get('page'),
                    'page_count': 1,
                    'spans_multiple_pages': False,
                    'confidence': 0.7,  # Medium confidence for recovered content
                    'word_count': len(section_content.split()),
                    'content_length': len(section_content),
                    'has_complete_content': True,
                    'is_heading_chunk': True,
                    'extraction_method': 'index_recovery',
                    'source': 'missing_section_recovery'
                }
                created_chunks.append(chunk)

        logger.info(f"Created {len(created_chunks)} chunks for missing sections")
        return created_chunks

    def _extract_section_content(self, section: Dict,
                               document_content: str) -> Optional[str]:
        """Extract content for a missing section from document text"""
        title = section['title']
        page = section.get('page')

        # Simple content extraction - look for the title in the document
        lines = document_content.split('\n')
        content_lines = []
        found_start = False

        for line in lines:
            if not found_start and title.lower() in line.lower():
                found_start = True
                content_lines.append(line)
            elif found_start:
                # Stop if we hit another major heading
                if (re.match(r'^\s*#+\s', line) or
                    re.match(r'^\s*\d+\.\s', line) or
                    re.match(r'(?i)^\s*chapter\s+\d+', line)):
                    break
                content_lines.append(line)
                # Limit content extraction
                if len(content_lines) > 50:
                    break

        return '\n'.join(content_lines) if content_lines else None

    def _fallback_validation_result(self, original_chunks: List[Dict]) -> ValidationResult:
        """Return fallback result when validation fails"""
        logger.warning("Using fallback validation result")

        return ValidationResult(
            validated_chunks=original_chunks,
            missing_sections=[],
            orphaned_chunks=[],
            enriched_metadata={
                'validation_summary': {
                    'total_matches': 0,
                    'exact_matches': 0,
                    'partial_matches': 0,
                    'missing_sections': 0,
                    'orphaned_chunks': len(original_chunks),
                    'validation_score': 50.0  # Neutral score
                },
                'validation_method': 'fallback'
            },
            validation_score=50.0
        )