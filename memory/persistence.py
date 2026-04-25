"""
Workspace state, user font approvals, and settings persistence.
"""

import json
from pathlib import Path
from typing import Optional
from app.memory.project import ProjectData
from app.core.logging import logger

def save_project(project: ProjectData, project_file_path: str) -> bool:
    """Saves ProjectData to JSON file."""
    try:
        data = {
            "project_name": project.project_name,
            "source_pdf_path": project.source_pdf_path,
            "current_pdf_path": project.current_pdf_path,
            "output_pdf_path": project.output_pdf_path,
            "approved_substitutions": project.approved_substitutions,
            "history_log": project.history_log,
            "settings": project.settings
        }
        with open(project_file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Project saved to '{project_file_path}'.")
        return True
    except Exception as e:
        logger.error(f"Failed to save project to '{project_file_path}': {e}")
        return False

def load_project(project_file_path: str) -> Optional[ProjectData]:
    """Loads ProjectData from JSON file."""
    try:
        path = Path(project_file_path)
        if not path.exists():
            return None
        with open(project_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return ProjectData(
            project_name=data.get("project_name", "Untitled"),
            source_pdf_path=data.get("source_pdf_path", ""),
            current_pdf_path=data.get("current_pdf_path", ""),
            output_pdf_path=data.get("output_pdf_path"),
            approved_substitutions=data.get("approved_substitutions", {}),
            history_log=data.get("history_log", []),
            settings=data.get("settings", {})
        )
    except Exception as e:
        logger.error(f"Failed to load project from '{project_file_path}': {e}")
        return None
