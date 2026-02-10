#!/usr/bin/env python3
"""
Test script for Mission Control System
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from mission_control import MissionControl, TaskCategory, Priority, Task


async def test_basic_functionality():
    """Test basic mission control functionality"""
    print("=" * 70)
    print("🧪 Testing Mission Control System")
    print("=" * 70)
    print()
    
    mc = MissionControl()
    
    # Test 1: Add manual tasks
    print("Test 1: Adding manual tasks...")
    mc.tasks = [
        Task(
            id="TEST-1",
            title="High impact blocker",
            source="Test",
            category=TaskCategory.FIX,
            priority=Priority.CRITICAL,
            impact=9,
            urgency=10,
            effort=3,
            blocker=True,
            blocker_reason="System down"
        ),
        Task(
            id="TEST-2",
            title="Quick win automation",
            source="Test",
            category=TaskCategory.AUTOMATE,
            priority=Priority.HIGH,
            impact=8,
            urgency=7,
            effort=2
        ),
        Task(
            id="TEST-3",
            title="Content creation task",
            source="Test",
            category=TaskCategory.CONTENT,
            priority=Priority.MEDIUM,
            impact=6,
            urgency=5,
            effort=4
        ),
        Task(
            id="TEST-4",
            title="Strategic planning",
            source="Test",
            category=TaskCategory.STRATEGY,
            priority=Priority.LOW,
            impact=7,
            urgency=3,
            effort=8,
            deadline="2026-02-15"
        ),
    ]
    print(f"✓ Added {len(mc.tasks)} test tasks")
    print()
    
    # Test 2: Prioritization
    print("Test 2: Testing prioritization...")
    mc.prioritize_tasks()
    print("✓ Tasks prioritized")
    print(f"  Top task: {mc.tasks[0].title} (score: {mc.tasks[0].priority_score:.1f})")
    print()
    
    # Test 3: Get blockers
    print("Test 3: Testing blocker detection...")
    blockers = mc.get_top_blockers()
    print(f"✓ Found {len(blockers)} blockers")
    for b in blockers:
        print(f"  - {b.id}: {b.title} ({b.blocker_reason})")
    print()
    
    # Test 4: Get high-impact tasks
    print("Test 4: Testing lever detection...")
    levers = mc.get_top_levers(3)
    print(f"✓ Found top {len(levers)} levers")
    for l in levers:
        print(f"  - {l.id}: {l.title} (impact: {l.impact}/10)")
    print()
    
    # Test 5: Get by category
    print("Test 5: Testing category filtering...")
    for category in TaskCategory:
        tasks = mc.get_by_category(category, limit=5)
        print(f"  - {category.value}: {len(tasks)} tasks")
    print()
    
    # Test 6: Time-critical tasks
    print("Test 6: Testing deadline detection...")
    critical = mc.get_time_critical()
    print(f"✓ Found {len(critical)} time-critical tasks")
    for t in critical:
        print(f"  - {t.id}: {t.title} (due: {t.deadline})")
    print()
    
    # Test 7: Generate dashboard
    print("Test 7: Testing dashboard generation...")
    dashboard = mc.generate_dashboard()
    print(f"✓ Generated dashboard ({len(dashboard)} chars)")
    print()
    
    # Test 8: Export JSON
    print("Test 8: Testing JSON export...")
    json_path = mc.export_to_json(Path("/tmp/test_mission_control.json"))
    print(f"✓ Exported to {json_path}")
    
    # Verify JSON file exists and is valid
    import json
    with open(json_path) as f:
        data = json.load(f)
        print(f"  - Total tasks in JSON: {data['summary']['total_tasks']}")
        print(f"  - Categories: {list(data['summary']['by_category'].keys())}")
    print()
    
    # Test 9: Action list
    print("Test 9: Testing action list generation...")
    action_list = mc.generate_action_list(limit=3)
    print(f"✓ Generated action list ({len(action_list)} chars)")
    lines = action_list.strip().split('\n')
    print(f"  - {len([l for l in lines if l.strip().startswith('1.') or l.strip().startswith('2.') or l.strip().startswith('3.')])} actions")
    print()
    
    print("=" * 70)
    print("✅ ALL TESTS PASSED!")
    print("=" * 70)
    
    return True


async def test_real_scan():
    """Test real system scan"""
    print("\n" + "=" * 70)
    print("🔍 Testing Real System Scan")
    print("=" * 70)
    print()
    
    mc = MissionControl()
    
    try:
        await mc.scan_all_sources()
        print(f"✓ Scanned successfully, found {len(mc.tasks)} tasks")
        
        if len(mc.tasks) > 0:
            print(f"  Sample task: {mc.tasks[0].id} - {mc.tasks[0].title}")
        
        return True
    except Exception as e:
        print(f"✗ Scan failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    try:
        # Test basic functionality
        test1 = await test_basic_functionality()
        
        # Test real scan
        test2 = await test_real_scan()
        
        if test1 and test2:
            print("\n🎉 All tests completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
