"""LogicGate - learn to build electric and logic circuits by drag and drop."""
__version__ = "0.1.0"
RELEASE_DATE = "2026-11-04"

# True when running in a web browser (pygbag / WebAssembly).
import sys as _sys
WEB = _sys.platform == "emscripten"
