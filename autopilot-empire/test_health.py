#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════
AUTOPILOT EMPIRE - Simple Health Check Test
Maurice's AI Business System - Basic Validation
═══════════════════════════════════════════════════════════════
"""

import sys
import requests
import time

def test_orchestrator_health():
    """Test Orchestrator health endpoint"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        print("✅ Orchestrator health check: PASSED")
        return True
    except Exception as e:
        print(f"❌ Orchestrator health check: FAILED - {e}")
        return False

def test_monitor_health():
    """Test Monitor health endpoint"""
    try:
        response = requests.get("http://localhost:9090/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        print("✅ Monitor health check: PASSED")
        return True
    except Exception as e:
        print(f"❌ Monitor health check: FAILED - {e}")
        return False

def test_ollama_availability():
    """Test Ollama availability"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Ollama availability: PASSED ({len(data.get('models', []))} models available)")
        return True
    except Exception as e:
        print(f"❌ Ollama availability: FAILED - {e}")
        return False

def test_agent_server_endpoints():
    """Test Agent Server API endpoints"""
    try:
        # Test /agents endpoint
        response = requests.get("http://localhost:8000/agents", timeout=10)
        assert response.status_code == 200
        agents = response.json()
        assert len(agents) > 0
        print(f"✅ Agent Server /agents: PASSED ({len(agents)} agents)")
        
        # Test /models endpoint
        response = requests.get("http://localhost:8000/models", timeout=10)
        assert response.status_code == 200
        models = response.json()
        assert len(models) > 0
        print(f"✅ Agent Server /models: PASSED ({len(models)} models)")
        
        # Test /stats endpoint
        response = requests.get("http://localhost:8000/stats", timeout=10)
        assert response.status_code == 200
        stats = response.json()
        assert "revenue_today" in stats
        print(f"✅ Agent Server /stats: PASSED")
        
        return True
    except Exception as e:
        print(f"❌ Agent Server endpoints: FAILED - {e}")
        return False

def test_monitor_status():
    """Test Monitor status endpoint"""
    try:
        response = requests.get("http://localhost:9090/status", timeout=10)
        assert response.status_code == 200
        status = response.json()
        assert "database" in status
        assert "ollama" in status
        assert "agents" in status
        print("✅ Monitor /status: PASSED")
        return True
    except Exception as e:
        print(f"❌ Monitor status: FAILED - {e}")
        return False

def main():
    """Run all health checks"""
    print("═══════════════════════════════════════════════════════════════")
    print("🏥 AUTOPILOT EMPIRE - Health Check Tests")
    print("═══════════════════════════════════════════════════════════════")
    print("")
    
    # Wait a bit for services to be ready
    print("⏳ Waiting 5 seconds for services to be ready...")
    time.sleep(5)
    print("")
    
    results = []
    
    # Run all tests
    print("Running tests...")
    print("")
    
    results.append(("Orchestrator Health", test_orchestrator_health()))
    results.append(("Monitor Health", test_monitor_health()))
    results.append(("Ollama Availability", test_ollama_availability()))
    results.append(("Agent Server Endpoints", test_agent_server_endpoints()))
    results.append(("Monitor Status", test_monitor_status()))
    
    print("")
    print("═══════════════════════════════════════════════════════════════")
    print("📊 TEST RESULTS")
    print("═══════════════════════════════════════════════════════════════")
    print("")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print("")
    print(f"Total: {passed}/{total} tests passed")
    print("")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
