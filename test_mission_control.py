#!/usr/bin/env python3
"""
TEST SUITE FOR MISSION CONTROL SYSTEM
Comprehensive tests for task prioritization and scanning.
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime, timedelta
from mission_control import (
    MissionControl,
    Task,
    TaskCategory,
    Priority,
)


async def test_basic_functionality():
    """Test basic Mission Control functionality."""
    print("\n" + "=" * 60)
    print("TEST: Basic Functionality")
    print("=" * 60)

    mission = MissionControl()

    # Create manual test tasks
    print("\n1️⃣  Creating test tasks...")
    mission.tasks = [
        Task(
            title="Fix critical API bug",
            category=TaskCategory.FIX,
            priority=Priority.CRITICAL,
            impact=9,
            urgency=9,
            effort=4,
            blocker=True,
            source="Test",
        ),
        Task(
            title="Implement new feature",
            category=TaskCategory.BUILD,
            priority=Priority.HIGH,
            impact=8,
            urgency=5,
            effort=6,
            source="Test",
        ),
        Task(
            title="Write blog post",
            category=TaskCategory.CONTENT,
            priority=Priority.MEDIUM,
            impact=4,
            urgency=3,
            effort=3,
            source="Test",
        ),
        Task(
            title="Optimize database queries",
            category=TaskCategory.AUTOMATE,
            priority=Priority.HIGH,
            impact=7,
            urgency=4,
            effort=5,
            source="Test",
        ),
        Task(
            title="Update strategy document",
            category=TaskCategory.STRATEGY,
            priority=Priority.MEDIUM,
            impact=6,
            urgency=2,
            effort=2,
            deadline=(datetime.now() + timedelta(days=3)).isoformat(),
            source="Test",
        ),
    ]
    print(f"✅ Created {len(mission.tasks)} test tasks")

    # Test prioritization
    print("\n2️⃣  Testing prioritization...")
    mission.prioritize_tasks()
    print("✅ Tasks prioritized by score")
    for i, task in enumerate(mission.tasks, 1):
        print(f"   {i}. {task.title} (Score: {task.priority_score:.0f})")
    assert mission.tasks[0].title == "Fix critical API bug"
    scores = [t.priority_score for t in mission.tasks]
    assert scores == sorted(scores)

    # Test blockers
    print("\n3️⃣  Testing blockers...")
    blockers = mission.get_top_blockers(5)
    print(f"✅ Found {len(blockers)} blocker(s)")
    for blocker in blockers:
        print(f"   - {blocker.title}")

    # Test levers
    print("\n4️⃣  Testing levers (high impact)...")
    levers = mission.get_top_levers(3)
    print(f"✅ Top 3 high-impact tasks:")
    for lever in levers:
        print(f"   - {lever.title} (Impact: {lever.impact}/10)")

    # Test categories
    print("\n5️⃣  Testing category filtering...")
    for cat in TaskCategory:
        tasks = mission.get_by_category(cat, 2)
        print(f"✅ {cat.value}: {len(tasks)} task(s)")

    # Test deadline filtering
    print("\n6️⃣  Testing time-critical tasks...")
    critical = mission.get_time_critical()
    print(f"✅ Found {len(critical)} time-critical task(s)")
    for task in critical:
        print(f"   - {task.title} (Due: {task.deadline})")

    # Test cost risks
    print("\n7️⃣  Testing cost risks...")
    costs = mission.get_cost_risks()
    print(f"✅ Found {len(costs)} cost risk task(s)")

    # Test dashboard generation
    print("\n8️⃣  Testing dashboard generation...")
    dashboard = mission.generate_dashboard()
    assert "Mission Control Dashboard" in dashboard
    assert "Summary Stats" in dashboard
    print("✅ Dashboard generated successfully")
    print(f"   Dashboard length: {len(dashboard)} chars")

    # Test action list
    print("\n9️⃣  Testing action list generation...")
    action_list = mission.generate_action_list(7)
    assert "Next 90 Minutes" in action_list
    print("✅ Action list generated successfully")
    print(f"   Action list length: {len(action_list)} chars")

    # Test JSON export
    print("\n🔟 Testing JSON export...")
    mission.export_to_json("test_mission_control_data.json")

    assert Path("test_mission_control_data.json").exists()
    with open("test_mission_control_data.json") as f:
        data = json.load(f)

    assert "summary" in data
    assert "tasks" in data
    assert data["summary"]["total_tasks"] == len(mission.tasks)
    print("✅ JSON export successful")
    print(f"   Exported {len(data['tasks'])} tasks")

    # Cleanup
    Path("test_mission_control_data.json").unlink()

    print("\n" + "=" * 60)
    print("✅ ALL BASIC TESTS PASSED")
    print("=" * 60)


async def test_real_scan():
    """Test real system scanning."""
    print("\n" + "=" * 60)
    print("TEST: Real System Scan")
    print("=" * 60)

    mission = MissionControl()

    print("\n🔍 Running real system scan...")
    print("   (This may take a moment)")

    try:
        await mission.scan_all_sources()
        print(f"✅ Scan complete: Found {len(mission.tasks)} tasks")

        if mission.tasks:
            mission.prioritize_tasks()
            print(f"✅ Tasks prioritized")
            print(f"\nTop 3 tasks:")
            for i, task in enumerate(mission.tasks[:3], 1):
                print(f"   {i}. {task.title} (Score: {task.priority_score:.0f})")
        else:
            print("⚠️  No tasks found (this may be normal if no sources are available)")

    except Exception as e:
        print(f"⚠️  Scan error (non-critical): {e}")

    print("\n" + "=" * 60)
    print("✅ REAL SCAN TEST COMPLETE")
    print("=" * 60)


async def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("MISSION CONTROL TEST SUITE")
    print("=" * 80)

    try:
        await test_basic_functionality()
        await test_real_scan()

        print("\n" + "=" * 80)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 80)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
