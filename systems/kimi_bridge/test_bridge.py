import asyncio
from kimi_client import KimiClient
import sys

async def test_bridge():
    print("🧪 Testing Kimi Bridge Client...")
    client = KimiClient()
    
    print(f"configurations: Local={client.local_model}, API={client.api_model}")
    
    messages = [{"role": "user", "content": "Hello, are you Kimi? Answer briefly."}]
    
    # Test 1: Local (Priority)
    print("\n[1] Testing Local Inference (Ollama)...")
    try:
        res = await client.chat(messages, use_local=True)
        print(f"✅ Success: {res}")
    except Exception as e:
        print(f"❌ Failed: {e}")

    # Test 2: API Only
    print("\n[2] Testing Cloud API (Moonshot)...")
    try:
        res = await client.chat(messages, use_local=False)
        print(f"✅ Success: {res}")
    except Exception as e:
        print(f"❌ Failed: {e}")
        
    print("\n✨ Test Complete.")

if __name__ == "__main__":
    try:
        asyncio.run(test_bridge())
    except KeyboardInterrupt:
        pass
