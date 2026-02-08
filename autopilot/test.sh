#!/bin/bash
# Test script for Autopilot Empire setup
# This validates components without actually starting Docker

set -e

echo "🧪 AUTOPILOT EMPIRE - Test Suite"
echo "================================"

cd "$(dirname "$0")"

# Test 1: File existence
echo ""
echo "Test 1: Checking required files..."
files=(
    "setup.sh"
    "docker-compose.yml"
    "orchestrator.py"
    "Dockerfile"
    "init-autopilot.sql"
    "README.md"
    ".gitignore"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file missing"
        exit 1
    fi
done

# Test 2: Bash syntax
echo ""
echo "Test 2: Validating bash script syntax..."
bash -n setup.sh && echo "✅ setup.sh syntax valid" || exit 1

# Test 3: Python syntax
echo ""
echo "Test 3: Validating Python code..."
python3 -m py_compile orchestrator.py && echo "✅ orchestrator.py syntax valid" || exit 1

# Test 4: Python imports and execution
echo ""
echo "Test 4: Testing orchestrator functionality..."
python3 << 'PYTEST'
import sys
sys.dont_write_bytecode = True

import orchestrator
print("✅ orchestrator module imports successfully")

# Test Enums
assert hasattr(orchestrator.AgentRole, 'CONTENT_CREATOR')
assert hasattr(orchestrator.AgentState, 'IDLE')
print("✅ Enums defined correctly")

# Test Agent class
agent = orchestrator.AutonomousAgent("test_agent", orchestrator.AgentRole.CONTENT_CREATOR, "test_model")
assert agent.agent_id == "test_agent"
assert agent.state == orchestrator.AgentState.IDLE
print("✅ AutonomousAgent class works")

# Test Orchestrator
orch = orchestrator.AutopilotOrchestrator()
assert len(orch.agents) == 7
print(f"✅ Orchestrator initialized with {len(orch.agents)} agents")

# Test async execution
import asyncio
async def test_exec():
    task = {"type": "test", "count": 1, "goal": 10.0}
    agent = list(orch.agents.values())[0]
    result = await agent.execute(task)
    assert result["status"] == "success"
    assert result["quality"] == 0.85
    return result

result = asyncio.run(test_exec())
print(f"✅ Task execution successful: {result['status']}")

print("\n✅ All Python tests passed!")
PYTEST

# Test 5: SQL syntax
echo ""
echo "Test 5: Validating SQL script..."
if grep -q "CREATE TABLE agents" init-autopilot.sql && \
   grep -q "CREATE TABLE revenue_events" init-autopilot.sql && \
   grep -q "CREATE TABLE task_executions" init-autopilot.sql; then
    echo "✅ All required tables defined in SQL"
else
    echo "❌ Missing table definitions in SQL"
    exit 1
fi

# Test 6: Docker Compose validation (structure check)
echo ""
echo "Test 6: Validating Docker Compose structure..."
if grep -q "ollama-master:" docker-compose.yml && \
   grep -q "orchestrator:" docker-compose.yml && \
   grep -q "postgres-master:" docker-compose.yml && \
   grep -q "redis-cache:" docker-compose.yml; then
    echo "✅ All required services defined in docker-compose.yml"
else
    echo "❌ Missing service definitions in docker-compose.yml"
    exit 1
fi

# Test 7: Dockerfile validation
echo ""
echo "Test 7: Validating Dockerfile..."
if grep -q "FROM python:3.11-slim" Dockerfile && \
   grep -q "COPY orchestrator.py" Dockerfile && \
   grep -q "CMD" Dockerfile; then
    echo "✅ Dockerfile structure valid"
else
    echo "❌ Dockerfile missing required directives"
    exit 1
fi

# Test 8: README completeness
echo ""
echo "Test 8: Checking documentation..."
if [ -s README.md ]; then
    word_count=$(wc -w < README.md)
    if [ "$word_count" -gt 100 ]; then
        echo "✅ README.md exists and contains documentation ($word_count words)"
    else
        echo "❌ README.md too short"
        exit 1
    fi
else
    echo "❌ README.md missing or empty"
    exit 1
fi

# Summary
echo ""
echo "================================"
echo "🎉 ALL TESTS PASSED!"
echo "================================"
echo ""
echo "The Autopilot Empire system is ready for deployment."
echo "To deploy, run: bash setup.sh"
echo ""
