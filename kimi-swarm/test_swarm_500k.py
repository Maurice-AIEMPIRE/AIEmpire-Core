#!/usr/bin/env python3
"""
Test script for 500K Swarm - validates structure without API calls
"""

import sys
import json
import os
from pathlib import Path

# Set dummy API key for testing (won't actually be used)
os.environ["MOONSHOT_API_KEY"] = "test-key-for-validation"

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all imports work."""
    print("Testing imports...")
    try:
        import asyncio
        import aiohttp
        import json
        import os
        import time
        from datetime import datetime
        from pathlib import Path
        from typing import List, Dict, Optional
        import random
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_task_types():
    """Test that task types are properly defined."""
    print("\nTesting task types...")
    try:
        # Import from swarm_500k
        import swarm_500k
        
        task_types = swarm_500k.TASK_TYPES
        print(f"  Found {len(task_types)} task types:")
        
        for task_type in task_types:
            assert "type" in task_type, f"Task missing 'type' field"
            assert "output_dir" in task_type, f"Task missing 'output_dir' field"
            assert "priority" in task_type, f"Task missing 'priority' field"
            assert "revenue_potential" in task_type, f"Task missing 'revenue_potential' field"
            assert "prompt" in task_type, f"Task missing 'prompt' field"
            print(f"    ✅ {task_type['type']} (Priority: {task_type['priority']}, Revenue: €{task_type['revenue_potential']})")
        
        print("✅ All task types valid")
        return True
    except Exception as e:
        print(f"❌ Task type validation failed: {e}")
        return False

def test_claude_orchestrator():
    """Test Claude orchestrator structure."""
    print("\nTesting Claude orchestrator...")
    try:
        import swarm_500k
        
        # Test orchestrator initialization
        orchestrator = swarm_500k.ClaudeOrchestrator("")
        print("  ✅ ClaudeOrchestrator initialized")
        
        # Test that it has required methods
        assert hasattr(orchestrator, "analyze_swarm_progress"), "Missing analyze_swarm_progress method"
        print("  ✅ analyze_swarm_progress method exists")
        
        print("✅ Claude orchestrator structure valid")
        return True
    except Exception as e:
        print(f"❌ Claude orchestrator test failed: {e}")
        return False

def test_swarm_structure():
    """Test swarm class structure."""
    print("\nTesting swarm structure...")
    try:
        import swarm_500k
        
        # Test swarm initialization
        swarm = swarm_500k.KimiSwarm500K()
        print("  ✅ KimiSwarm500K initialized")
        
        # Test required methods
        methods = [
            "init_session",
            "close_session",
            "save_result",
            "execute_task",
            "select_task_type",
            "run_batch",
            "claude_orchestration_checkpoint",
            "print_stats",
            "run_swarm"
        ]
        
        for method in methods:
            assert hasattr(swarm, method), f"Missing {method} method"
        print(f"  ✅ All {len(methods)} required methods exist")
        
        # Test stats structure
        expected_stats_keys = [
            "total_tasks", "completed", "failed", "tokens_used",
            "cost_usd", "start_time", "results", "by_type",
            "estimated_revenue", "claude_orchestrations"
        ]
        for key in expected_stats_keys:
            assert key in swarm.stats, f"Missing stats key: {key}"
        print(f"  ✅ Stats structure valid ({len(expected_stats_keys)} keys)")
        
        print("✅ Swarm structure valid")
        return True
    except Exception as e:
        print(f"❌ Swarm structure test failed: {e}")
        return False

def test_output_directories():
    """Test that output directory structure is defined."""
    print("\nTesting output directory structure...")
    try:
        import swarm_500k
        
        required_dirs = [
            "OUTPUT_DIR", "LEADS_DIR", "CONTENT_DIR",
            "COMPETITORS_DIR", "NUGGETS_DIR", "REVENUE_OPS_DIR",
            "CLAUDE_INSIGHTS_DIR"
        ]
        
        for dir_name in required_dirs:
            assert hasattr(swarm_500k, dir_name), f"Missing directory constant: {dir_name}"
            dir_path = getattr(swarm_500k, dir_name)
            print(f"  ✅ {dir_name}: {dir_path}")
        
        print("✅ Output directory structure valid")
        return True
    except Exception as e:
        print(f"❌ Output directory test failed: {e}")
        return False

def test_configuration():
    """Test configuration values."""
    print("\nTesting configuration...")
    try:
        import swarm_500k
        
        config_checks = [
            ("MAX_CONCURRENT", 500, "Concurrency level"),
            ("TOTAL_AGENTS", 500000, "Total agents capacity"),
            ("BUDGET_USD", 75.0, "Budget limit"),
            ("CLAUDE_ORCHESTRATION_INTERVAL", 1000, "Claude check interval"),
        ]
        
        for var_name, expected_value, description in config_checks:
            actual_value = getattr(swarm_500k, var_name)
            assert actual_value == expected_value, f"{var_name} mismatch: expected {expected_value}, got {actual_value}"
            print(f"  ✅ {description}: {actual_value}")
        
        print("✅ Configuration valid")
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("="*60)
    print("500K KIMI SWARM - VALIDATION TESTS")
    print("="*60)
    
    tests = [
        test_imports,
        test_task_types,
        test_claude_orchestrator,
        test_swarm_structure,
        test_output_directories,
        test_configuration,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed! System ready to run.")
        return 0
    else:
        print(f"❌ {total - passed} test(s) failed. Please fix issues before running.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
