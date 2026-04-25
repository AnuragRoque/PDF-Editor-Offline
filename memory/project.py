"""
Project Data model for persisting PDF Editor workspace state.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class ProjectData:
    project_name: str
    source_pdf_path: str
    current_pdf_path: str
    output_pdf_path: Optional[str] = None
    approved_substitutions: Dict[str, str] = field(default_factory=dict)
    history_log: List[Dict[str, Any]] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)
