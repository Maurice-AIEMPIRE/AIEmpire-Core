#!/usr/bin/env python3
"""
Tests for Mission Control system.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent))

from mission_control import (
    MissionControl,
    Task,
    TaskCategory,
    Priority,
)


def test_task_priority_score():
    """Test that priority_score computes correctly."""
    task = Task(
        id="test-1",
        title="Test Task",
        source="test",
        category=TaskCategory.BUILD,
        priority=Priority.HIGH,
        impact=8,
        urgency=7,
        effort=3,
    )
    # (10-8)*100 + (10-7)*10 + 3 = 200 + 30 + 3 = 233
    assert task.priority_score == 233, f"Expected 233, got {task.priority_score}"
    print("PASS: test_task_priority_score")


def test_task_priority_score_extreme():
    """Test priority score with extreme values."""
    # Maximum priority (impact=10, urgency=10, effort=1)
    task_max = Task(
        id="max",
        title="Max Priority",
        source="test",
        category=TaskCategory.FIX,
        priority=Priority.CRITICAL,
        impact=10,
        urgency=10,
        effort=1,
    )
    # (10-10)*100 + (10-10)*10 + 1 = 0 + 0 + 1 = 1
    assert task_max.priority_score == 1, f"Expected 1, got {task_max.priority_score}"

    # Minimum priority (impact=1, urgency=1, effort=10)
    task_min = Task(
        id="min",
        title="Min Priority",
        source="test",
        category=TaskCategory.STRATEGY,
        priority=Priority.LOW,
        impact=1,
        urgency=1,
        effort=10,
    )
    # (10-1)*100 + (10-1)*10 + 10 = 900 + 90 + 10 = 1000
    assert task_min.priority_score == 1000, f"Expected 1000, got {task_min.priority_score}"

    # Max priority should sort before min priority
    assert task_max.priority_score < task_min.priority_score
    print("PASS: test_task_priority_score_extreme")


def test_prioritize_tasks():
    """Test task prioritization sorting."""
    mc = MissionControl(repo_path="/tmp/test-repo")

    tasks = [
        Task(id="low", title="Low", source="test", category=TaskCategory.BUILD,
             priority=Priority.LOW, impact=2, urgency=2, effort=8),
        Task(id="high", title="High", source="test", category=TaskCategory.FIX,
             priority=Priority.CRITICAL, impact=9, urgency=9, effort=2),
        Task(id="mid", title="Mid", source="test", category=TaskCategory.CONTENT,
             priority=Priority.MEDIUM, impact=5, urgency=5, effort=5),
    ]

    sorted_tasks = mc.prioritize_tasks(tasks)
    assert sorted_tasks[0].id == "high", f"Expected 'high' first, got '{sorted_tasks[0].id}'"
    assert sorted_tasks[-1].id == "low", f"Expected 'low' last, got '{sorted_tasks[-1].id}'"
    print("PASS: test_prioritize_tasks")


def test_get_top_blockers():
    """Test blocker filtering."""
    mc = MissionControl(repo_path="/tmp/test-repo")
    mc.tasks = [
        Task(id="b1", title="Blocker 1", source="test", category=TaskCategory.FIX,
             priority=Priority.CRITICAL, blocker=True, blocker_reason="Broken"),
        Task(id="n1", title="Normal 1", source="test", category=TaskCategory.BUILD,
             priority=Priority.MEDIUM),
        Task(id="b2", title="Blocker 2", source="test", category=TaskCategory.FIX,
             priority=Priority.HIGH, blocker=True, blocker_reason="Down"),
    ]

    blockers = mc.get_top_blockers()
    assert len(blockers) == 2, f"Expected 2 blockers, got {len(blockers)}"
    assert all(t.blocker for t in blockers)
    print("PASS: test_get_top_blockers")


def test_get_top_levers():
    """Test lever calculation (high impact, low effort)."""
    mc = MissionControl(repo_path="/tmp/test-repo")
    mc.tasks = [
        Task(id="lever", title="Easy Win", source="test", category=TaskCategory.AUTOMATE,
             priority=Priority.MEDIUM, impact=9, effort=2),
        Task(id="hard", title="Hard Task", source="test", category=TaskCategory.BUILD,
             priority=Priority.MEDIUM, impact=3, effort=9),
    ]

    levers = mc.get_top_levers(limit=5)
    assert levers[0].id == "lever", f"Expected 'lever' first, got '{levers[0].id}'"
    print("PASS: test_get_top_levers")


def test_get_by_category():
    """Test category filtering."""
    mc = MissionControl(repo_path="/tmp/test-repo")
    mc.tasks = [
        Task(id="fix1", title="Fix 1", source="test", category=TaskCategory.FIX,
             priority=Priority.HIGH),
        Task(id="build1", title="Build 1", source="test", category=TaskCategory.BUILD,
             priority=Priority.MEDIUM),
        Task(id="fix2", title="Fix 2", source="test", category=TaskCategory.FIX,
             priority=Priority.LOW),
    ]

    fixes = mc.get_by_category(TaskCategory.FIX)
    assert len(fixes) == 2, f"Expected 2 FIX tasks, got {len(fixes)}"

    builds = mc.get_by_category(TaskCategory.BUILD)
    assert len(builds) == 1, f"Expected 1 BUILD task, got {len(builds)}"

    content = mc.get_by_category(TaskCategory.CONTENT)
    assert len(content) == 0, f"Expected 0 CONTENT tasks, got {len(content)}"
    print("PASS: test_get_by_category")


def test_generate_dashboard():
    """Test dashboard generation with manual tasks."""
    mc = MissionControl(repo_path="/tmp/test-repo")
    mc.tasks = [
        Task(id="t1", title="Fix CI pipeline", source="workflow-runs",
             category=TaskCategory.FIX, priority=Priority.CRITICAL,
             impact=9, urgency=9, effort=3, blocker=True,
             blocker_reason="CI is broken"),
        Task(id="t2", title="Create landing page", source="github-issues",
             category=TaskCategory.BUILD, priority=Priority.HIGH,
             impact=8, urgency=6, effort=5),
        Task(id="t3", title="Write blog post", source="atomic-reactor",
             category=TaskCategory.CONTENT, priority=Priority.MEDIUM,
             impact=5, urgency=4, effort=3),
    ]
    mc.scan_results = {
        "github_issues": {"count": 1},
        "workflow_runs": {"count": 1},
        "task_files": {"count": 1},
    }

    dashboard = mc.generate_dashboard()

    assert "MISSION CONTROL DASHBOARD" in dashboard
    assert "Fix CI pipeline" in dashboard
    assert "Create landing page" in dashboard
    assert "Top 10 Blockers" in dashboard
    assert "Top 10 Levers" in dashboard
    assert "90-Minute Action List" in dashboard
    print("PASS: test_generate_dashboard")


def test_generate_action_list():
    """Test action list generation."""
    mc = MissionControl(repo_path="/tmp/test-repo")
    mc.tasks = [
        Task(id="a1", title="Deploy hotfix", source="test",
             category=TaskCategory.FIX, priority=Priority.CRITICAL,
             impact=10, urgency=10, effort=2, blocker=True),
        Task(id="a2", title="Setup monitoring", source="test",
             category=TaskCategory.AUTOMATE, priority=Priority.HIGH,
             impact=7, urgency=5, effort=4),
    ]

    action_list = mc.generate_action_list()
    assert "[FIX]" in action_list
    assert "[AUTO]" in action_list
    assert "Deploy hotfix" in action_list
    assert "BLOCKER" in action_list
    print("PASS: test_generate_action_list")


def test_export_to_json():
    """Test JSON export."""
    mc = MissionControl(repo_path="/tmp/test-repo")
    mc.tasks = [
        Task(id="j1", title="JSON Test", source="test",
             category=TaskCategory.BUILD, priority=Priority.MEDIUM,
             impact=5, urgency=5, effort=5),
    ]
    mc.scan_results = {"test_source": {"count": 1}}

    data = mc.export_to_json()

    assert "scan_time" in data
    assert data["total_tasks"] == 1
    assert len(data["tasks"]) == 1
    assert data["tasks"][0]["id"] == "j1"
    assert data["tasks"][0]["category"] == "build"
    assert data["tasks"][0]["priority"] == "medium"
    assert "summary" in data

    # Verify it's JSON serializable
    json_str = json.dumps(data)
    assert len(json_str) > 0
    print("PASS: test_export_to_json")


def test_category_mapping():
    """Test internal category mapping."""
    mc = MissionControl(repo_path="/tmp/test-repo")

    assert mc._map_category("build") == TaskCategory.BUILD
    assert mc._map_category("fix") == TaskCategory.FIX
    assert mc._map_category("automate") == TaskCategory.AUTOMATE
    assert mc._map_category("content") == TaskCategory.CONTENT
    assert mc._map_category("strategy") == TaskCategory.STRATEGY
    assert mc._map_category("unknown") == TaskCategory.BUILD  # default
    print("PASS: test_category_mapping")


def test_priority_mapping():
    """Test internal priority mapping."""
    mc = MissionControl(repo_path="/tmp/test-repo")

    assert mc._map_priority("critical") == Priority.CRITICAL
    assert mc._map_priority("high") == Priority.HIGH
    assert mc._map_priority("medium") == Priority.MEDIUM
    assert mc._map_priority("low") == Priority.LOW
    assert mc._map_priority("unknown") == Priority.MEDIUM  # default
    print("PASS: test_priority_mapping")


def test_label_categorization():
    """Test label-based categorization."""
    mc = MissionControl(repo_path="/tmp/test-repo")

    assert mc._categorize_by_labels(["bug", "urgent"]) == TaskCategory.FIX
    assert mc._categorize_by_labels(["automation", "ci"]) == TaskCategory.AUTOMATE
    assert mc._categorize_by_labels(["content", "marketing"]) == TaskCategory.CONTENT
    assert mc._categorize_by_labels(["strategy", "revenue"]) == TaskCategory.STRATEGY
    assert mc._categorize_by_labels(["feature"]) == TaskCategory.BUILD  # default
    print("PASS: test_label_categorization")


def test_label_priority():
    """Test label-based priority."""
    mc = MissionControl(repo_path="/tmp/test-repo")

    assert mc._priority_by_labels(["critical", "p0"]) == Priority.CRITICAL
    assert mc._priority_by_labels(["high", "important"]) == Priority.HIGH
    assert mc._priority_by_labels(["low", "minor"]) == Priority.LOW
    assert mc._priority_by_labels(["enhancement"]) == Priority.MEDIUM  # default
    print("PASS: test_label_priority")


async def test_real_scan():
    """Run a real scan (may produce 0 results in test env)."""
    mc = MissionControl(repo_path=str(Path(__file__).parent))
    tasks = await mc.scan_all_sources()

    print(f"Real scan found {len(tasks)} tasks")
    print(f"Scan results: {mc.scan_results}")

    # Dashboard should always generate without error
    dashboard = mc.generate_dashboard()
    assert "MISSION CONTROL DASHBOARD" in dashboard

    # JSON export should always work
    data = mc.export_to_json()
    json_str = json.dumps(data)
    assert len(json_str) > 0

    print("PASS: test_real_scan")


def main():
    """Run all tests."""
    print("=" * 60)
    print("MISSION CONTROL - Test Suite")
    print("=" * 60)
    print()

    # Unit tests
    test_task_priority_score()
    test_task_priority_score_extreme()
    test_prioritize_tasks()
    test_get_top_blockers()
    test_get_top_levers()
    test_get_by_category()
    test_generate_dashboard()
    test_generate_action_list()
    test_export_to_json()
    test_category_mapping()
    test_priority_mapping()
    test_label_categorization()
    test_label_priority()

    # Integration test
    asyncio.run(test_real_scan())

    print()
    print("=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
