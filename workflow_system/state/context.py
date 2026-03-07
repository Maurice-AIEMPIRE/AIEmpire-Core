"""
Workflow State Management - Context accumulates across steps.
Each step reads prior context and appends its own findings.
This is the memory layer that makes the system compound.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

STATE_DIR = Path(__file__).parent
HISTORY_DIR = STATE_DIR / "history"
HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def _state_file() -> Path:
    return STATE_DIR / "current_state.json"


def _pattern_file() -> Path:
    return STATE_DIR / "pattern_library.json"


def load_state() -> Dict:
    """Load accumulated workflow state."""
    f = _state_file()
    if f.exists():
        return json.loads(f.read_text())
    return {
        "created": datetime.now().isoformat(),
        "cycle": 0,
        "steps_completed": [],
        "context": {},
        "patterns": [],
        "improvements": [],
    }


def save_state(state: Dict) -> None:
    """Persist workflow state."""
    state["updated"] = datetime.now().isoformat()
    _state_file().write_text(json.dumps(state, indent=2, ensure_ascii=False))


def append_step_result(step_name: str, result: Dict) -> Dict:
    """Add a step's output to the accumulated context."""
    state = load_state()
    state["steps_completed"].append(
        {
            "step": step_name,
            "timestamp": datetime.now().isoformat(),
            "summary": result.get("summary", ""),
        }
    )
    state["context"][step_name] = result
    save_state(state)
    return state


def get_context_for_step(step_name: str) -> Dict:
    """Get all prior context relevant to the next step."""
    state = load_state()
    return {
        "cycle": state.get("cycle", 0),
        "prior_steps": state.get("context", {}),
        "patterns": state.get("patterns", []),
        "improvements": state.get("improvements", []),
    }


def advance_cycle() -> int:
    """Start a new weekly cycle. Archives old state."""
    state = load_state()
    cycle = state.get("cycle", 0) + 1

    # Archive previous cycle
    archive = HISTORY_DIR / f"cycle_{cycle - 1}_{datetime.now().strftime('%Y%m%d')}.json"
    archive.write_text(json.dumps(state, indent=2, ensure_ascii=False))

    # Carry forward patterns and improvements only
    new_state = {
        "created": datetime.now().isoformat(),
        "cycle": cycle,
        "steps_completed": [],
        "context": {},
        "patterns": state.get("patterns", []),
        "improvements": state.get("improvements", []),
    }
    save_state(new_state)
    return cycle


def add_pattern(pattern: Dict) -> None:
    """Add a discovered pattern to the persistent library."""
    state = load_state()
    state.setdefault("patterns", []).append(
        {
            **pattern,
            "discovered": datetime.now().isoformat(),
            "cycle": state.get("cycle", 0),
        }
    )
    save_state(state)

    # Also update standalone pattern library
    lib = load_pattern_library()
    lib.append(pattern)
    _pattern_file().write_text(json.dumps(lib, indent=2, ensure_ascii=False))


def load_pattern_library() -> List[Dict]:
    """Load the persistent pattern library across all cycles."""
    f = _pattern_file()
    if f.exists():
        return json.loads(f.read_text())
    return []
