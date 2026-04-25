"""
Master Edit Planner and Automatic Repair Loop.
"""

from typing import Tuple, Optional
from app.core.models import EditSpec, StrategyType, ValidationReport
from app.editing.commands import Command, ReplaceTextCommand, AddTextCommand, RemoveTextCommand
from app.editing.strategy import STRATEGY_HIERARCHY
from app.core.logging import logger

def plan_and_execute_edit(
    current_pdf_path: str,
    spec: EditSpec,
    preferred_strategy: Optional[StrategyType] = None
) -> Tuple[bool, str, ValidationReport, StrategyType]:
    """
    Executes edit with Automatic Repair Loop across strategies.
    Always verifies generated PDF by reopening and running 6-layer validation.
    Returns (success, output_pdf_path, validation_report, strategy_used).
    """
    if spec.operation.value == "replace":
        cmd = ReplaceTextCommand(spec)
    elif spec.operation.value == "add":
        cmd = AddTextCommand(spec)
    elif spec.operation.value == "remove":
        cmd = RemoveTextCommand(spec)
    else:
        cmd = ReplaceTextCommand(spec)

    strategies_to_try = [preferred_strategy] if preferred_strategy else STRATEGY_HIERARCHY

    last_report: Optional[ValidationReport] = None
    last_output_path = current_pdf_path
    last_strategy = STRATEGY_HIERARCHY[0]

    for strat in strategies_to_try:
        if strat is None:
            continue

        logger.info(f"Attempting edit operation '{spec.operation.value}' with strategy '{strat.value}'...")
        success, temp_output, report = cmd.execute(current_pdf_path, strat)
        
        last_report = report
        last_output_path = temp_output
        last_strategy = strat

        if success and report.is_valid:
            logger.info(f"Edit transaction PASS with strategy '{strat.value}'.")
            return (True, temp_output, report, strat)

        logger.warning(f"Strategy '{strat.value}' validation failed. Diagnosing failure for repair...")

    # If all failed
    logger.error("All edit strategies failed validation. Rolling back to original source state.")
    return (False, current_pdf_path, last_report or ValidationReport(is_valid=False, overall_status="FAILED"), last_strategy)
