"""
Custom exception definitions for Local Precision PDF Editor.
"""

class PDFEditorError(Exception):
    """Base exception for all PDF Editor errors."""
    pass

class NonEditablePDFError(PDFEditorError):
    """Raised when PDF does not contain reliable editable text (e.g. scanned image-only PDF)."""
    pass

class FontError(PDFEditorError):
    """Raised when font resolution or font embedding fails."""
    pass

class FontNotFoundError(FontError):
    """Raised when exact or suitable fallback font cannot be found."""
    pass

class OverflowError(PDFEditorError):
    """Raised when replacement text exceeds bounding box and auto-fit is disabled."""
    pass

class ValidationError(PDFEditorError):
    """Base exception for validation failures."""
    def __init__(self, message: str, layer: str = "general", details: dict = None):
        super().__init__(message)
        self.layer = layer
        self.details = details or {}

class StructuralValidationError(ValidationError):
    """Raised when structural validation (page count, boxes, metadata) fails."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, layer="structural", details=details)

class ContentValidationError(ValidationError):
    """Raised when content validation (unexpected text edit / missing text) fails."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, layer="content", details=details)

class TypographyValidationError(ValidationError):
    """Raised when font, size, weight, color fails on untouched or target text."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, layer="typography", details=details)

class GeometryValidationError(ValidationError):
    """Raised when bounding box, coordinates, or matrix drift is detected."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, layer="geometry", details=details)

class VisualValidationError(ValidationError):
    """Raised when visual diff outside expected bounding box exceeds threshold."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, layer="visual", details=details)

class TransactionError(PDFEditorError):
    """Raised when an edit transaction fails and rolls back."""
    pass

class RepairFailedError(PDFEditorError):
    """Raised when automatic repair engine exhausts all strategies."""
    pass
