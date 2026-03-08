#!/usr/bin/env python3
"""
Neural Brain - Data Harvester
Extract and ingest historical AI conversations
Sources: ChatGPT, Claude, Gemini, Grok exports
Convert to RAG-ready knowledge store (ChromaDB)
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class DataHarvester:
    """Extract and process historical AI conversations"""

    def __init__(self, knowledge_store_path: Path = Path("neural_brain_knowledge.json")):
        self.knowledge_store_path = knowledge_store_path
        self.load_knowledge_store()

    def load_knowledge_store(self):
        """Load existing knowledge store"""
        if self.knowledge_store_path.exists():
            with open(self.knowledge_store_path, 'r') as f:
                self.knowledge = json.load(f)
        else:
            self.knowledge = {
                "harvested_sources": [],
                "insights": [],
                "patterns": [],
                "best_practices": [],
                "revenue_hints": [],
                "timestamps": []
            }

    def save_knowledge_store(self):
        """Persist knowledge store"""
        with open(self.knowledge_store_path, 'w') as f:
            json.dump(self.knowledge, f, indent=2, default=str)

    def harvest_chatgpt_export(self, json_file: Path) -> List[Dict]:
        """Parse ChatGPT conversation export"""
        conversations = []

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # ChatGPT export format
            for item in data:
                if "title" in item and "conversations" in item:
                    for conv in item.get("conversations", []):
                        if "messages" in conv:
                            for msg in conv["messages"]:
                                if msg.get("from") in ["gpt", "assistant"]:
                                    conversations.append({
                                        "source": "chatgpt",
                                        "title": item.get("title"),
                                        "content": msg.get("content", ""),
                                        "timestamp": msg.get("timestamp"),
                                        "type": "response"
                                    })

            logger.info(f"✅ Harvested {len(conversations)} ChatGPT conversations")
            return conversations

        except Exception as e:
            logger.error(f"❌ Error parsing ChatGPT export: {e}")
            return []

    def harvest_claude_export(self, json_file: Path) -> List[Dict]:
        """Parse Claude conversation export"""
        conversations = []

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Handle both single conversation and multiple
            items = data if isinstance(data, list) else [data]

            for item in items:
                if isinstance(item, dict):
                    # Direct conversation object
                    for msg in item.get("messages", []):
                        if msg.get("role") == "assistant":
                            conversations.append({
                                "source": "claude",
                                "content": msg.get("content", ""),
                                "timestamp": item.get("created_at", datetime.now().isoformat()),
                                "type": "response"
                            })

            logger.info(f"✅ Harvested {len(conversations)} Claude conversations")
            return conversations

        except Exception as e:
            logger.error(f"❌ Error parsing Claude export: {e}")
            return []

    def harvest_gemini_export(self, json_file: Path) -> List[Dict]:
        """Parse Google Gemini export"""
        conversations = []

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Gemini export format
            for item in data.get("conversations", []):
                for msg in item.get("messages", []):
                    if msg.get("author") in ["bot", "model", "gemini"]:
                        conversations.append({
                            "source": "gemini",
                            "content": msg.get("content", ""),
                            "timestamp": item.get("timestamp"),
                            "type": "response"
                        })

            logger.info(f"✅ Harvested {len(conversations)} Gemini conversations")
            return conversations

        except Exception as e:
            logger.error(f"❌ Error parsing Gemini export: {e}")
            return []

    def harvest_grok_export(self, json_file: Path) -> List[Dict]:
        """Parse X/Grok export"""
        conversations = []

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Grok export format
            for conv in data.get("conversations", []):
                for msg in conv.get("messages", []):
                    if msg.get("role") == "assistant":
                        conversations.append({
                            "source": "grok",
                            "content": msg.get("content", ""),
                            "timestamp": conv.get("timestamp"),
                            "type": "response"
                        })

            logger.info(f"✅ Harvested {len(conversations)} Grok conversations")
            return conversations

        except Exception as e:
            logger.error(f"❌ Error parsing Grok export: {e}")
            return []

    def extract_insights(self, content: str) -> List[str]:
        """Extract actionable insights from content"""
        insights = []

        # Pattern matching for key concepts
        patterns = {
            "revenue": r"(?:revenue|income|profit|earn|monetize).*?[\.\!]",
            "automation": r"(?:automat|autonomous|self-.*?optim).*?[\.\!]",
            "implementation": r"(?:implement|deploy|launch|release).*?[\.\!]",
            "ai_technique": r"(?:prompt|agent|chain|model|neural).*?[\.\!]",
            "best_practice": r"(?:best practice|recommended|optimal|efficient).*?[\.\!]"
        }

        for category, pattern in patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                insights.append({
                    "category": category,
                    "text": match.strip(),
                    "confidence": 0.8
                })

        return insights

    def process_harvest(self, conversations: List[Dict]) -> Dict:
        """Process harvested conversations into knowledge"""
        results = {
            "total_conversations": len(conversations),
            "insights_extracted": 0,
            "patterns_found": 0,
            "best_practices": 0
        }

        for conv in conversations:
            content = conv.get("content", "")

            # Extract insights
            insights = self.extract_insights(content)
            results["insights_extracted"] += len(insights)
            self.knowledge["insights"].extend(insights)

            # Track source
            source = conv.get("source")
            if source not in self.knowledge["harvested_sources"]:
                self.knowledge["harvested_sources"].append(source)

            # Extract best practices
            if any(word in content.lower() for word in ["best practice", "recommended", "optimal"]):
                self.knowledge["best_practices"].append({
                    "source": source,
                    "content": content[:500],
                    "extracted_at": datetime.now().isoformat()
                })
                results["best_practices"] += 1

        self.save_knowledge_store()
        return results

    def harvest_directory(self, directory: Path, source_type: str = "auto") -> Dict:
        """Harvest all export files from directory"""
        logger.info(f"🔍 Harvesting from {directory}")

        all_conversations = []
        results = {
            "total_files": 0,
            "processed_files": 0,
            "failed_files": 0,
            "total_conversations": 0
        }

        for file_path in directory.glob("*.json"):
            results["total_files"] += 1
            logger.info(f"Processing {file_path.name}")

            # Auto-detect source type
            file_name = file_path.name.lower()
            if "chatgpt" in file_name or source_type == "chatgpt":
                convs = self.harvest_chatgpt_export(file_path)
            elif "claude" in file_name or source_type == "claude":
                convs = self.harvest_claude_export(file_path)
            elif "gemini" in file_name or source_type == "gemini":
                convs = self.harvest_gemini_export(file_path)
            elif "grok" in file_name or source_type == "grok":
                convs = self.harvest_grok_export(file_path)
            else:
                # Try each parser
                convs = (self.harvest_claude_export(file_path) or
                        self.harvest_chatgpt_export(file_path) or
                        self.harvest_gemini_export(file_path))

            if convs:
                all_conversations.extend(convs)
                results["processed_files"] += 1
            else:
                results["failed_files"] += 1

        # Process all conversations
        results["total_conversations"] = len(all_conversations)
        process_results = self.process_harvest(all_conversations)

        logger.info(f"✅ Harvest complete:")
        logger.info(f"   Total conversations: {results['total_conversations']}")
        logger.info(f"   Insights extracted: {process_results['insights_extracted']}")
        logger.info(f"   Best practices: {process_results['best_practices']}")

        return {**results, **process_results}

    def generate_summary(self) -> str:
        """Generate summary of harvested knowledge"""
        summary = f"""
🧠 Neural Brain Knowledge Summary
================================

📊 Sources Harvested: {', '.join(self.knowledge['harvested_sources']) or 'None yet'}
💡 Total Insights: {len(self.knowledge['insights'])}
🏆 Best Practices Extracted: {len(self.knowledge['best_practices'])}
💰 Revenue Hints: {len(self.knowledge['revenue_hints'])}

Top Insight Categories:
"""
        # Count by category
        categories = {}
        for insight in self.knowledge['insights']:
            cat = insight.get('category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1

        for cat, count in sorted(categories.items(), key=lambda x: -x[1])[:5]:
            summary += f"\n  • {cat}: {count} items"

        summary += f"\n\n✅ Knowledge store updated: {datetime.now().isoformat()}"
        return summary


async def harvest_from_uploads(uploads_dir: Path = Path("neural_brain_uploads")):
    """Harvest data from uploaded files in neural_brain_uploads"""
    harvester = DataHarvester()

    logger.info(f"📂 Scanning {uploads_dir} for exports...")

    if uploads_dir.exists():
        results = harvester.harvest_directory(uploads_dir, source_type="auto")
        summary = harvester.generate_summary()

        logger.info(summary)
        return results
    else:
        logger.warning(f"Directory {uploads_dir} not found")
        return None


def load_knowledge_for_rag() -> Dict:
    """Load knowledge store formatted for RAG"""
    ks = DataHarvester()

    return {
        "insights": ks.knowledge.get("insights", []),
        "best_practices": ks.knowledge.get("best_practices", []),
        "patterns": ks.knowledge.get("patterns", []),
        "sources": ks.knowledge.get("harvested_sources", [])
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
    else:
        path = Path("exports")

    harvester = DataHarvester()

    if path.exists():
        if path.is_dir():
            results = harvester.harvest_directory(path)
        else:
            # Try to detect file type
            if "chatgpt" in path.name:
                results = harvester.process_harvest(harvester.harvest_chatgpt_export(path))
            elif "claude" in path.name:
                results = harvester.process_harvest(harvester.harvest_claude_export(path))
            else:
                results = harvester.process_harvest(harvester.harvest_claude_export(path))

        print(harvester.generate_summary())
    else:
        print(f"❌ Path not found: {path}")
        print(f"Usage: python neural_brain_data_harvester.py <path-to-exports>")
