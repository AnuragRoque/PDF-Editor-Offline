"""
Editing Strategy hierarchy definitions.
"""

from typing import List
from app.core.models import StrategyType

STRATEGY_HIERARCHY: List[StrategyType] = [
    StrategyType.STRATEGY_1_STREAM_PATCH,
    StrategyType.STRATEGY_2_PYMUPDF_REDACT_INSERT,
    StrategyType.STRATEGY_3_PIKEPDF_OBJECT,
    StrategyType.STRATEGY_4_LOCALIZED_RECONSTRUCTION
]
