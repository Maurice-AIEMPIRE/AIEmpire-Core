#!/usr/bin/env python3
"""
Mission Control Example - Sample Usage

This script demonstrates how to use Mission Control programmatically
and integrate it with other systems.
"""

from mission_control_scanner import TaskScanner, MissionControl
import json


def example_basic_scan():
    """Example 1: Basic scan and display"""
    print("=" * 80)
    print("EXAMPLE 1: Basic Mission Control Scan")
    print("=" * 80)
    
    # Create scanner and run scan
    scanner = TaskScanner()
    scan_data = scanner.scan_all()
    
    # Create Mission Control dashboard
    mc = MissionControl(scan_data)
    
    # Display dashboard
    dashboard = mc.generate_dashboard()
    print(dashboard)
    
    # Display next 90 min action list
    print("\n")
    action_list = mc.generate_next_90_min()
    print(action_list)


def example_programmatic_access():
    """Example 2: Programmatic access to scan data"""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Programmatic Data Access")
    print("=" * 80)
    
    scanner = TaskScanner()
    scan_data = scanner.scan_all()
    
    # Access specific data
    print(f"\n📊 Statistics:")
    print(f"  Total Tasks: {scan_data['stats']['total_open']}")
    print(f"  By Category: {dict(scan_data['stats']['by_category'])}")
    print(f"  Blockers: {len(scan_data['stats']['blockers'])}")
    print(f"  High-Impact Tasks: {len(scan_data['stats']['levers'])}")
    print(f"  Cost Risks: {len(scan_data['stats']['cost_risks'])}")
    
    # Get top 3 priority tasks
    print(f"\n🎯 Top 3 Priority Tasks:")
    for i, task in enumerate(scan_data['tasks'][:3], 1):
        print(f"  {i}. [{task['category']:10s}] {task['title']}")
        print(f"     Impact: {task['impact']}/10 | Urgency: {task['urgency']}/10 | Priority Score: {task['priority_score']}")


def example_filtering_tasks():
    """Example 3: Filter tasks by criteria"""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Filter Tasks by Criteria")
    print("=" * 80)
    
    scanner = TaskScanner()
    scan_data = scanner.scan_all()
    
    # Filter high-impact tasks (impact >= 8)
    high_impact = [t for t in scan_data['tasks'] if t['impact'] >= 8]
    print(f"\n🚀 High-Impact Tasks (>= 8/10): {len(high_impact)}")
    for task in high_impact[:5]:
        print(f"  • [{task['source']:15s}] {task['title']}")
    
    # Filter by category
    build_tasks = [t for t in scan_data['tasks'] if t['category'] == 'BUILD']
    print(f"\n🔨 BUILD Tasks: {len(build_tasks)}")
    for task in build_tasks[:3]:
        print(f"  • {task['title']} (Priority: {task['priority_score']})")
    
    # Filter by source
    reactor_tasks = [t for t in scan_data['tasks'] if t['source'] == 'AtomicReactor']
    print(f"\n⚛️  Atomic Reactor Tasks: {len(reactor_tasks)}")
    for task in reactor_tasks[:3]:
        print(f"  • {task['title']}")


def example_export_integration():
    """Example 4: Export and integrate with other systems"""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Export for Knowledge Graph")
    print("=" * 80)
    
    scanner = TaskScanner()
    scan_data = scanner.scan_all()
    mc = MissionControl(scan_data)
    
    # Export to JSON
    json_file = mc.export_json()
    print(f"\n✅ Exported to: {json_file}")
    
    # Load and show structure
    with open(json_file) as f:
        data = json.load(f)
    
    print(f"\n📄 JSON Structure:")
    print(f"  Keys: {list(data.keys())}")
    print(f"  Summary: {data['summary']}")
    print(f"  Total Tasks in Export: {len(data['all_tasks'])}")


def example_custom_analysis():
    """Example 5: Custom analysis - Calculate team capacity"""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Custom Analysis - Team Capacity")
    print("=" * 80)
    
    scanner = TaskScanner()
    scan_data = scanner.scan_all()
    
    # Calculate total effort needed
    total_effort = sum(t['effort'] for t in scan_data['tasks'])
    
    # Average effort per task
    avg_effort = total_effort / len(scan_data['tasks']) if scan_data['tasks'] else 0
    
    print(f"\n📊 Team Capacity Analysis:")
    print(f"  Total Tasks: {len(scan_data['tasks'])}")
    print(f"  Total Effort Points: {total_effort}")
    print(f"  Average Effort/Task: {avg_effort:.1f}/10")
    
    # Estimate completion time (assuming 1 effort point = 1 hour)
    print(f"\n⏱️  Time Estimates:")
    print(f"  Total Hours Needed: ~{total_effort} hours")
    print(f"  With 1 person (8h/day): ~{total_effort/8:.1f} days")
    print(f"  With 2 people (16h/day): ~{total_effort/16:.1f} days")
    print(f"  With 5 people (40h/day): ~{total_effort/40:.1f} days")
    
    # Group by urgency
    urgent = len([t for t in scan_data['tasks'] if t['urgency'] >= 8])
    normal = len([t for t in scan_data['tasks'] if 5 <= t['urgency'] < 8])
    low = len([t for t in scan_data['tasks'] if t['urgency'] < 5])
    
    print(f"\n🔥 Urgency Distribution:")
    print(f"  Urgent (8-10):  {urgent:3d} tasks")
    print(f"  Normal (5-7):   {normal:3d} tasks")
    print(f"  Low (1-4):      {low:3d} tasks")


def example_brain_integration():
    """Example 6: Integration with Brain System"""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Brain System Integration")
    print("=" * 80)
    
    scanner = TaskScanner()
    scan_data = scanner.scan_all()
    
    # Simulate Prefrontal (CEO) Brain decision-making
    print("\n🧠 Prefrontal Brain Decision Making:")
    
    # Get top 3 tasks by priority
    top_tasks = scan_data['tasks'][:3]
    
    print("\n📋 RECOMMENDED SPRINT:")
    for i, task in enumerate(top_tasks, 1):
        print(f"\n  Sprint Item #{i}:")
        print(f"    Task: {task['title']}")
        print(f"    Reason: Impact={task['impact']}/10, Urgency={task['urgency']}/10")
        print(f"    Category: {task['category']}")
        print(f"    Source: {task['source']}")
    
    # Check blockers
    blockers = scan_data['stats']['blockers']
    if blockers:
        print(f"\n⚠️  ALERT: {len(blockers)} blockers detected!")
        print("   Resolve these before starting sprint:")
        for blocker in blockers[:3]:
            print(f"   • {blocker['task']}: {blocker['reason']}")
    
    # Cost analysis
    cost_risks = scan_data['stats']['cost_risks']
    if cost_risks:
        print(f"\n💰 COST ALERT: {len(cost_risks)} cost risks detected")
        total_compute = len([r for r in cost_risks if r['type'] == 'Compute'])
        total_token = len([r for r in cost_risks if r['type'] == 'Token'])
        print(f"   Compute risks: {total_compute}")
        print(f"   Token risks: {total_token}")


def main():
    """Run all examples"""
    examples = [
        ("Basic Scan", example_basic_scan),
        ("Programmatic Access", example_programmatic_access),
        ("Filtering Tasks", example_filtering_tasks),
        ("Export Integration", example_export_integration),
        ("Custom Analysis", example_custom_analysis),
        ("Brain Integration", example_brain_integration),
    ]
    
    print("\n🚀 MISSION CONTROL EXAMPLES\n")
    print("Available examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    print("\n" + "=" * 80)
    print("Running Example 2 (Programmatic Access) and Example 5 (Custom Analysis)")
    print("=" * 80)
    
    # Run selected examples
    example_programmatic_access()
    example_custom_analysis()
    
    print("\n\n✨ Examples complete!")
    print("\n💡 TIP: Uncomment other example calls in main() to see more use cases")


if __name__ == "__main__":
    main()
