#!/usr/bin/env python3
"""
Test script for Night Run 1000 - validates structure without API calls.
"""

import sys
import os
from pathlib import Path

# Set dummy API keys for import-time validation
os.environ["MOONSHOT_API_KEY"] = "test-key-for-validation"
os.environ["ANTHROPIC_API_KEY"] = "test-key-for-validation"

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


def test_task_config_imports():
    """Test that night_tasks_config imports correctly."""
    print("Testing night_tasks_config imports...")
    try:
        from night_tasks_config import TASK_CATEGORIES, TASK_VARIANTS, generate_task_list
        print("  ✅ All imports successful")
        return True
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        return False


def test_task_categories():
    """Test that all 20 categories are defined."""
    print("\nTesting task categories...")
    try:
        from night_tasks_config import TASK_CATEGORIES

        assert len(TASK_CATEGORIES) == 20, f"Expected 20 categories, got {len(TASK_CATEGORIES)}"
        print(f"  ✅ {len(TASK_CATEGORIES)} categories defined")

        for cat in TASK_CATEGORIES:
            assert "id" in cat, f"Category missing 'id'"
            assert "name" in cat, f"Category missing 'name'"
            assert "count" in cat, f"Category missing 'count'"
            assert "agent" in cat, f"Category missing 'agent'"
            assert "priority" in cat, f"Category missing 'priority'"
            assert "revenue_potential" in cat, f"Category missing 'revenue_potential'"
            assert "prompt" in cat, f"Category missing 'prompt'"
            assert cat["agent"] in ("kimi", "claude"), f"Invalid agent: {cat['agent']}"
            assert cat["count"] == 50, f"Expected 50 tasks per category, got {cat['count']}"

        print("  ✅ All categories have required fields")
        return True
    except Exception as e:
        print(f"  ❌ Category validation failed: {e}")
        return False


def test_generate_1000_tasks():
    """Test that exactly 1000 tasks are generated."""
    print("\nTesting task generation...")
    try:
        from night_tasks_config import generate_task_list

        tasks = generate_task_list()
        assert len(tasks) == 1000, f"Expected 1000 tasks, got {len(tasks)}"
        print(f"  ✅ {len(tasks)} tasks generated")

        # Check task structure
        for task in tasks[:5]:
            assert "task_id" in task
            assert "category_id" in task
            assert "category_name" in task
            assert "agent" in task
            assert "priority" in task
            assert "revenue_potential" in task
            assert "prompt" in task
            assert "variant" in task

        print("  ✅ Task structure valid")

        # Check distribution
        kimi_tasks = [t for t in tasks if t["agent"] == "kimi"]
        claude_tasks = [t for t in tasks if t["agent"] == "claude"]
        print(f"  ✅ Kimi tasks: {len(kimi_tasks)}")
        print(f"  ✅ Claude tasks: {len(claude_tasks)}")
        assert len(kimi_tasks) + len(claude_tasks) == 1000

        return True
    except Exception as e:
        print(f"  ❌ Task generation failed: {e}")
        return False


def test_task_id_uniqueness():
    """Test that all task IDs are unique."""
    print("\nTesting task ID uniqueness...")
    try:
        from night_tasks_config import generate_task_list

        tasks = generate_task_list()
        ids = [t["task_id"] for t in tasks]
        assert len(ids) == len(set(ids)), "Duplicate task IDs found!"
        print(f"  ✅ All {len(ids)} task IDs are unique")
        return True
    except Exception as e:
        print(f"  ❌ Uniqueness test failed: {e}")
        return False


def test_night_runner_imports():
    """Test that night_run_1000 imports correctly."""
    print("\nTesting night_run_1000 imports...")
    try:
        from night_run_1000 import NightRunner, KimiSwarmAgent, ClaudeAgentArmy
        print("  ✅ All imports successful")
        return True
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        return False


def test_night_runner_structure():
    """Test NightRunner class structure."""
    print("\nTesting NightRunner structure...")
    try:
        from night_run_1000 import NightRunner

        runner = NightRunner()
        assert hasattr(runner, "kimi"), "Missing kimi agent"
        assert hasattr(runner, "claude"), "Missing claude agent"
        assert hasattr(runner, "run"), "Missing run method"
        print("  ✅ NightRunner structure valid")
        return True
    except Exception as e:
        print(f"  ❌ Structure test failed: {e}")
        return False


def test_kimi_swarm_agent():
    """Test KimiSwarmAgent class."""
    print("\nTesting KimiSwarmAgent...")
    try:
        from night_run_1000 import KimiSwarmAgent

        agent = KimiSwarmAgent()
        assert hasattr(agent, "init_session")
        assert hasattr(agent, "close_session")
        assert hasattr(agent, "execute")
        assert agent.stats["completed"] == 0
        assert agent.stats["failed"] == 0
        assert agent.stats["cost_usd"] == 0.0
        print("  ✅ KimiSwarmAgent structure valid")
        return True
    except Exception as e:
        print(f"  ❌ KimiSwarmAgent test failed: {e}")
        return False


def test_claude_agent_army():
    """Test ClaudeAgentArmy class."""
    print("\nTesting ClaudeAgentArmy...")
    try:
        from night_run_1000 import ClaudeAgentArmy, CLAUDE_CONCURRENT

        army = ClaudeAgentArmy()
        assert hasattr(army, "init_session")
        assert hasattr(army, "close_session")
        assert hasattr(army, "execute")
        assert hasattr(army, "meta_review")
        assert army.stats["completed"] == 0
        assert CLAUDE_CONCURRENT == 100, f"Expected 100 Claude agents, got {CLAUDE_CONCURRENT}"
        print(f"  ✅ ClaudeAgentArmy with {CLAUDE_CONCURRENT} concurrent agents")
        return True
    except Exception as e:
        print(f"  ❌ ClaudeAgentArmy test failed: {e}")
        return False


def test_output_directories():
    """Test that output directories are created."""
    print("\nTesting output directories...")
    try:
        from night_run_1000 import OUTPUT_DIR, KIMI_OUTPUT, CLAUDE_OUTPUT, REPORTS_DIR, META_DIR

        dirs = [OUTPUT_DIR, KIMI_OUTPUT, CLAUDE_OUTPUT, REPORTS_DIR, META_DIR]
        for d in dirs:
            assert d.exists(), f"Directory not created: {d}"
            print(f"  ✅ {d.name}")

        print("  ✅ All output directories exist")
        return True
    except Exception as e:
        print(f"  ❌ Directory test failed: {e}")
        return False


def test_variant_coverage():
    """Test that task variants provide enough diversity."""
    print("\nTesting variant coverage...")
    try:
        from night_tasks_config import TASK_VARIANTS

        for key, variants in TASK_VARIANTS.items():
            assert len(variants) >= 50, f"{key} has only {len(variants)} variants (need ≥50)"
            print(f"  ✅ {key}: {len(variants)} variants")

        return True
    except Exception as e:
        print(f"  ❌ Variant test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("NIGHT RUN 1000 - VALIDATION TESTS")
    print("=" * 60)

    tests = [
        test_task_config_imports,
        test_task_categories,
        test_generate_1000_tasks,
        test_task_id_uniqueness,
        test_night_runner_imports,
        test_night_runner_structure,
        test_kimi_swarm_agent,
        test_claude_agent_army,
        test_output_directories,
        test_variant_coverage,
    ]

    results = []
    for test in tests:
        results.append(test())

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("✅ All tests passed! Night Run ready.")
        return 0
    else:
        print(f"❌ {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
