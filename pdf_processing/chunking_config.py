#!/usr/bin/env python3
"""
Configurable Chunking Settings
Allows customization of chunking behavior for different document types and scenarios
"""

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class ChunkingConfig:
    """Configuration for PDF chunking behavior"""

    # Section boundary detection
    max_section_lines: int = 100
    min_content_lines: int = 3
    early_stop_threshold: int = 10

    # Content size limits
    max_chunk_size: int = 8000
    target_chunk_size: int = 4000
    min_chunk_size: int = 100

    # Boundary detection patterns
    strong_boundary_patterns: List[str] = None
    weak_boundary_patterns: List[str] = None
    transition_markers: List[str] = None

    # Quality thresholds
    max_over_inclusion_ratio: float = 0.3  # Max % of chunks that can have over-inclusion
    max_headings_per_chunk: int = 5
    max_procedure_blocks: int = 2

    def __post_init__(self):
        """Set default patterns if not provided"""
        if self.strong_boundary_patterns is None:
            self.strong_boundary_patterns = [
                r'^#+\s+(?:Chapter|Appendix)\s+\d+',
                r'^#+\s+(?:Prerequisites|Before you begin|Next steps|What to do next)',
                r'^#+\s+(?:Results|Outcome|Summary)',
                r'^#+\s+(?:About this task|Steps|Procedure)',
            ]

        if self.weak_boundary_patterns is None:
            self.weak_boundary_patterns = [
                r'^#+\s+(?:Update|Configure|Install|Setup|Create|Delete|Add|Remove)',
                r'^#+\s+\w+\s+(?:Discovery|Configuration|Installation)',
                r'^#+\s+(?:Export|Import|Backup|Restore)',
            ]

        if self.transition_markers is None:
            self.transition_markers = [
                'About this task',
                'Before you begin',
                'Prerequisites',
                'What to do next',
                'Next steps',
                'Results',
                'Troubleshooting',
                'Examples',
                'Notes'
            ]


class DocumentTypeConfigs:
    """Predefined configurations for different document types"""

    @staticmethod
    def get_config(doc_type: str = "default") -> ChunkingConfig:
        """Get configuration for specific document type"""

        configs = {
            "upgrade_guide": ChunkingConfig(
                max_section_lines=50,  # Shorter sections for procedures
                min_content_lines=2,
                target_chunk_size=3000,  # Smaller chunks for procedural content
                max_headings_per_chunk=3,
                strong_boundary_patterns=[
                    r'^#+\s+(?:Chapter|Appendix)\s+\d+',
                    r'^#+\s+(?:Prerequisites|Before you begin)',
                    r'^#+\s+(?:About this task|Steps)',
                    r'^#+\s+(?:Results|What to do next)',
                    r'^#+\s+(?:Update|Upgrade)\s+\w+',  # Specific to upgrade docs
                ],
                weak_boundary_patterns=[
                    r'^#+\s+(?:Export|Import|Delete|Configure)',
                    r'^#+\s+\w+\s+(?:Discovery|Switch)',
                ],
            ),

            "installation_guide": ChunkingConfig(
                max_section_lines=80,
                target_chunk_size=5000,
                strong_boundary_patterns=[
                    r'^#+\s+(?:Chapter|Section)\s+\d+',
                    r'^#+\s+(?:Prerequisites|System Requirements)',
                    r'^#+\s+(?:Installation|Configuration)',
                    r'^#+\s+(?:Post-installation|Verification)',
                ],
            ),

            "configuration_guide": ChunkingConfig(
                max_section_lines=60,
                target_chunk_size=4000,
                max_headings_per_chunk=4,
                strong_boundary_patterns=[
                    r'^#+\s+(?:Configuring|Setting up)',
                    r'^#+\s+(?:Prerequisites|Requirements)',
                    r'^#+\s+(?:Examples|Use Cases)',
                ],
            ),

            "solution_pack_guide": ChunkingConfig(
                max_section_lines=70,
                target_chunk_size=4500,
                strong_boundary_patterns=[
                    r'^#+\s+(?:Deploying|Installing)',
                    r'^#+\s+(?:Frontend|Backend)\s+Server',
                    r'^#+\s+(?:Load\s+[Bb]alancer|NFS\s+[Ss]hare)',
                ],
            ),

            "srm_specific": ChunkingConfig(
                max_section_lines=80,
                min_content_lines=3,
                target_chunk_size=4500,
                max_chunk_size=8000,
                max_headings_per_chunk=4,
                max_over_inclusion_ratio=0.25,
                strong_boundary_patterns=[
                    # Chapter and major section boundaries
                    r'^#+\s+(?:Chapter|Section)\s+\d+',
                    r'^#+\s+(?:Part|Appendix)\s+[A-Z]',

                    # SRM-specific installation and configuration
                    r'^#+\s+(?:Installing|Deploying)\s+.*(?:SolutionPack|Solution Pack)',
                    r'^#+\s+(?:Configuring|Setting up)\s+.*(?:SRM|StorageResourceMonitor)',
                    r'^#+\s+(?:Adding|Installing)\s+.*(?:Discovery|Device)',

                    # Major procedural boundaries
                    r'^#+\s+(?:Prerequisites|System Requirements|Before you begin)',
                    r'^#+\s+(?:Post-installation|Verification|Next steps)',
                    r'^#+\s+(?:Troubleshooting|Known Issues)',

                    # SRM-specific components
                    r'^#+\s+(?:Frontend|Backend)\s+Server',
                    r'^#+\s+(?:Load\s+[Bb]alancer|NFS\s+[Ss]hare)',
                    r'^#+\s+(?:Database|MySQL)\s+Configuration',
                ],
                weak_boundary_patterns=[
                    # Common SRM operations
                    r'^#+\s+(?:Install|Add|Remove|Delete|Update|Upgrade)',
                    r'^#+\s+(?:Configure|Setup|Enable|Disable)',
                    r'^#+\s+(?:Export|Import|Backup|Restore)',
                    r'^#+\s+(?:Create|Modify|Edit)\s+.*(?:Report|Task|Schedule)',

                    # SRM discovery and monitoring
                    r'^#+\s+.*Discovery.*(?:Configuration|Setup)',
                    r'^#+\s+.*Monitoring.*(?:Setup|Configuration)',
                    r'^#+\s+.*SolutionPack.*(?:Installation|Configuration)',

                    # Specific SRM features
                    r'^#+\s+(?:Shared\s+Reports|Scheduled\s+Tasks)',
                    r'^#+\s+(?:Management\s+Functions|User\s+Reports)',
                ],
                transition_markers=[
                    'About this task',
                    'Before you begin',
                    'Prerequisites',
                    'System requirements',
                    'What to do next',
                    'Next steps',
                    'Results',
                    'Troubleshooting',
                    'Examples',
                    'Notes',
                    'Important',
                    'Caution',
                    'Warning',
                    'SolutionPack installation',
                    'Device discovery',
                    'Configuration verification'
                ]
            ),

            "default": ChunkingConfig()  # Standard settings
        }

        return configs.get(doc_type, configs["default"])

    @staticmethod
    def detect_document_type(filename: str, content_preview: str = "") -> str:
        """Auto-detect document type from filename and content"""
        filename_lower = filename.lower()
        content_lower = content_preview.lower()

        # Check for SRM-specific documents first
        if any(term in filename_lower for term in ['srm', 'storage resource monitor', 'storageresourcemonitor']):
            return "srm_specific"
        elif any(term in content_lower for term in ['srm', 'storage resource monitor', 'solutionpack', 'device discovery']):
            return "srm_specific"

        # Fallback to generic document types
        elif any(term in filename_lower for term in ['upgrade', 'migration']):
            return "upgrade_guide"
        elif any(term in filename_lower for term in ['install', 'deployment']):
            return "installation_guide"
        elif any(term in filename_lower for term in ['config', 'configuration']):
            return "configuration_guide"
        elif any(term in filename_lower for term in ['solution', 'pack']):
            return "solution_pack_guide"
        elif any(term in content_lower for term in ['upgrade', 'migration', 'version']):
            return "upgrade_guide"
        else:
            return "default"


def validate_chunking_quality(chunks: List[Dict[str, Any]], config: ChunkingConfig) -> Dict[str, Any]:
    """Validate chunking quality against configuration thresholds"""

    total_chunks = len(chunks)
    if total_chunks == 0:
        return {"status": "error", "message": "No chunks found"}

    issues = []
    over_inclusion_count = 0

    for chunk in chunks:
        content = chunk.get('content', '')
        chunk_issues = []

        # Check for over-inclusion indicators
        heading_count = content.count('##') + content.count('# ')
        if heading_count > config.max_headings_per_chunk:
            chunk_issues.append(f'Too many headings ({heading_count})')

        procedure_blocks = content.count('Steps\n1.') + content.count('## Steps')
        if procedure_blocks > config.max_procedure_blocks:
            chunk_issues.append(f'Multiple procedures ({procedure_blocks})')

        if len(content) > config.max_chunk_size:
            chunk_issues.append(f'Oversized ({len(content)} chars)')

        if chunk_issues:
            over_inclusion_count += 1
            issues.append({
                'title': chunk.get('title', 'Unknown'),
                'issues': chunk_issues
            })

    over_inclusion_ratio = over_inclusion_count / total_chunks

    status = "good"
    if over_inclusion_ratio > config.max_over_inclusion_ratio:
        status = "needs_improvement"
    elif over_inclusion_ratio > config.max_over_inclusion_ratio * 0.5:
        status = "acceptable"

    return {
        "status": status,
        "over_inclusion_ratio": over_inclusion_ratio,
        "problematic_chunks": over_inclusion_count,
        "total_chunks": total_chunks,
        "issues": issues[:5],  # Show top 5 issues
        "recommendation": _get_quality_recommendation(status, over_inclusion_ratio)
    }


def _get_quality_recommendation(status: str, ratio: float) -> str:
    """Get recommendation based on quality assessment"""
    if status == "good":
        return "Chunking quality is excellent. No improvements needed."
    elif status == "acceptable":
        return f"Chunking quality is acceptable ({ratio:.1%} over-inclusion). Consider fine-tuning boundary detection."
    else:
        return f"Chunking quality needs improvement ({ratio:.1%} over-inclusion). Recommend adjusting section boundary patterns."