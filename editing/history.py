"""
Undo / Redo Command History and Edit Transaction Manager.
"""

from typing import List, Optional
from app.editing.commands import Command
from app.core.logging import logger

class EditHistory:
    def __init__(self, initial_pdf_path: str):
        self.initial_pdf_path = initial_pdf_path
        self.undo_stack: List[Tuple[Command, str]] = []  # List of (command, output_pdf_path)
        self.redo_stack: List[Tuple[Command, str]] = []

    def get_current_pdf_path(self) -> str:
        """Returns the PDF file path of the current active working state."""
        if self.undo_stack:
            return self.undo_stack[-1][1]
        return self.initial_pdf_path

    def push_command(self, cmd: Command, output_pdf_path: str):
        """Pushes a successfully committed edit transaction onto undo stack and clears redo stack."""
        self.undo_stack.append((cmd, output_pdf_path))
        self.redo_stack.clear()
        logger.info(f"Pushed edit command onto history. History depth: {len(self.undo_stack)}.")

    def can_undo(self) -> bool:
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        return len(self.redo_stack) > 0

    def undo(self) -> Optional[str]:
        """Rolls back the last edit command and returns previous PDF file path."""
        if not self.can_undo():
            return None
        item = self.undo_stack.pop()
        self.redo_stack.append(item)
        prev_path = self.get_current_pdf_path()
        logger.info(f"Undid edit command. Current working path: '{prev_path}'.")
        return prev_path

    def redo(self) -> Optional[str]:
        """Re-applies the next undone edit command."""
        if not self.can_redo():
            return None
        item = self.redo_stack.pop()
        self.undo_stack.append(item)
        new_path = item[1]
        logger.info(f"Redid edit command. Current working path: '{new_path}'.")
        return new_path
