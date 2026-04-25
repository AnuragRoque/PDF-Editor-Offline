"""
Command Pattern implementation for Undoable Edit Transactions.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple
from app.core.models import EditSpec, EditOperation, StrategyType, EditTransaction, ValidationReport
from app.pdf.writer import create_temp_pdf_path
from app.pdf.text_replacer import execute_replace_strategy
from app.pdf.text_inserter import execute_add_text
from app.pdf.text_remover import execute_remove_text
from app.validation.validator import validate_pdf_edit
from app.core.logging import logger

class Command(ABC):
    """Abstract base class for all undoable edit commands."""
    def __init__(self, spec: EditSpec):
        self.spec = spec
        self.transaction: Optional[EditTransaction] = None

    @abstractmethod
    def execute(self, current_pdf_path: str, strategy: StrategyType) -> Tuple[bool, str, ValidationReport]:
        pass

class ReplaceTextCommand(Command):
    """Command for replacing target text span with new string."""
    def execute(self, current_pdf_path: str, strategy: StrategyType) -> Tuple[bool, str, ValidationReport]:
        temp_output = create_temp_pdf_path("edit_rep_")
        success, used_strat, msg = execute_replace_strategy(current_pdf_path, temp_output, self.spec, strategy)

        if not success:
            return (False, temp_output, ValidationReport(is_valid=False, overall_status="FAILED"))

        validation = validate_pdf_edit(current_pdf_path, temp_output, self.spec)
        self.transaction = EditTransaction(
            spec=self.spec,
            strategy_used=used_strat,
            validation=validation,
            temp_pdf_path=temp_output,
            status="COMMITTED" if validation.is_valid else "FAILED"
        )
        return (validation.is_valid, temp_output, validation)

class AddTextCommand(Command):
    """Command for inserting new text span on target page."""
    def execute(self, current_pdf_path: str, strategy: StrategyType) -> Tuple[bool, str, ValidationReport]:
        temp_output = create_temp_pdf_path("edit_add_")
        success, msg = execute_add_text(current_pdf_path, temp_output, self.spec)

        if not success:
            return (False, temp_output, ValidationReport(is_valid=False, overall_status="FAILED"))

        validation = validate_pdf_edit(current_pdf_path, temp_output, self.spec)
        self.transaction = EditTransaction(
            spec=self.spec,
            strategy_used=strategy,
            validation=validation,
            temp_pdf_path=temp_output,
            status="COMMITTED" if validation.is_valid else "FAILED"
        )
        return (validation.is_valid, temp_output, validation)

class RemoveTextCommand(Command):
    """Command for surgically removing text span."""
    def execute(self, current_pdf_path: str, strategy: StrategyType) -> Tuple[bool, str, ValidationReport]:
        temp_output = create_temp_pdf_path("edit_rem_")
        success, msg = execute_remove_text(current_pdf_path, temp_output, self.spec)

        if not success:
            return (False, temp_output, ValidationReport(is_valid=False, overall_status="FAILED"))

        validation = validate_pdf_edit(current_pdf_path, temp_output, self.spec)
        self.transaction = EditTransaction(
            spec=self.spec,
            strategy_used=strategy,
            validation=validation,
            temp_pdf_path=temp_output,
            status="COMMITTED" if validation.is_valid else "FAILED"
        )
        return (validation.is_valid, temp_output, validation)
