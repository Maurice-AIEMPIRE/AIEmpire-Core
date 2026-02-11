"""
Helper module to import saas-platform modules with hyphens in the path.
Provides clean import paths for the API.
"""
import importlib
import sys
from pathlib import Path

# Add parent to path
_root = Path(__file__).parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

# Re-export config
from importlib import import_module as _im

def _load(attr_path):
    """Dynamically load from saas-platform directory."""
    parts = attr_path.split(".")
    # Navigate directory
    current = _root / "saas-platform"
    for part in parts[:-1]:
        current = current / part

    mod_file = current / f"{parts[-1]}.py"
    init_file = current / parts[-1] / "__init__.py"

    if mod_file.exists():
        spec = importlib.util.spec_from_file_location(attr_path, mod_file)
    elif init_file.exists():
        spec = importlib.util.spec_from_file_location(attr_path, init_file)
    else:
        raise ImportError(f"Cannot find {attr_path}")

    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
