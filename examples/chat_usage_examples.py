#!/usr/bin/env python3
"""
USAGE EXAMPLES - Chat Upload & Multi-Model Support
Praktische Beispiele für die neuen Chat-Features
Maurice's AI Empire - 2026
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import chat_manager
sys.path.append(str(Path(__file__).parent.parent))
from chat_manager import ChatManager


async def example_1_basic_upload():
    """Example 1: Einfaches Chat-Upload."""
    print("=" * 60)
    print("EXAMPLE 1: Einfaches Chat-Upload")
    print("=" * 60)
    
    manager = ChatManager()
    
    # Chat-Historie als Text
    chat_text = """User: Hallo, ich brauche Hilfe mit Python
Assistant: Gerne! Was möchtest du über Python wissen?
User: Wie erstelle ich eine REST API?
Assistant: Du kannst FastAPI oder Flask verwenden. FastAPI ist moderner."""
    
    # Upload
    result = await manager.upload_chat(chat_text, format="text")
    print(f"\n✅ Upload erfolgreich: {result}")
    
    # Frage stellen mit Kontext
    print("\n📝 Stelle Frage mit Kontext:")
    answer = await manager.ask_question(
        "Gib mir ein Beispiel für FastAPI",
        model="ollama-qwen"  # Lokal, kostenlos
    )
    print(f"Antwort: {answer.get('answer', answer.get('error'))[:200]}...")


async def example_2_model_comparison():
    """Example 2: Verschiedene Modelle vergleichen."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Model-Vergleich")
    print("=" * 60)
    
    manager = ChatManager()
    
    question = "Was ist Machine Learning in 2 Sätzen?"
    
    # Teste mit verschiedenen Modellen
    models = ["ollama-qwen", "ollama-mistral"]
    
    for model_name in models:
        print(f"\n🤖 Testing mit: {model_name}")
        result = await manager.ask_question(question, model=model_name)
        
        if result.get("success"):
            print(f"✅ {model_name}: {result['answer'][:100]}...")
        else:
            print(f"❌ {model_name}: {result['error']}")


async def example_3_json_upload():
    """Example 3: JSON Format Upload."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: JSON Format Upload")
    print("=" * 60)
    
    manager = ChatManager()
    
    # Chat als JSON
    chat_json = """[
        {"role": "user", "content": "Ich plane ein AI Projekt"},
        {"role": "assistant", "content": "Cool! Worum geht es?"},
        {"role": "user", "content": "Automatisierung von Content"},
        {"role": "assistant", "content": "Das ist ein tolles Projekt!"}
    ]"""
    
    result = await manager.upload_chat(chat_json, format="json")
    print(f"\n✅ JSON Upload: {result}")
    
    # Summary
    summary = manager.get_history_summary()
    print(f"\n📊 Summary: {summary}")


async def example_4_export_import():
    """Example 4: Export und Import."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Export und Import")
    print("=" * 60)
    
    manager = ChatManager()
    
    # Erstelle eine Konversation
    await manager.ask_question("Was ist Python?", model="ollama-qwen")
    
    # Export
    exported = manager.export_conversation()
    print(f"\n📥 Exported: {len(exported)} chars")
    print(f"First 200 chars:\n{exported[:200]}...")
    
    # Jetzt könnte man diesen JSON speichern und später wieder hochladen
    print("\n💡 Tipp: Speichere diesen JSON und lade ihn später mit upload_chat hoch!")


async def example_5_cost_optimization():
    """Example 5: Kosten-Optimierung."""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Kosten-Optimierung")
    print("=" * 60)
    
    manager = ChatManager()
    
    # Strategie: Ollama für einfache Fragen (FREE)
    print("\n💰 Strategie 1: Ollama für einfache Fragen (KOSTENLOS)")
    manager.switch_model("ollama-qwen")
    result = await manager.ask_question("Was ist 2+2?")
    print(f"Result: {result.get('answer', result.get('error'))[:200] if result.get('answer') else result.get('error')}")
    
    # Für komplexe Aufgaben würde man zu Claude wechseln
    print("\n💰 Strategie 2: Claude für komplexe Tasks (QUALITÄT)")
    print("(Würde zu claude-sonnet wechseln wenn API Key vorhanden)")
    
    # Cost Model
    print("\n📊 Cost Model:")
    print("- Ollama (lokal): FREE → 95% der Tasks")
    print("- Kimi: $0.0001/1K tokens → 4% der Tasks")
    print("- Claude Haiku: $0.25/1M tokens → 0.9% der Tasks")
    print("- Claude Opus: $15/1M tokens → 0.1% der Tasks (nur kritisch)")


async def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print(" CHAT UPLOAD & MULTI-MODEL SUPPORT - USAGE EXAMPLES")
    print("=" * 70)
    
    try:
        await example_1_basic_upload()
        await example_2_model_comparison()
        await example_3_json_upload()
        await example_4_export_import()
        await example_5_cost_optimization()
        
        print("\n" + "=" * 70)
        print("✅ Alle Beispiele abgeschlossen!")
        print("=" * 70)
        
        print("\n📚 Weitere Infos:")
        print("- docs/CHAT_UPLOAD_GUIDE.md")
        print("- GITHUB_CONTROL_SYSTEM.md")
        print("\n💡 In GitHub Issues nutzen:")
        print("@bot upload-chat text")
        print("@bot ask [deine Frage]")
        print("@bot models")
        print("@bot switch-model ollama-qwen")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
