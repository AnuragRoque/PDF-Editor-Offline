# Local Precision PDF Editor

A **fully offline** desktop application for *surgical* text editing of PDF documents.
It replaces, adds, and removes text **in place** — preserving the original layout,
fonts, colors, and geometry — and then **verifies every edit** with a multi-layer
validation pipeline (including a rendered pixel-diff) before committing it.

Nothing ever leaves your machine: no network calls, no cloud services, no telemetry.

---

## Key features

- **Surgical text replacement** using baseline-aware redaction so only the target
  glyphs are erased — adjacent lines are never disturbed.
- **Strategy hierarchy with fallback**: direct content-stream patch → PyMuPDF
  redact + reinsert → pikepdf object edit → localized reconstruction.
- **6-layer validation** on every edit: Integrity → Structural → Content →
  Typography → Geometry → Visual. Edits that change more than a small pixel budget
  *outside* the target region are automatically rolled back.
- **Undo / redo** history of edit transactions.
- **Responsive UI** — document analysis and editing run on background threads.
- Dark, modern PyQt6 interface with a text list, page canvas, and properties inspector.
- Scanned / image-only PDFs are detected and rejected (editing requires real text).

---

## Requirements

- **Python 3.12+** (developed and tested on 3.12)
- The packages listed in [`requirements.txt`](requirements.txt):
  PyMuPDF, pikepdf, PyQt6, Pillow, numpy (plus pytest for the test suite).

## Installation

```bash
# From the project root
python -m venv .venv

# Activate the virtual environment
#   Windows (PowerShell):
.venv\Scripts\Activate.ps1
#   macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

## Usage

Launch the application:

```bash
python run.py
```

Optionally open a PDF directly from the command line:

```bash
python run.py path/to/document.pdf
```

### Editing workflow

1. **Open** a text-based PDF (`File → Open PDF...`).
2. Select a text element from the left **text list** or by clicking it on the canvas.
3. Edit its content in the right-hand **Properties** panel and apply the change.
4. The edit runs through the validation pipeline; on success it is committed, and on
   failure it is rolled back automatically.
5. Use **Undo / Redo** as needed, then **Save PDF As...** to export the result.

---

## Project structure

```
app/
  core/         Config, domain models, exceptions, logging
  pdf/          Loading, analysis, text detection, fonts, geometry, rendering, editing engines
  editing/      Command pattern, strategy hierarchy, planner, undo/redo history
  validation/   6-layer validation pipeline (structural → visual pixel-diff)
  ui/           PyQt6 main window, canvas, panels, dialogs
  memory/       Project/session persistence
  main.py       Application entry point
run.py          Root launcher
tests/          pytest suite
```

## Running the tests

```bash
python -m pytest
```

## How editing works (under the hood)

1. [`app/pdf/analyzer.py`](app/pdf/analyzer.py) parses the PDF into a `DocumentModel`
   of text spans (bounding box, font, size, color, baseline origin).
2. An edit is described by an `EditSpec` and dispatched through
   [`app/editing/planner.py`](app/editing/planner.py), which tries each strategy in the
   hierarchy until one produces a valid result.
3. The core replacement computes a tight, baseline-aware redaction rectangle
   (`compute_tight_redact_rect` in [`app/pdf/text_replacer.py`](app/pdf/text_replacer.py)),
   erases the target text, and reinserts the new text at the original baseline.
4. Every candidate output is re-opened and validated by
   [`app/validation/validator.py`](app/validation/validator.py); the visual layer renders
   before/after pages and rejects the edit if too many pixels change outside the target box.

---

## Notes & limitations

- Editing requires a **text-based** PDF; scanned/image-only documents are not supported.
- The strategy fallback currently retries with alternate engines rather than
  re-fitting the spec (e.g. adjusting font size) between attempts.
- Application data (logs, temp files) is stored under `~/.precision_pdf_editor/`.
