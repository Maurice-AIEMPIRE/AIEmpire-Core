#!/usr/bin/env python3
"""
Quick Test Suite for Advanced Telegram Bot
Tests: Redis, Ollama, Ant Protocol, NLU, Agent Routing
"""

import asyncio
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def test_result(name, success, details=""):
    """Print test result"""
    status = f"{GREEN}✅ PASS{RESET}" if success else f"{RED}❌ FAIL{RESET}"
    print(f"{status} - {name}")
    if details:
        print(f"       {BLUE}{details}{RESET}")


# ============================================================================
# TEST 1: Redis Connection
# ============================================================================

def test_redis():
    """Test Redis connectivity"""
    try:
        import redis
        r = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), decode_responses=True)
        r.ping()

        # Test write/read
        r.set("bot_test", f"Test at {datetime.utcnow().isoformat()}")
        value = r.get("bot_test")

        test_result("Redis Connection", True, f"Host: {os.getenv('REDIS_HOST', 'localhost')}")
        return True
    except Exception as e:
        test_result("Redis Connection", False, str(e))
        return False


# ============================================================================
# TEST 2: Python Imports
# ============================================================================

def test_imports():
    """Test all required imports"""
    try:
        import aiohttp
        import redis
        import tenacity
        from dotenv import load_dotenv

        test_result("Python Imports", True, "aiohttp, redis, tenacity, dotenv")
        return True
    except Exception as e:
        test_result("Python Imports", False, str(e))
        return False


# ============================================================================
# TEST 3: NLU Engine
# ============================================================================

async def test_nlu():
    """Test NLU Engine"""
    try:
        from advanced_bot import NLUEngine

        nlu = NLUEngine()
        await nlu.initialize()

        # Test intent detection
        result = await nlu.understand("What is the system status?", [])

        await nlu.close()

        success = result.get("intent") in ["status", "query"]
        test_result(
            "NLU Engine",
            success,
            f"Intent: {result.get('intent')}, Confidence: {result.get('confidence')}%"
        )
        return success
    except Exception as e:
        test_result("NLU Engine", False, str(e))
        return False


# ============================================================================
# TEST 4: Agent Executor
# ============================================================================

async def test_agent_executor():
    """Test Agent Executor"""
    try:
        from agent_executor import AgentExecutor

        executor = AgentExecutor()
        await executor.initialize()

        # Test Ant Protocol connection (should fail gracefully if unreachable)
        result = await executor.get_all_agents_status()

        await executor.close()

        test_result(
            "Agent Executor",
            True,
            f"Status check completed. Found {len(result)} agents"
        )
        return True
    except Exception as e:
        test_result("Agent Executor", False, str(e))
        return False


# ============================================================================
# TEST 5: Telegram Connection
# ============================================================================

def test_telegram():
    """Test Telegram Bot Token"""
    try:
        token = os.getenv("BOT_TOKEN")
        if not token:
            test_result("Telegram Token", False, "BOT_TOKEN not in .env")
            return False

        if len(token) < 20:
            test_result("Telegram Token", False, "Token too short")
            return False

        test_result("Telegram Token", True, f"Token format valid: {token[:10]}...")
        return True
    except Exception as e:
        test_result("Telegram Token", False, str(e))
        return False


# ============================================================================
# TEST 6: Ollama Connection
# ============================================================================

async def test_ollama():
    """Test Ollama NLU Provider"""
    try:
        import aiohttp

        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")

        async with aiohttp.ClientSession() as session:
            try:
                response = await session.get(
                    f"{ollama_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=5)
                )

                if response.status == 200:
                    data = await response.json()
                    models = data.get("models", [])
                    test_result(
                        "Ollama Connection",
                        True,
                        f"URL: {ollama_url}, Models: {len(models)}"
                    )
                    return True
                else:
                    test_result(
                        "Ollama Connection",
                        False,
                        f"HTTP {response.status}"
                    )
                    return False
            except asyncio.TimeoutError:
                test_result(
                    "Ollama Connection",
                    False,
                    f"Timeout - Ollama not accessible at {ollama_url}"
                )
                return False
    except Exception as e:
        test_result("Ollama Connection", False, str(e))
        return False


# ============================================================================
# TEST 7: Ant Protocol Connection
# ============================================================================

async def test_ant_protocol():
    """Test Ant Protocol API"""
    try:
        import aiohttp

        ant_url = os.getenv("ANT_PROTOCOL_URL", "http://localhost:8900")

        async with aiohttp.ClientSession() as session:
            try:
                response = await session.get(
                    f"{ant_url}/health",
                    timeout=aiohttp.ClientTimeout(total=5)
                )

                if response.status in [200, 404]:
                    test_result(
                        "Ant Protocol",
                        True,
                        f"URL: {ant_url} (HTTP {response.status})"
                    )
                    return True
                else:
                    test_result(
                        "Ant Protocol",
                        False,
                        f"HTTP {response.status}"
                    )
                    return False
            except asyncio.TimeoutError:
                test_result(
                    "Ant Protocol",
                    False,
                    f"Timeout - Not accessible at {ant_url}"
                )
                return False
    except Exception as e:
        test_result("Ant Protocol", False, str(e))
        return False


# ============================================================================
# ASYNC TESTS
# ============================================================================

async def run_async_tests():
    """Run all async tests"""
    results = []

    print(f"\n{BLUE}🧪 Testing NLU Engine...{RESET}")
    results.append(await test_nlu())

    print(f"\n{BLUE}🤖 Testing Agent Executor...{RESET}")
    results.append(await test_agent_executor())

    print(f"\n{BLUE}🌐 Testing Ollama...{RESET}")
    results.append(await test_ollama())

    print(f"\n{BLUE}🐜 Testing Ant Protocol...{RESET}")
    results.append(await test_ant_protocol())

    return results


# ============================================================================
# MAIN TEST SUITE
# ============================================================================

async def main():
    """Run all tests"""
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Advanced Telegram Bot - Test Suite{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

    # Sync tests
    print(f"{BLUE}🔍 Testing Imports...{RESET}")
    test_imports()

    print(f"\n{BLUE}📊 Testing Redis...{RESET}")
    test_redis()

    print(f"\n{BLUE}🔑 Testing Telegram...{RESET}")
    test_telegram()

    # Async tests
    async_results = await run_async_tests()

    # Summary
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Test Summary{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

    total_tests = 7 + len(async_results)
    passed = sum([
        test_imports(),
        test_redis(),
        test_telegram()
    ]) + sum(async_results)

    print(f"Passed: {passed}/{total_tests} tests")

    if passed == total_tests:
        print(f"\n{GREEN}✅ ALL TESTS PASSED! Bot is ready to deploy!{RESET}\n")
        return 0
    else:
        print(f"\n{YELLOW}⚠️  Some tests failed. Check configuration.{RESET}\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
