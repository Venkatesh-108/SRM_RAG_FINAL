#!/usr/bin/env python3
"""
PDF Processor Module
Main processor that combines extraction, chunking, and indexing
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

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

logger = logging.getLogger(__name__)

class PDFProcessor:
    """Main processor for PDF extraction, chunking, and indexing"""
    
    def __init__(self, output_dir: str = "extracted_docs", index_dir: str = "indexes",
                 model_name: str = 'all-MiniLM-L6-v2', max_chunk_size: int = 8000):
        self.output_dir = Path(output_dir)
        self.index_dir = Path(index_dir)
        self.model_name = model_name
        self.max_chunk_size = max_chunk_size
        
        # Create directories
        self.output_dir.mkdir(exist_ok=True)
        self.index_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.extractor = PDFExtractor()
        self.model = SentenceTransformer(model_name)
    
    def process_document(self, pdf_path: str, document_id: str) -> Dict[str, Any]:
        """Process a single PDF document"""
        logger.info(f"Processing document: {pdf_path} -> {document_id}")
        
        # Create document directory
        doc_dir = self.output_dir / document_id
        doc_dir.mkdir(exist_ok=True)
        
        # Extract with hybrid method
        extracted_data = self.extractor.extract_document(pdf_path)
        
        logger.info(f"Extracted content length: {extracted_data['content_length']} characters")
        logger.info(f"Found {len(extracted_data['enhanced_structure']['chapters'])} chapters")
        
        # Create chunks with complete content
        chunks = self._create_chunks(extracted_data['enhanced_structure'])
        
        # Create vector index
        vector_data = self._create_vector_index(chunks)
        
        # Save all data
        self._save_data(doc_dir, document_id, extracted_data, chunks)
        
        # Save vector indexes
        self._save_vector_indexes(document_id, vector_data)
        
        return {
            'document_id': document_id,
            'total_chapters': len(extracted_data['enhanced_structure']['chapters']),
            'total_sections': extracted_data['enhanced_structure']['total_sections'],
            'total_chunks': len(chunks),
            'content_length': extracted_data['content_length'],
            'vector_dimension': vector_data['embedding_model'],
            'extraction_method': 'hybrid_docling_font',
            'processing_time': datetime.now().isoformat()
        }
    
    def _create_chunks(self, structure: Dict) -> List[Dict]:
        """Create chunks preserving complete content with heading metadata"""
        chunks = []
        
        for chapter in structure['chapters']:
            # Chapter overview chunk
            chapter_chunk = self._create_chapter_chunk(chapter)
            chunks.append(chapter_chunk)
            
            # Individual section chunks with complete content
            for section in chapter.get('sections', []):
                section_chunk = self._create_section_chunk(section, chapter)
                chunks.append(section_chunk)
        
        logger.info(f"Created {len(chunks)} chunks with complete content")
        return chunks
    
    def _create_chapter_chunk(self, chapter: Dict) -> Dict:
        """Create chapter chunk with complete content"""
        
        # Include complete chapter content
        content = f"# {chapter['title']}\n\n{chapter.get('complete_content', '')}"
        
        # Add section overview if available
        if chapter.get('sections'):
            content += "\n\n## Sections in this chapter:\n"
            for section in chapter['sections']:
                content += f"- {section['title']}\n"
        
        return {
            'content': content,
            'title': chapter['title'],
            'chunk_type': 'complete_chapter',
            'hierarchy_level': 'chapter',
            'font_size': chapter.get('font_size', 0),
            'is_bold': chapter.get('is_bold', False),
            'heading_level': chapter.get('heading_level', 1),
            'page': chapter.get('page', 1),
            'pages': [chapter.get('page', 1)],
            'primary_page': chapter.get('page', 1),
            'confidence': chapter.get('confidence', 0.5),
            'word_count': len(content.split()),
            'content_length': len(content),
            'has_complete_content': True,
            'is_heading_chunk': True,
            'searchable_titles': [chapter['title']],
            'extraction_method': 'hybrid_docling_font'
        }
    
    def _create_section_chunk(self, section: Dict, parent_chapter: Dict) -> Dict:
        """Create section chunk with complete content"""
        
        # Format with hierarchy and complete content
        content = f"## {section['title']}\n"
        content += f"*Chapter: {parent_chapter['title']}*\n"
        content += f"*Page: {section.get('page', 'N/A')}*\n\n"
        content += section.get('complete_content', '')
        
        return {
            'content': content,
            'title': section['title'],
            'chunk_type': 'complete_section',
            'hierarchy_level': 'section',
            'chapter_title': parent_chapter['title'],
            'font_size': section.get('font_size', 0),
            'is_bold': section.get('is_bold', False),
            'heading_level': section.get('heading_level', 2),
            'page': section.get('page', 1),
            'pages': [section.get('page', 1)],
            'primary_page': section.get('page', 1),
            'confidence': section.get('confidence', 0.5),
            'word_count': len(content.split()),
            'content_length': len(content),
            'has_complete_content': True,
            'is_heading_chunk': True,
            'searchable_titles': [section['title'], parent_chapter['title']],
            'extraction_method': 'hybrid_docling_font'
        }
    
    def _create_vector_index(self, chunks: List[Dict]) -> Dict[str, Any]:
        """Create vector index from chunks"""
        logger.info(f"Creating vector index for {len(chunks)} chunks")
        
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
        
        # Prepare metadata
        metadata = []
        for chunk in chunks:
            metadata.append({
                'title': chunk['title'],
                'chunk_type': chunk['chunk_type'],
                'hierarchy_level': chunk['hierarchy_level'],
                'font_size': chunk.get('font_size', 0),
                'is_bold': chunk.get('is_bold', False),
                'heading_level': chunk.get('heading_level', 0),
                'page': chunk.get('page', 1),
                'primary_page': chunk.get('primary_page', 1),
                'confidence': chunk.get('confidence', 0.5),
                'is_heading_chunk': chunk.get('is_heading_chunk', False),
                'extraction_method': chunk.get('extraction_method', 'unknown')
            })
        
        return {
            'index': index,
            'metadata': metadata,
            'chunks': [chunk['content'] for chunk in chunks],
            'embedding_model': self.model_name,
            'dimension': dimension
        }
    
    def _save_data(self, doc_dir: Path, document_id: str, extracted_data: Dict, chunks: List[Dict]):
        """Save extracted data and chunks"""
        
        # Save complete markdown content
        with open(doc_dir / "complete_content.md", 'w', encoding='utf-8') as f:
            f.write(extracted_data['full_text'])
        
        # Save structured data from Docling
        try:
            with open(doc_dir / "docling_structure.json", 'w', encoding='utf-8') as f:
                json.dump(extracted_data['structured_json'], f, indent=2, ensure_ascii=False)
        except TypeError:
            # If not JSON serializable, save just the text content
            with open(doc_dir / "docling_content.md", 'w', encoding='utf-8') as f:
                f.write(extracted_data['structured_json'].get('main_text', ''))
        
        # Save font analysis
        with open(doc_dir / "font_analysis.json", 'w', encoding='utf-8') as f:
            json.dump(extracted_data['font_analysis'], f, indent=2, ensure_ascii=False)
        
        # Save enhanced structure
        with open(doc_dir / "enhanced_structure.json", 'w', encoding='utf-8') as f:
            json.dump(extracted_data['enhanced_structure'], f, indent=2, ensure_ascii=False)
        
        # Save chunks
        with open(doc_dir / "enhanced_chunks.json", 'w', encoding='utf-8') as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)
        
        # Create heading summary
        headings = []
        for chapter in extracted_data['enhanced_structure']['chapters']:
            headings.append({
                'title': chapter['title'],
                'font_size': chapter.get('font_size', 0),
                'is_bold': chapter.get('is_bold', False),
                'heading_level': chapter.get('heading_level', 1),
                'page': chapter.get('page', 1),
                'confidence': chapter.get('confidence', 0.5)
            })
            
            for section in chapter.get('sections', []):
                headings.append({
                    'title': section['title'],
                    'font_size': section.get('font_size', 0),
                    'is_bold': section.get('is_bold', False),
                    'heading_level': section.get('heading_level', 2),
                    'page': section.get('page', 1),
                    'confidence': section.get('confidence', 0.5)
                })
        
        with open(doc_dir / "heading_summary.json", 'w', encoding='utf-8') as f:
            json.dump(headings, f, indent=2, ensure_ascii=False)
        
        # Save processing summary
        summary = {
            'document_id': document_id,
            'processing_date': datetime.now().isoformat(),
            'extraction_method': 'hybrid_docling_font',
            'total_content_length': extracted_data['content_length'],
            'total_chapters': len(extracted_data['enhanced_structure']['chapters']),
            'total_sections': extracted_data['enhanced_structure']['total_sections'],
            'total_chunks': len(chunks),
            'font_analysis_summary': {
                'body_size': extracted_data['font_analysis']['body_size'],
                'heading_sizes': extracted_data['font_analysis']['heading_sizes'],
                'headings_detected': len(extracted_data['font_analysis']['heading_map'])
            }
        }
        
        with open(doc_dir / "processing_summary.json", 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Data saved to {doc_dir}")
    
    def _save_vector_indexes(self, document_id: str, vector_data: Dict):
        """Save vector indexes"""
        
        # Save FAISS index
        index_path = self.index_dir / f"{document_id}.faiss"
        faiss.write_index(vector_data['index'], str(index_path))
        
        # Save metadata
        metadata_path = self.index_dir / f"{document_id}_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': vector_data['metadata'],
                'chunks': vector_data['chunks'],
                'embedding_model': vector_data['embedding_model']
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Vector indexes saved to {self.index_dir}")
    
    def process_batch(self, pdf_directory: str, output_dir: str = None, index_dir: str = None) -> List[Dict[str, Any]]:
        """Process all PDFs in a directory"""
        pdf_dir = Path(pdf_directory)
        if not pdf_dir.exists():
            raise ValueError(f"PDF directory not found: {pdf_directory}")
        
        # Update output directories if provided
        if output_dir:
            self.output_dir = Path(output_dir)
            self.output_dir.mkdir(exist_ok=True)
        if index_dir:
            self.index_dir = Path(index_dir)
            self.index_dir.mkdir(exist_ok=True)
        
        # Find all PDF files
        pdf_files = list(pdf_dir.glob("*.pdf"))
        if not pdf_files:
            raise ValueError(f"No PDF files found in {pdf_directory}")
        
        results = []
        for pdf_file in pdf_files:
            # Create document ID from filename
            document_id = pdf_file.stem.replace(' ', '_').replace('-', '_')
            
            try:
                result = self.process_document(str(pdf_file), document_id)
                results.append(result)
                logger.info(f"Successfully processed: {pdf_file.name}")
            except Exception as e:
                logger.error(f"Failed to process {pdf_file.name}: {e}")
                results.append({
                    'document_id': document_id,
                    'status': 'failed',
                    'error': str(e)
                })
        
        return results
