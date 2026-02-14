from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from automation.utils.files import ensure_dir, write_json


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STATE_PATH = ROOT / "content_factory" / "deliverables" / "shorts_revenue" / "strategy_state.json"
NUGGET_REGISTRY_PATH = ROOT / "ai-vault" / "nuggets" / "nugget_registry.json"
ALLOWED_ASSET_TYPES = {"hook", "angle", "offer", "process", "metric", "story"}


def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def default_state() -> Dict[str, Any]:
    return {
        "updated_at": _now_iso(),
        "patterns": [],
        "history": [],
        "kpi_gates": {
            "target_vph": 120.0,
            "min_like_rate": 0.03,
            "min_comment_rate": 0.005,
        },
        "adaptive": {
            "low_vph_streak": 0,
            "hook_intensity": 1,
            "script_hook_setup_word_cap": 120,
            "force_new_angle_cluster": False,
            "emotional_framing_boost": False,
            "story_contrarian_boost_pct": 0,
            "cta_mode": "default",
            "cta_binary_required": False,
        },
        "next_test_matrix": [],
    }


def load_strategy_state(path: Path = DEFAULT_STATE_PATH) -> Dict[str, Any]:
    if not path.exists():
        return default_state()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default_state()
    if not isinstance(payload, dict):
        return default_state()
    state = default_state()
    state.update(payload)
    if not isinstance(state.get("patterns"), list):
        state["patterns"] = []
    if not isinstance(state.get("history"), list):
        state["history"] = []
    if not isinstance(state.get("kpi_gates"), dict):
        state["kpi_gates"] = default_state()["kpi_gates"]
    if not isinstance(state.get("adaptive"), dict):
        state["adaptive"] = default_state()["adaptive"]
    if not isinstance(state.get("next_test_matrix"), list):
        state["next_test_matrix"] = []
    return state


def save_strategy_state(state: Dict[str, Any], path: Path = DEFAULT_STATE_PATH) -> Path:
    ensure_dir(path.parent)
    state["updated_at"] = _now_iso()
    write_json(path, state)
    return path


def _first_words(text: str, count: int = 8) -> str:
    words = [w for w in re.split(r"\s+", str(text or "").strip()) if w]
    return " ".join(words[:count]).strip()


def _topic_cluster(title: str, hashtags: Iterable[str]) -> str:
    tags = [str(t).strip().lower().lstrip("#") for t in hashtags if str(t).strip()]
    topical = [t for t in tags if t and t not in {"shorts", "fyp", "viral"}]
    if topical:
        return topical[0]
    tokens = [tok.lower() for tok in re.findall(r"[A-Za-zÄÖÜäöüß0-9]+", str(title or "")) if tok]
    stop = {"der", "die", "das", "und", "oder", "mit", "von", "für", "ein", "eine", "you", "your"}
    for token in tokens:
        if len(token) < 4 or token in stop:
            continue
        return token
    return "general"


def _pattern_key(topic_cluster: str, hook_template: str) -> str:
    return f"{topic_cluster}::{hook_template}".strip()


def _normalize_status(value: str) -> str:
    raw = str(value or "").strip().lower()
    if raw in {"active", "paused", "killed"}:
        return raw
    return "active"


def load_top_nuggets(limit: int = 8) -> List[Dict[str, Any]]:
    if not NUGGET_REGISTRY_PATH.exists():
        return []
    try:
        payload = json.loads(NUGGET_REGISTRY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    items = payload.get("items") if isinstance(payload, dict) else None
    if not isinstance(items, list):
        return []
    out: List[Dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if str(item.get("status") or "active") != "active":
            continue
        asset = str(item.get("asset_type") or "").lower()
        if asset not in ALLOWED_ASSET_TYPES:
            continue
        out.append(
            {
                "insight": str(item.get("insight") or "").strip(),
                "action": str(item.get("action") or "").strip(),
                "asset_type": asset,
                "priority_score": _safe_float(item.get("priority_score"), 0.0),
            }
        )
    out.sort(key=lambda x: x["priority_score"], reverse=True)
    return out[: max(0, limit)]


def build_strategy_prompt_context(state: Dict[str, Any], top_nuggets: List[Dict[str, Any]]) -> str:
    kpi = state.get("kpi_gates") if isinstance(state.get("kpi_gates"), dict) else {}
    adaptive = state.get("adaptive") if isinstance(state.get("adaptive"), dict) else {}
    target_vph = _safe_float(kpi.get("target_vph"), 120.0)
    min_like = _safe_float(kpi.get("min_like_rate"), 0.03)
    min_comment = _safe_float(kpi.get("min_comment_rate"), 0.005)

    low_streak = _safe_int(adaptive.get("low_vph_streak"), 0)
    hook_intensity = _safe_int(adaptive.get("hook_intensity"), 1)
    script_cap = _safe_int(adaptive.get("script_hook_setup_word_cap"), 120)
    force_new_angle = bool(adaptive.get("force_new_angle_cluster"))
    emotional_boost = bool(adaptive.get("emotional_framing_boost"))
    story_boost = _safe_int(adaptive.get("story_contrarian_boost_pct"), 0)
    cta_mode = str(adaptive.get("cta_mode") or "default")
    cta_binary_required = bool(adaptive.get("cta_binary_required"))

    lines: List[str] = []
    lines.append("SYSTEM_STRATEGY_CONTEXT:")
    lines.append("- Channel focus: DE AI-Automation.")
    lines.append("- Goal: humorvoll, interessant, spannend, am Zeitnerv.")
    lines.append("- Revenue lane: Product-first. CTA split target: 70% Produkt (Prompt Vault), 30% Community.")
    lines.append(f"- KPI gates: target_vph={target_vph}, min_like_rate={min_like}, min_comment_rate={min_comment}.")
    lines.append("- Keine unpruefbaren Einkommensversprechen als eigene Behauptung.")
    lines.append("- Must adapt from recent KPI feedback.")
    lines.append(
        f"- Adaptive controls: low_vph_streak={low_streak}, hook_intensity={hook_intensity}, "
        f"hook_setup_word_cap={script_cap}, force_new_angle_cluster={force_new_angle}."
    )
    if emotional_boost:
        lines.append(f"- Emotional framing boost active. Story/contrarian share +{story_boost}% this run.")
    if cta_mode == "binary_one_word" or cta_binary_required:
        lines.append("- CTA mode is binary one-word reply and is mandatory in every draft.")

    patterns = state.get("patterns")
    if isinstance(patterns, list) and patterns:
        active = [p for p in patterns if isinstance(p, dict) and str(p.get("status") or "active") == "active"]
        active.sort(key=lambda p: _safe_float(p.get("avg_vph"), 0.0), reverse=True)
        if active:
            lines.append("- Winning patterns (reuse structure, do not copy text):")
            for idx, item in enumerate(active[:5], start=1):
                lines.append(
                    f"  {idx}) topic_cluster={item.get('topic_cluster')} | hook_template={item.get('hook_template')} | avg_vph={item.get('avg_vph')}"
                )
            if force_new_angle:
                lines.append("- Enforce at least 2 new angle clusters not present in winning patterns.")

    if top_nuggets:
        lines.append("- Top nuggets to convert into scripts:")
        for idx, nugget in enumerate(top_nuggets, start=1):
            lines.append(
                f"  {idx}) [{nugget.get('asset_type')}] insight={nugget.get('insight')} | action={nugget.get('action')}"
            )
    return "\n".join(lines).strip()


def _find_pattern(state: Dict[str, Any], key: str) -> Dict[str, Any]:
    patterns = state.setdefault("patterns", [])
    if not isinstance(patterns, list):
        state["patterns"] = []
        patterns = state["patterns"]
    for item in patterns:
        if isinstance(item, dict) and str(item.get("key") or "") == key:
            return item
    entry = {
        "key": key,
        "topic_cluster": "",
        "hook_template": "",
        "win_count": 0,
        "fail_count": 0,
        "avg_vph": 0.0,
        "last_used_at": _now_iso(),
        "status": "active",
    }
    patterns.append(entry)
    return entry


def update_strategy_from_metrics(
    state: Dict[str, Any],
    *,
    run_id: str,
    target_vph: float,
    avg_vph: float,
    avg_like_rate: float,
    avg_comment_rate: float,
    drafts_payload: List[Dict[str, Any]],
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    changed: List[Dict[str, Any]] = []
    winners: List[Dict[str, Any]] = []
    killed: List[Dict[str, Any]] = []

    for draft in drafts_payload:
        title = str(draft.get("title") or "")
        hook = str(draft.get("hook") or "")
        hashtags = draft.get("hashtags") if isinstance(draft.get("hashtags"), list) else []
        cluster = _topic_cluster(title, hashtags)
        hook_template = _first_words(hook, 8)
        key = _pattern_key(cluster, hook_template)
        entry = _find_pattern(state, key)

        old_status = _normalize_status(str(entry.get("status") or "active"))
        entry["topic_cluster"] = cluster
        entry["hook_template"] = hook_template
        entry["last_used_at"] = _now_iso()

        wins = _safe_int(entry.get("win_count"), 0)
        fails = _safe_int(entry.get("fail_count"), 0)
        prev_avg = _safe_float(entry.get("avg_vph"), 0.0)
        if avg_vph >= target_vph:
            wins += 1
        else:
            fails += 1
        entry["win_count"] = wins
        entry["fail_count"] = fails
        entry["avg_vph"] = round((prev_avg * 0.7) + (avg_vph * 0.3), 2)

        new_status = old_status
        if fails >= 3 and wins == 0:
            new_status = "killed"
        elif fails >= 2 and wins >= 1:
            new_status = "paused"
        elif wins >= 2 and entry["avg_vph"] >= target_vph:
            new_status = "active"
        entry["status"] = new_status

        if new_status != old_status:
            changed.append(
                {
                    "pattern_key": key,
                    "from": old_status,
                    "to": new_status,
                    "avg_vph": entry["avg_vph"],
                    "win_count": wins,
                    "fail_count": fails,
                }
            )
        if new_status == "active" and wins >= 1:
            winners.append(
                {
                    "pattern_key": key,
                    "topic_cluster": cluster,
                    "hook_template": hook_template,
                    "avg_vph": entry["avg_vph"],
                }
            )
        if new_status == "killed":
            killed.append(
                {
                    "pattern_key": key,
                    "topic_cluster": cluster,
                    "hook_template": hook_template,
                    "avg_vph": entry["avg_vph"],
                }
            )

    kpi = state.setdefault("kpi_gates", {})
    if not isinstance(kpi, dict):
        kpi = {}
    kpi["target_vph"] = round(target_vph, 2)
    kpi["min_like_rate"] = 0.03
    kpi["min_comment_rate"] = 0.005
    state["kpi_gates"] = kpi

    adaptive = state.setdefault("adaptive", {})
    if not isinstance(adaptive, dict):
        adaptive = {}

    low_streak = _safe_int(adaptive.get("low_vph_streak"), 0)
    hook_intensity = _safe_int(adaptive.get("hook_intensity"), 1)
    script_cap = _safe_int(adaptive.get("script_hook_setup_word_cap"), 120)
    if avg_vph < target_vph:
        low_streak += 1
    else:
        low_streak = 0
        adaptive["force_new_angle_cluster"] = False

    if low_streak >= 2:
        new_hook_intensity = min(6, max(1, hook_intensity + 1))
        if new_hook_intensity != hook_intensity:
            changed.append(
                {
                    "adaptive_change": "hook_intensity_up",
                    "from": hook_intensity,
                    "to": new_hook_intensity,
                    "reason": "avg_vph_below_target_2_runs",
                }
            )
        hook_intensity = new_hook_intensity
        script_cap = 55
        adaptive["force_new_angle_cluster"] = True
        changed.append(
            {
                "adaptive_change": "script_shortening_enforced",
                "to_word_cap": 55,
                "reason": "avg_vph_below_target_2_runs",
            }
        )

    if avg_like_rate < 0.03:
        adaptive["emotional_framing_boost"] = True
        adaptive["story_contrarian_boost_pct"] = 20
        changed.append(
            {
                "adaptive_change": "emotional_framing_up",
                "story_contrarian_boost_pct": 20,
                "reason": "avg_like_rate_below_0.03",
            }
        )
    else:
        adaptive["emotional_framing_boost"] = False
        adaptive["story_contrarian_boost_pct"] = 0

    if avg_comment_rate < 0.005:
        adaptive["cta_mode"] = "binary_one_word"
        adaptive["cta_binary_required"] = True
        changed.append(
            {
                "adaptive_change": "cta_binary_mode_enabled",
                "reason": "avg_comment_rate_below_0.005",
            }
        )
    else:
        adaptive["cta_mode"] = "default"
        adaptive["cta_binary_required"] = False

    adaptive["low_vph_streak"] = low_streak
    adaptive["hook_intensity"] = hook_intensity
    adaptive["script_hook_setup_word_cap"] = script_cap
    state["adaptive"] = adaptive

    next_test_matrix = [
        {
            "test": "hook_pattern_interrupt",
            "enabled": low_streak >= 2,
            "target": "avg_vph",
        },
        {
            "test": "story_contrarian_mix_plus_20pct",
            "enabled": bool(adaptive.get("emotional_framing_boost")),
            "target": "like_rate",
        },
        {
            "test": "binary_one_word_cta",
            "enabled": bool(adaptive.get("cta_binary_required")),
            "target": "comment_rate",
        },
    ]
    state["next_test_matrix"] = next_test_matrix

    history = state.setdefault("history", [])
    if not isinstance(history, list):
        state["history"] = []
        history = state["history"]
    history.append(
        {
            "run_id": run_id,
            "timestamp": _now_iso(),
            "target_vph": round(target_vph, 2),
            "avg_vph": round(avg_vph, 2),
            "avg_like_rate": round(avg_like_rate, 4),
            "avg_comment_rate": round(avg_comment_rate, 4),
            "strategy_changes": changed,
            "winning_patterns": winners[:10],
            "killed_patterns": killed[:10],
            "next_test_matrix": next_test_matrix,
        }
    )
    state["history"] = history[-200:]
    return state, changed, winners[:10], killed[:10], next_test_matrix


def refresh_strategy_from_latest(
    path: Path = DEFAULT_STATE_PATH,
    *,
    target_vph_default: float = 120.0,
) -> Dict[str, Any]:
    """
    Refresh strategy state from latest workflow deliverables without creating new drafts.
    Useful for degrade mode when heavy render/upload tasks are paused.
    """
    state = load_strategy_state(path)
    updates: List[Dict[str, Any]] = []

    sources = [
        {
            "workflow": "shorts_revenue",
            "latest": ROOT / "content_factory" / "deliverables" / "shorts_revenue" / "latest.json",
            "metrics_file": "youtube_metrics.json",
        },
        {
            "workflow": "youtube_shorts",
            "latest": ROOT / "content_factory" / "deliverables" / "youtube_shorts" / "latest.json",
            "metrics_file": "metrics.json",
        },
    ]

    for src in sources:
        latest_path = src["latest"]
        if not latest_path.exists():
            continue
        try:
            latest_payload = json.loads(latest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        run_id = str(latest_payload.get("run_id") or "").strip()
        if not run_id:
            continue
        run_dir = latest_path.parent / run_id
        drafts_path = run_dir / "drafts.json"
        metrics_path = run_dir / str(src["metrics_file"])
        if not drafts_path.exists() or not metrics_path.exists():
            continue
        try:
            drafts_payload = json.loads(drafts_path.read_text(encoding="utf-8"))
            metrics_payload = json.loads(metrics_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue

        drafts = drafts_payload.get("items") if isinstance(drafts_payload, dict) else []
        summary = (metrics_payload.get("summary") if isinstance(metrics_payload, dict) else {}) or {}
        if not isinstance(drafts, list):
            drafts = []
        target_vph = _safe_float((state.get("kpi_gates") or {}).get("target_vph"), target_vph_default)

        state, changed, winners, killed, matrix = update_strategy_from_metrics(
            state,
            run_id=f"{run_id}:refresh",
            target_vph=target_vph,
            avg_vph=_safe_float(summary.get("avg_views_per_hour"), 0.0),
            avg_like_rate=_safe_float(summary.get("avg_like_rate"), 0.0),
            avg_comment_rate=_safe_float(summary.get("avg_comment_rate"), 0.0),
            drafts_payload=drafts,
        )
        updates.append(
            {
                "workflow": src["workflow"],
                "run_id": run_id,
                "strategy_changes": changed,
                "winning_patterns": winners,
                "killed_patterns": killed,
                "next_test_matrix": matrix,
            }
        )

    save_strategy_state(state, path=path)
    return {
        "updated_at": _now_iso(),
        "state_path": str(path),
        "updates": updates,
    }
