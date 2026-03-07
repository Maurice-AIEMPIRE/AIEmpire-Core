#!/usr/bin/env python3
"""
Neural Brain - X.com Monitor
Real-time monitoring of top AI experts on X/Twitter
Detects trending topics (3x mention = implement)
Extracts implementations and concepts
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import logging
import re

logger = logging.getLogger(__name__)


class XMonitor:
    """Monitor X.com for AI expert insights"""

    # Top AI experts to monitor
    DEFAULT_EXPERTS = [
        "Peter_Steingraber",
        "ylecun",  # Yann LeCun
        "demishassabis",  # DeepMind
        "karpathy",  # AI architect
        "sama",  # Sam Altman
        "darioamodei",  # Anthropic
        "jackiehluo",  # Hugging Face
        "stabilityai",
        "AGI_Research",
        "TheXAICompany",
        "OpenAI",
        "GoogleDeepMind",
        "MetaAI",
        "nvidia",
        "huggingface",
        "cerebras",
        "mistralai",
        "anthropicai",
        "perplexity_ai",
        "cohere",
    ]

    def __init__(self, experts: Optional[List[str]] = None):
        self.experts = experts or self.DEFAULT_EXPERTS
        self.knowledge_file = Path("neural_brain_x_monitor.json")
        self.load_knowledge()

    def load_knowledge(self):
        """Load monitoring data"""
        if self.knowledge_file.exists():
            with open(self.knowledge_file, 'r') as f:
                self.data = json.load(f)
        else:
            self.data = {
                "trends": {},
                "insights": [],
                "implementations": [],
                "last_sync": None,
                "monitoring_history": []
            }

    def save_knowledge(self):
        """Persist monitoring data"""
        with open(self.knowledge_file, 'w') as f:
            json.dump(self.data, f, indent=2, default=str)

    def extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from tweet"""
        # AI/ML keywords
        keywords = re.findall(
            r'(?:agentic|agents?|prompt|embeddings?|rag|llm|transformers?|'
            r'fine-tun(?:ing|ed)|rlhf|retrieval|augment|chain|auto-implement|'
            r'autonomous|self-optim|reasoning|multimodal|vision|code-gen)',
            text.lower()
        )
        return list(set(keywords))

    def detect_trend(self, keyword: str, mention_count: int = 3) -> bool:
        """Check if keyword is trending (3+ mentions)"""
        trend_data = self.data["trends"].get(keyword, {})
        count = trend_data.get("mention_count", 0)
        return count >= mention_count

    def process_tweet(self, tweet: dict) -> Optional[dict]:
        """Process a tweet (mock implementation)"""
        text = tweet.get("text", "")
        author = tweet.get("author", "")
        timestamp = tweet.get("created_at", datetime.now().isoformat())

        keywords = self.extract_keywords(text)

        if not keywords:
            return None

        processed = {
            "author": author,
            "text": text[:500],
            "keywords": keywords,
            "timestamp": timestamp,
            "engagement": tweet.get("likes", 0) + tweet.get("retweets", 0),
            "extracted_concepts": self._extract_concepts(text),
            "implementation_hint": self._extract_implementation(text)
        }

        # Update trend counts
        for keyword in keywords:
            if keyword not in self.data["trends"]:
                self.data["trends"][keyword] = {
                    "mention_count": 0,
                    "first_seen": timestamp,
                    "experts": []
                }

            trend = self.data["trends"][keyword]
            trend["mention_count"] += 1
            if author not in trend["experts"]:
                trend["experts"].append(author)

            # Check if trending
            if self.detect_trend(keyword):
                processed["is_trending"] = True

        return processed

    def _extract_concepts(self, text: str) -> List[str]:
        """Extract AI concepts from text"""
        concepts = []

        # Common AI architecture patterns
        patterns = {
            "agentic": ["agents", "autonomous", "action", "planning"],
            "rag": ["retrieval", "augmented", "generation", "context"],
            "reasoning": ["chain", "step", "reason", "logic"],
            "optimization": ["efficient", "fast", "cost", "optimiz"],
            "implementation": ["implement", "build", "deploy", "code"]
        }

        for concept, keywords in patterns.items():
            if any(kw in text.lower() for kw in keywords):
                concepts.append(concept)

        return list(set(concepts))

    def _extract_implementation(self, text: str) -> Optional[str]:
        """Extract implementation hints from tweet"""
        # Look for code snippets or technical details
        if "```" in text:
            code_blocks = re.findall(r'```(.+?)```', text, re.DOTALL)
            if code_blocks:
                return f"Code snippet: {code_blocks[0][:200]}"

        # Look for methodology descriptions
        if any(word in text.lower() for word in ["implement", "build", "use", "deploy"]):
            return f"Implementation hint: {text[:200]}"

        return None

    def generate_implementation_queue(self) -> List[Dict]:
        """Generate list of trending items to implement"""
        queue = []

        for keyword, trend_data in self.data["trends"].items():
            if trend_data["mention_count"] >= 3:
                queue.append({
                    "keyword": keyword,
                    "priority": trend_data["mention_count"],
                    "experts": trend_data["experts"][:5],
                    "first_seen": trend_data["first_seen"],
                    "status": "pending_implementation"
                })

        # Sort by priority
        queue.sort(key=lambda x: -x["priority"])
        return queue

    def log_insight(self, tweet_data: dict):
        """Log extracted insight"""
        insight = {
            "timestamp": datetime.now().isoformat(),
            "author": tweet_data.get("author"),
            "summary": tweet_data.get("text", "")[:200],
            "concepts": tweet_data.get("extracted_concepts", []),
            "trending": tweet_data.get("is_trending", False),
            "implementation": tweet_data.get("implementation_hint")
        }

        self.data["insights"].append(insight)

        if tweet_data.get("is_trending"):
            self.data["implementations"].append({
                "timestamp": datetime.now().isoformat(),
                "source": tweet_data.get("author"),
                "concept": ", ".join(tweet_data.get("extracted_concepts", [])),
                "status": "queued",
                "details": tweet_data.get("implementation_hint")
            })

    async def simulate_x_monitoring(self, num_tweets: int = 20) -> Dict:
        """Simulate monitoring X.com (for demo without API key)"""
        logger.info(f"📡 Simulating X.com monitoring ({num_tweets} tweets)")

        # Mock tweets from experts
        mock_tweets = [
            {
                "author": "Peter_Steingraber",
                "text": "Just implemented agentic RAG system - 3x faster knowledge retrieval. Using autonomous agents with chain-of-thought reasoning.",
                "created_at": datetime.now().isoformat(),
                "likes": 1200,
                "retweets": 450
            },
            {
                "author": "ylecun",
                "text": "The future is agentic. Autonomous systems that reason and implement. See our paper on agent coordination.",
                "created_at": (datetime.now() - timedelta(hours=2)).isoformat(),
                "likes": 5600,
                "retweets": 2100
            },
            {
                "author": "karpathy",
                "text": "Autonomous agents with retrieval augmented generation - the killer combo for production AI systems.",
                "created_at": (datetime.now() - timedelta(hours=4)).isoformat(),
                "likes": 3400,
                "retweets": 1200
            },
            {
                "author": "demishassabis",
                "text": "DeepMind is exploring self-improving agents. Autonomous optimization loops are the next frontier.",
                "created_at": (datetime.now() - timedelta(hours=6)).isoformat(),
                "likes": 4100,
                "retweets": 1800
            },
            {
                "author": "sama",
                "text": "Agents that reason, act, and self-improve. This is what we're building at OpenAI.",
                "created_at": (datetime.now() - timedelta(hours=8)).isoformat(),
                "likes": 6700,
                "retweets": 2900
            },
            {
                "author": "huggingface",
                "text": "New agent framework for autonomous implementations. Deploy RAG + agents in 5 lines of code.",
                "created_at": (datetime.now() - timedelta(hours=10)).isoformat(),
                "likes": 2100,
                "retweets": 980
            },
            {
                "author": "anthropicai",
                "text": "Extended thinking + agent coordination = powerful autonomous systems. See our latest research.",
                "created_at": (datetime.now() - timedelta(hours=12)).isoformat(),
                "likes": 3200,
                "retweets": 1400
            },
            {
                "author": "stabilityai",
                "text": "Autonomous agents for multimodal content generation. Vision + language agents working together.",
                "created_at": (datetime.now() - timedelta(hours=14)).isoformat(),
                "likes": 1800,
                "retweets": 650
            },
        ]

        results = {
            "tweets_processed": 0,
            "insights_extracted": 0,
            "trending_items": 0,
            "implementations_queued": 0
        }

        for tweet in mock_tweets[:num_tweets]:
            processed = self.process_tweet(tweet)
            if processed:
                self.log_insight(processed)
                results["tweets_processed"] += 1
                results["insights_extracted"] += 1

                if processed.get("is_trending"):
                    results["trending_items"] += 1

        self.data["last_sync"] = datetime.now().isoformat()

        # Generate implementation queue
        queue = self.generate_implementation_queue()
        results["implementations_queued"] = len(queue)

        self.save_knowledge()

        return {**results, "queue": queue}

    def get_trending_implementations(self) -> List[Dict]:
        """Get current trending implementations"""
        return self.generate_implementation_queue()

    def get_monitoring_report(self) -> str:
        """Generate monitoring report"""
        queue = self.generate_implementation_queue()

        report = "📡 X.com Monitoring Report\n"
        report += "=" * 40 + "\n\n"

        report += f"🔍 Experts Monitored: {len(self.experts)}\n"
        report += f"💡 Insights Extracted: {len(self.data['insights'])}\n"
        report += f"📈 Trends Detected: {len(self.data['trends'])}\n"
        report += f"🚀 Implementations Queued: {len(self.data['implementations'])}\n\n"

        if queue:
            report += "🎯 Trending Topics (3+ mentions):\n"
            for item in queue[:5]:
                report += f"\n  • {item['keyword'].upper()}\n"
                report += f"    Priority: {item['priority']}\n"
                report += f"    Experts: {', '.join(item['experts'][:3])}\n"
                report += f"    Status: {item['status']}\n"
        else:
            report += "No trending items yet - keep monitoring!\n"

        if self.data["last_sync"]:
            report += f"\n🕐 Last Sync: {self.data['last_sync']}\n"

        return report


async def run_continuous_monitoring(interval_minutes: int = 60):
    """Run continuous monitoring loop"""
    import asyncio

    monitor = XMonitor()

    logger.info("🚀 Starting X.com monitoring (continuous mode)")
    logger.info(f"📡 Will check every {interval_minutes} minutes")

    iteration = 0
    try:
        while True:
            iteration += 1
            logger.info(f"\n{'='*50}")
            logger.info(f"📡 Monitoring iteration {iteration}")
            logger.info(f"{'='*50}")

            results = await monitor.simulate_x_monitoring(num_tweets=20)

            logger.info(f"✅ Processed {results['tweets_processed']} tweets")
            logger.info(f"💡 Extracted {results['insights_extracted']} insights")

            if results.get("queue"):
                logger.info(f"🚀 Queued {results['implementations_queued']} implementations:")
                for item in results["queue"][:3]:
                    logger.info(f"   • {item['keyword']} (priority: {item['priority']})")

            report = monitor.get_monitoring_report()
            logger.info("\n" + report)

            logger.info(f"⏰ Next check in {interval_minutes} minutes...")
            await asyncio.sleep(interval_minutes * 60)

    except KeyboardInterrupt:
        logger.info("✅ X.com monitoring stopped")


if __name__ == "__main__":
    import sys
    import asyncio

    monitor = XMonitor()

    if len(sys.argv) > 1 and sys.argv[1] == "monitor":
        # Run continuous monitoring
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        asyncio.run(run_continuous_monitoring(interval))
    else:
        # Run single check
        logger.info("Running X.com monitoring simulation...")
        results = asyncio.run(monitor.simulate_x_monitoring(20))

        logger.info(monitor.get_monitoring_report())

        print(json.dumps(results, indent=2, default=str))
