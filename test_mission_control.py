#!/usr/bin/env python3
"""
TEST SUITE - Mission Control System
Tests all scanning, prioritization, and reporting functions.
Maurice's AI Empire - 2026
"""

import asyncio
import json
import os
import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure the project root is on the path
sys.path.insert(0, str(Path(__file__).parent))

from mission_control import (
    MissionControl,
    Task,
    TaskCategory,
    Priority,
)


class TestTask(unittest.TestCase):
    """Test the Task dataclass"""

    def test_task_creation(self):
        """Test basic task creation"""
        task = Task(
            id="TEST-001",
            title="Test task",
            source="Unit Test",
            category=TaskCategory.BUILD,
            priority=Priority.HIGH,
            impact=8,
            urgency=7,
            effort=3,
        )
        self.assertEqual(task.id, "TEST-001")
        self.assertEqual(task.title, "Test task")
        self.assertEqual(task.category, TaskCategory.BUILD)
        self.assertEqual(task.priority, Priority.HIGH)
        self.assertFalse(task.blocker)

    def test_task_priority_score(self):
        """Test priority score calculation: lower is higher priority"""
        high_impact = Task(
            id="T1", title="High impact", source="test",
            category=TaskCategory.BUILD, priority=Priority.HIGH,
            impact=10, urgency=10, effort=1,
        )
        low_impact = Task(
            id="T2", title="Low impact", source="test",
            category=TaskCategory.BUILD, priority=Priority.LOW,
            impact=1, urgency=1, effort=10,
        )
        # Higher impact + urgency = lower priority_score
        self.assertLess(high_impact.priority_score, low_impact.priority_score)

    def test_task_priority_score_impact_dominates(self):
        """Impact should dominate over urgency in priority score"""
        high_impact_low_urgency = Task(
            id="T1", title="High impact", source="test",
            category=TaskCategory.BUILD, priority=Priority.HIGH,
            impact=10, urgency=1, effort=5,
        )
        low_impact_high_urgency = Task(
            id="T2", title="High urgency", source="test",
            category=TaskCategory.BUILD, priority=Priority.HIGH,
            impact=5, urgency=10, effort=5,
        )
        self.assertLess(
            high_impact_low_urgency.priority_score,
            low_impact_high_urgency.priority_score,
        )

    def test_task_blocker(self):
        """Test blocker task attributes"""
        task = Task(
            id="T-BLOCKER",
            title="Blocking issue",
            source="test",
            category=TaskCategory.FIX,
            priority=Priority.CRITICAL,
            impact=10,
            urgency=10,
            effort=2,
            blocker=True,
            blocker_reason="Critical system failure",
        )
        self.assertTrue(task.blocker)
        self.assertEqual(task.blocker_reason, "Critical system failure")

    def test_task_optional_fields(self):
        """Test optional field defaults"""
        task = Task(
            id="T-MIN",
            title="Minimal",
            source="test",
            category=TaskCategory.BUILD,
            priority=Priority.LOW,
            impact=1,
            urgency=1,
            effort=1,
        )
        self.assertIsNone(task.deadline)
        self.assertIsNone(task.blocker_reason)
        self.assertIsNone(task.cost_risk)
        self.assertIsNone(task.description)


class TestTaskCategory(unittest.TestCase):
    """Test TaskCategory enum"""

    def test_all_categories_exist(self):
        """All expected categories should exist"""
        expected = ["BUILD", "FIX", "AUTOMATE", "CONTENT", "STRATEGY"]
        for cat in expected:
            self.assertIn(cat, [c.value for c in TaskCategory])

    def test_category_values(self):
        """Category values should be uppercase strings"""
        for cat in TaskCategory:
            self.assertEqual(cat.value, cat.value.upper())


class TestPriority(unittest.TestCase):
    """Test Priority enum"""

    def test_all_priorities_exist(self):
        """All expected priorities should exist"""
        expected = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        for pri in expected:
            self.assertIn(pri, [p.name for p in Priority])

    def test_priority_ordering(self):
        """CRITICAL should have lower value than LOW"""
        self.assertLess(Priority.CRITICAL.value, Priority.LOW.value)


class TestMissionControl(unittest.TestCase):
    """Test the MissionControl class"""

    def setUp(self):
        """Set up test fixtures"""
        self.mc = MissionControl(repo_path=str(Path(__file__).parent))

    def test_initialization(self):
        """Test MissionControl initialization"""
        self.assertIsNotNone(self.mc)
        self.assertEqual(self.mc.tasks, [])
        self.assertIsInstance(self.mc.repo_path, Path)

    def test_categorize_from_labels_bug(self):
        """Test label categorization for bugs"""
        result = self.mc._categorize_from_labels(["bug", "urgent"])
        self.assertEqual(result, TaskCategory.FIX)

    def test_categorize_from_labels_content(self):
        """Test label categorization for content"""
        result = self.mc._categorize_from_labels(["content", "social-media"])
        self.assertEqual(result, TaskCategory.CONTENT)

    def test_categorize_from_labels_automation(self):
        """Test label categorization for automation"""
        result = self.mc._categorize_from_labels(["automation", "workflow"])
        self.assertEqual(result, TaskCategory.AUTOMATE)

    def test_categorize_from_labels_strategy(self):
        """Test label categorization for strategy"""
        result = self.mc._categorize_from_labels(["strategy", "roadmap"])
        self.assertEqual(result, TaskCategory.STRATEGY)

    def test_categorize_from_labels_default(self):
        """Test label categorization defaults to BUILD"""
        result = self.mc._categorize_from_labels(["feature", "enhancement"])
        self.assertEqual(result, TaskCategory.BUILD)

    def test_prioritize_tasks(self):
        """Test task prioritization sorts correctly"""
        self.mc.tasks = [
            Task(id="LOW", title="Low", source="test",
                 category=TaskCategory.BUILD, priority=Priority.LOW,
                 impact=2, urgency=2, effort=8),
            Task(id="HIGH", title="High", source="test",
                 category=TaskCategory.FIX, priority=Priority.CRITICAL,
                 impact=10, urgency=10, effort=1),
            Task(id="MED", title="Medium", source="test",
                 category=TaskCategory.BUILD, priority=Priority.MEDIUM,
                 impact=5, urgency=5, effort=5),
        ]

        self.mc.prioritize_tasks()

        # First task should be the highest impact one
        self.assertEqual(self.mc.tasks[0].id, "HIGH")
        self.assertEqual(self.mc.tasks[-1].id, "LOW")

    def test_get_top_blockers(self):
        """Test getting top blockers"""
        self.mc.tasks = [
            Task(id="B1", title="Blocker 1", source="test",
                 category=TaskCategory.FIX, priority=Priority.CRITICAL,
                 impact=10, urgency=10, effort=2, blocker=True,
                 blocker_reason="System down"),
            Task(id="N1", title="Not blocker", source="test",
                 category=TaskCategory.BUILD, priority=Priority.LOW,
                 impact=3, urgency=3, effort=5),
            Task(id="B2", title="Blocker 2", source="test",
                 category=TaskCategory.FIX, priority=Priority.HIGH,
                 impact=8, urgency=9, effort=3, blocker=True,
                 blocker_reason="Workflow broken"),
        ]

        blockers = self.mc.get_top_blockers()
        self.assertEqual(len(blockers), 2)
        self.assertTrue(all(t.blocker for t in blockers))

    def test_get_top_blockers_limit(self):
        """Test blocker limit parameter"""
        self.mc.tasks = [
            Task(id=f"B{i}", title=f"Blocker {i}", source="test",
                 category=TaskCategory.FIX, priority=Priority.HIGH,
                 impact=8, urgency=8, effort=3, blocker=True)
            for i in range(20)
        ]

        blockers = self.mc.get_top_blockers(limit=5)
        self.assertEqual(len(blockers), 5)

    def test_get_top_levers(self):
        """Test getting highest-impact tasks"""
        self.mc.tasks = [
            Task(id="L1", title="Low impact", source="test",
                 category=TaskCategory.BUILD, priority=Priority.LOW,
                 impact=2, urgency=2, effort=2),
            Task(id="H1", title="High impact", source="test",
                 category=TaskCategory.BUILD, priority=Priority.HIGH,
                 impact=10, urgency=5, effort=5),
        ]

        levers = self.mc.get_top_levers(limit=1)
        self.assertEqual(len(levers), 1)
        self.assertEqual(levers[0].id, "H1")

    def test_get_time_critical(self):
        """Test getting time-critical tasks"""
        self.mc.tasks = [
            Task(id="TC1", title="Deadline task", source="test",
                 category=TaskCategory.BUILD, priority=Priority.HIGH,
                 impact=8, urgency=9, effort=3,
                 deadline="2026-02-15"),
            Task(id="N1", title="No deadline", source="test",
                 category=TaskCategory.BUILD, priority=Priority.LOW,
                 impact=3, urgency=3, effort=5),
        ]

        time_critical = self.mc.get_time_critical()
        self.assertEqual(len(time_critical), 1)
        self.assertEqual(time_critical[0].id, "TC1")

    def test_get_cost_risks(self):
        """Test getting cost-risk tasks"""
        self.mc.tasks = [
            Task(id="CR1", title="Costly task", source="test",
                 category=TaskCategory.FIX, priority=Priority.HIGH,
                 impact=7, urgency=8, effort=4,
                 cost_risk="API cost overrun"),
            Task(id="N1", title="No cost risk", source="test",
                 category=TaskCategory.BUILD, priority=Priority.LOW,
                 impact=3, urgency=3, effort=5),
        ]

        cost_risks = self.mc.get_cost_risks()
        self.assertEqual(len(cost_risks), 1)
        self.assertEqual(cost_risks[0].cost_risk, "API cost overrun")

    def test_get_by_category(self):
        """Test filtering tasks by category"""
        self.mc.tasks = [
            Task(id="B1", title="Build task", source="test",
                 category=TaskCategory.BUILD, priority=Priority.MEDIUM,
                 impact=5, urgency=5, effort=5),
            Task(id="F1", title="Fix task", source="test",
                 category=TaskCategory.FIX, priority=Priority.HIGH,
                 impact=8, urgency=8, effort=3),
            Task(id="B2", title="Build task 2", source="test",
                 category=TaskCategory.BUILD, priority=Priority.LOW,
                 impact=3, urgency=3, effort=7),
        ]

        build_tasks = self.mc.get_by_category(TaskCategory.BUILD)
        self.assertEqual(len(build_tasks), 2)
        self.assertTrue(all(t.category == TaskCategory.BUILD for t in build_tasks))

    def test_get_by_category_limit(self):
        """Test category filter with limit"""
        self.mc.tasks = [
            Task(id=f"B{i}", title=f"Build {i}", source="test",
                 category=TaskCategory.BUILD, priority=Priority.MEDIUM,
                 impact=5, urgency=5, effort=5)
            for i in range(10)
        ]

        limited = self.mc.get_by_category(TaskCategory.BUILD, limit=3)
        self.assertEqual(len(limited), 3)


class TestDashboardGeneration(unittest.TestCase):
    """Test dashboard and report generation"""

    def setUp(self):
        """Set up with sample tasks"""
        self.mc = MissionControl(repo_path=str(Path(__file__).parent))
        self.mc.tasks = [
            Task(id="GH-1", title="Fix critical workflow", source="GitHub Issues",
                 category=TaskCategory.FIX, priority=Priority.CRITICAL,
                 impact=10, urgency=10, effort=2, blocker=True,
                 blocker_reason="Pipeline broken"),
            Task(id="GH-2", title="Create Fiverr gigs", source="GitHub Issues",
                 category=TaskCategory.CONTENT, priority=Priority.HIGH,
                 impact=9, urgency=7, effort=4),
            Task(id="TASK-deploy", title="Deploy CRM update", source="Atomic Reactor",
                 category=TaskCategory.BUILD, priority=Priority.MEDIUM,
                 impact=6, urgency=5, effort=5,
                 deadline="2026-02-20"),
            Task(id="WF-content", title="Fix content workflow", source="GitHub Actions",
                 category=TaskCategory.FIX, priority=Priority.HIGH,
                 impact=7, urgency=8, effort=3,
                 cost_risk="Content pipeline stopped"),
        ]

    def test_generate_dashboard(self):
        """Test dashboard generation produces valid markdown"""
        dashboard = self.mc.generate_dashboard()

        self.assertIsInstance(dashboard, str)
        self.assertIn("MISSION CONTROL", dashboard)
        self.assertIn("Overview", dashboard)
        self.assertIn("Top 10 Blockers", dashboard)
        self.assertIn("Top 10 Levers", dashboard)
        self.assertIn("Tasks by Category", dashboard)
        self.assertIn("What to do NOW", dashboard)

    def test_dashboard_contains_tasks(self):
        """Test dashboard includes task data"""
        dashboard = self.mc.generate_dashboard()

        self.assertIn("GH-1", dashboard)
        self.assertIn("Fix critical workflow", dashboard)
        self.assertIn("Pipeline broken", dashboard)

    def test_dashboard_overview_stats(self):
        """Test dashboard overview statistics"""
        dashboard = self.mc.generate_dashboard()

        self.assertIn("Total Open Tasks", dashboard)
        self.assertIn("Blockers", dashboard)
        self.assertIn("High Priority", dashboard)

    def test_dashboard_time_critical_section(self):
        """Test dashboard includes time-critical tasks"""
        dashboard = self.mc.generate_dashboard()

        self.assertIn("Time-Critical", dashboard)
        self.assertIn("2026-02-20", dashboard)

    def test_dashboard_cost_risks_section(self):
        """Test dashboard includes cost risks"""
        dashboard = self.mc.generate_dashboard()

        self.assertIn("Cost Risks", dashboard)
        self.assertIn("Content pipeline stopped", dashboard)

    def test_generate_action_list(self):
        """Test action list generation"""
        self.mc.prioritize_tasks()
        action_list = self.mc.generate_action_list(limit=3)

        self.assertIsInstance(action_list, str)
        # Should contain task details
        self.assertIn("Source:", action_list)
        self.assertIn("Priority:", action_list)

    def test_action_list_limit(self):
        """Test action list respects limit"""
        self.mc.prioritize_tasks()
        action_list = self.mc.generate_action_list(limit=2)

        # Count numbered items (lines starting with "1." or "2.")
        lines = action_list.strip().split("\n")
        numbered = [l for l in lines if l and l[0].isdigit() and "." in l[:3]]
        self.assertLessEqual(len(numbered), 2)


class TestJsonExport(unittest.TestCase):
    """Test JSON export functionality"""

    def setUp(self):
        """Set up with sample tasks"""
        self.mc = MissionControl(repo_path=str(Path(__file__).parent))
        self.mc.tasks = [
            Task(id="TEST-1", title="Test task", source="Unit Test",
                 category=TaskCategory.BUILD, priority=Priority.HIGH,
                 impact=8, urgency=7, effort=3),
        ]
        self.output_path = Path(__file__).parent / "test_mission_control_output.json"

    def tearDown(self):
        """Clean up test output files"""
        if self.output_path.exists():
            self.output_path.unlink()

    def test_export_creates_file(self):
        """Test JSON export creates a file"""
        result = self.mc.export_to_json(output_path=self.output_path)
        self.assertTrue(self.output_path.exists())
        self.assertEqual(result, str(self.output_path))

    def test_export_valid_json(self):
        """Test exported file contains valid JSON"""
        self.mc.export_to_json(output_path=self.output_path)

        with open(self.output_path) as f:
            data = json.load(f)

        self.assertIsInstance(data, dict)
        self.assertIn("generated_at", data)
        self.assertIn("summary", data)
        self.assertIn("tasks", data)

    def test_export_summary_structure(self):
        """Test exported summary has correct structure"""
        self.mc.export_to_json(output_path=self.output_path)

        with open(self.output_path) as f:
            data = json.load(f)

        summary = data["summary"]
        self.assertIn("total_tasks", summary)
        self.assertIn("by_category", summary)
        self.assertIn("by_priority", summary)
        self.assertIn("blockers", summary)
        self.assertEqual(summary["total_tasks"], 1)

    def test_export_task_data(self):
        """Test exported tasks contain correct data"""
        self.mc.export_to_json(output_path=self.output_path)

        with open(self.output_path) as f:
            data = json.load(f)

        tasks = data["tasks"]
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["id"], "TEST-1")
        self.assertEqual(tasks[0]["title"], "Test task")
        self.assertEqual(tasks[0]["category"], "BUILD")
        self.assertEqual(tasks[0]["priority"], "HIGH")

    def test_export_enum_serialization(self):
        """Test that enums are properly serialized to strings"""
        self.mc.export_to_json(output_path=self.output_path)

        with open(self.output_path) as f:
            data = json.load(f)

        task = data["tasks"][0]
        # Should be strings, not enum representations
        self.assertIsInstance(task["category"], str)
        self.assertIsInstance(task["priority"], str)
        self.assertNotIn("TaskCategory", task["category"])
        self.assertNotIn("Priority", task["priority"])


class TestScanners(unittest.TestCase):
    """Test individual scanner methods"""

    def setUp(self):
        """Set up with local repo path"""
        self.mc = MissionControl(repo_path=str(Path(__file__).parent))

    def test_scan_task_files_no_yaml(self):
        """Test task file scanner handles missing yaml gracefully"""
        # Should not raise even if yaml is not installed or no files found
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(self.mc.scan_task_files())
        except Exception as e:
            self.fail(f"scan_task_files raised exception: {e}")
        finally:
            loop.close()

    @patch("subprocess.run")
    def test_scan_github_issues_no_gh(self, mock_run):
        """Test GitHub scanner handles missing gh CLI"""
        mock_run.side_effect = FileNotFoundError("gh not found")

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(self.mc.scan_github_issues())
        except Exception as e:
            self.fail(f"scan_github_issues raised exception: {e}")
        finally:
            loop.close()

    @patch("subprocess.run")
    def test_scan_github_issues_with_data(self, mock_run):
        """Test GitHub scanner processes issues correctly"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([
            {
                "number": 42,
                "title": "Test issue",
                "labels": [{"name": "bug"}],
                "state": "OPEN",
                "createdAt": "2026-02-10T10:00:00Z",
            }
        ])
        mock_run.return_value = mock_result

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(self.mc.scan_github_issues())
        finally:
            loop.close()

        self.assertEqual(len(self.mc.tasks), 1)
        self.assertEqual(self.mc.tasks[0].id, "GH-42")
        self.assertEqual(self.mc.tasks[0].category, TaskCategory.FIX)
        self.assertTrue(self.mc.tasks[0].blocker)

    @patch("subprocess.run")
    def test_scan_workflow_runs_failure(self, mock_run):
        """Test workflow scanner detects failures"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([
            {"name": "CI Build", "status": "completed", "conclusion": "failure"},
            {"name": "Deploy", "status": "completed", "conclusion": "success"},
        ])
        mock_run.return_value = mock_result

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(self.mc.scan_workflow_runs())
        finally:
            loop.close()

        # Only failed workflows should create tasks
        self.assertEqual(len(self.mc.tasks), 1)
        self.assertIn("CI Build", self.mc.tasks[0].title)
        self.assertTrue(self.mc.tasks[0].blocker)

    @patch("subprocess.run")
    def test_scan_docker_no_docker(self, mock_run):
        """Test Docker scanner handles missing docker"""
        mock_run.side_effect = FileNotFoundError("docker not found")

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(self.mc.scan_docker_services())
        except Exception as e:
            self.fail(f"scan_docker_services raised exception: {e}")
        finally:
            loop.close()

    def test_scan_brain_system_no_db(self):
        """Test brain scanner handles missing database"""
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(self.mc.scan_brain_system())
        except Exception as e:
            self.fail(f"scan_brain_system raised exception: {e}")
        finally:
            loop.close()

    def test_scan_logs_no_errors(self):
        """Test log scanner handles no log files"""
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(self.mc.scan_logs())
        except Exception as e:
            self.fail(f"scan_logs raised exception: {e}")
        finally:
            loop.close()


class TestEmptyState(unittest.TestCase):
    """Test behavior with no tasks"""

    def setUp(self):
        self.mc = MissionControl(repo_path=str(Path(__file__).parent))

    def test_empty_dashboard(self):
        """Test dashboard generation with no tasks"""
        dashboard = self.mc.generate_dashboard()
        self.assertIn("MISSION CONTROL", dashboard)
        self.assertIn("Total Open Tasks", dashboard)
        self.assertIn("0", dashboard)

    def test_empty_blockers(self):
        """Test blockers with no tasks"""
        blockers = self.mc.get_top_blockers()
        self.assertEqual(len(blockers), 0)

    def test_empty_levers(self):
        """Test levers with no tasks"""
        levers = self.mc.get_top_levers()
        self.assertEqual(len(levers), 0)

    def test_empty_prioritize(self):
        """Test prioritization with no tasks"""
        self.mc.prioritize_tasks()
        self.assertEqual(len(self.mc.tasks), 0)

    def test_empty_action_list(self):
        """Test action list with no tasks"""
        action_list = self.mc.generate_action_list()
        self.assertEqual(action_list, "")


if __name__ == "__main__":
    unittest.main()
