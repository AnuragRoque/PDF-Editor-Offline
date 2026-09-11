"""
Data models and core domain objects for Local Precision PDF Editor.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any, Optional
from enum import Enum
import uuid
import time

# PyMuPDF span font_flags bit masks (see get_text("dict") span "flags").
#   bit 0 (1)  = superscripted
#   bit 1 (2)  = italic
#   bit 2 (4)  = serifed
#   bit 3 (8)  = monospaced
#   bit 4 (16) = bold
FONT_FLAG_SUPERSCRIPT = 1
FONT_FLAG_ITALIC = 2
FONT_FLAG_SERIF = 4
FONT_FLAG_MONOSPACE = 8
FONT_FLAG_BOLD = 16

@dataclass
class BBox:
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        return max(0.0, self.x1 - self.x0)

    @property
    def height(self) -> float:
        return max(0.0, self.y1 - self.y0)

    @property
    def tuple(self) -> Tuple[float, float, float, float]:
        return (self.x0, self.y0, self.x1, self.y1)

    def intersects(self, other: "BBox") -> bool:
        return not (self.x1 < other.x0 or self.x0 > other.x1 or self.y1 < other.y0 or self.y0 > other.y1)

    def pad(self, padding: float) -> "BBox":
        return BBox(
            max(0.0, self.x0 - padding),
            max(0.0, self.y0 - padding),
            self.x1 + padding,
            self.y1 + padding
        )

    def to_dict(self) -> Dict[str, float]:
        return {"x0": self.x0, "y0": self.y0, "x1": self.x1, "y1": self.y1}

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "BBox":
        return cls(x0=data["x0"], y0=data["y0"], x1=data["x1"], y1=data["y1"])

@dataclass
class ColorInfo:
    r: float = 0.0
    g: float = 0.0
    b: float = 0.0
    a: float = 1.0

    @property
    def rgb_255(self) -> Tuple[int, int, int]:
        return (int(self.r * 255), int(self.g * 255), int(self.b * 255))

    @property
    def hex_color(self) -> str:
        r, g, b = self.rgb_255
        return f"#{r:02x}{g:02x}{b:02x}"

    @classmethod
    def from_tuple(cls, color_tuple: Any) -> "ColorInfo":
        if not color_tuple:
            return cls(0.0, 0.0, 0.0)
        if isinstance(color_tuple, (int, float)):
            val = float(color_tuple)
            return cls(val, val, val)
        if len(color_tuple) == 3:
            return cls(float(color_tuple[0]), float(color_tuple[1]), float(color_tuple[2]))
        elif len(color_tuple) == 4:
            # Check if CMYK or RGBA
            r, g, b, a = [float(x) for x in color_tuple]
            return cls(r, g, b, a)
        return cls(0.0, 0.0, 0.0)

@dataclass
class FontInfo:
    name: str
    family: str = ""
    weight: str = "normal"  # normal, bold
    style: str = "normal"   # normal, italic
    size: float = 12.0
    is_embedded: bool = False
    is_subset: bool = False
    encoding: str = ""

@dataclass
class TextSpan:
    id: str
    page_num: int
    text: str
    bbox: BBox
    font_name: str
    font_size: float
    font_flags: int
    color: ColorInfo
    origin: Tuple[float, float]
    matrix: Tuple[float, float, float, float, float, float]
    rotation: float = 0.0
    block_idx: int = 0
    line_idx: int = 0
    span_idx: int = 0

    @property
    def is_bold(self) -> bool:
        name = self.font_name.lower()
        return bool(self.font_flags & FONT_FLAG_BOLD) or "bold" in name or "black" in name or "heavy" in name

    @property
    def is_italic(self) -> bool:
        name = self.font_name.lower()
        return bool(self.font_flags & FONT_FLAG_ITALIC) or "italic" in name or "oblique" in name

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "page_num": self.page_num,
            "text": self.text,
            "bbox": self.bbox.to_dict(),
            "font_name": self.font_name,
            "font_size": self.font_size,
            "color": self.color.hex_color,
            "origin": list(self.origin),
            "rotation": self.rotation,
            "block_idx": self.block_idx,
            "line_idx": self.line_idx,
            "span_idx": self.span_idx
        }

@dataclass
class ImageInfo:
    id: str
    page_num: int
    bbox: BBox
    width: int
    height: int
    ext: str = "png"

@dataclass
class AnnotationInfo:
    id: str
    page_num: int
    type_name: str
    bbox: BBox
    content: str = ""

@dataclass
class LinkInfo:
    id: str
    page_num: int
    bbox: BBox
    uri: str = ""
    dest_page: Optional[int] = None

@dataclass
class PageModel:
    page_num: int
    width: float
    height: float
    rotation: int
    mediabox: Tuple[float, float, float, float]
    cropbox: Tuple[float, float, float, float]
    spans: List[TextSpan] = field(default_factory=list)
    images: List[ImageInfo] = field(default_factory=list)
    annotations: List[AnnotationInfo] = field(default_factory=list)
    links: List[LinkInfo] = field(default_factory=list)

@dataclass
class DocumentModel:
    file_path: str
    page_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    pages: List[PageModel] = field(default_factory=list)
    is_encrypted: bool = False
    is_text_based: bool = True
    fonts: List[FontInfo] = field(default_factory=list)

class EditOperation(str, Enum):
    REPLACE = "replace"
    ADD = "add"
    REMOVE = "remove"

class StrategyType(str, Enum):
    STRATEGY_1_STREAM_PATCH = "content_stream_patch"
    STRATEGY_2_PYMUPDF_REDACT_INSERT = "pymupdf_redact_insert"
    STRATEGY_3_PIKEPDF_OBJECT = "pikepdf_object"
    STRATEGY_4_LOCALIZED_RECONSTRUCTION = "localized_reconstruction"

@dataclass
class EditSpec:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    page_num: int = 0
    operation: EditOperation = EditOperation.REPLACE
    target_span: Optional[TextSpan] = None
    target_text: str = ""
    replacement_text: str = ""
    target_bbox: Optional[BBox] = None
    font_name: str = "Helvetica"
    font_size: float = 12.0
    color: Optional[ColorInfo] = None
    matrix: Optional[Tuple[float, float, float, float, float, float]] = None
    origin: Optional[Tuple[float, float]] = None
    
    # Fit override controls
    manual_font_size: Optional[float] = None
    manual_hscale: float = 100.0  # Horizontal scaling percentage
    manual_offset_x: float = 0.0
    manual_offset_y: float = 0.0

@dataclass
class ValidationLayerResult:
    layer_name: str
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ValidationReport:
    is_valid: bool
    layers: Dict[str, ValidationLayerResult] = field(default_factory=dict)
    unexpected_diff_pixels: int = 0
    diff_image_path: Optional[str] = None
    overall_status: str = "PASS"

@dataclass
class EditTransaction:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    spec: EditSpec = field(default_factory=EditSpec)
    strategy_used: StrategyType = StrategyType.STRATEGY_2_PYMUPDF_REDACT_INSERT
    validation: Optional[ValidationReport] = None
    temp_pdf_path: Optional[str] = None
    status: str = "PENDING"  # PENDING, COMMITTED, ROLLED_BACK
