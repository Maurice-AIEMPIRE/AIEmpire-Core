"""
Self-Improving Content Generation Engine
==========================================
Generates Human-Level Content for Multiple Platforms

Features:
  1. Learns from engagement metrics (YT, TikTok, X)
  2. A/B tests content formats
  3. Adapts to trending topics
  4. Generates 100+ variations
  5. Automatically posts to all platforms
  6. Analyzes what works, doubles down

Platforms:
  - YouTube (long-form: 5-15 min videos with scripts)
  - TikTok (short-form: 15-60 sec + hooks)
  - Twitter/X (threads, hot takes, engagement)
  - Medium/Blog (deep-dive articles 2000-5000 words)

Content Loop:
  Trend Detection → Content Generation → Multi-Platform Posts
            ↑_________________________________↓
            Engagement Analysis → Learning Loop Update
"""

import json
import asyncio
from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any
import time

from antigravity.config import PROJECT_ROOT
from antigravity.offline_claude import OfflineClaude, ClaudeRole


class ContentTier(str, Enum):
    """Content quality/depth."""
    VIRAL = "viral"          # Trending, high engagement
    QUALITY = "quality"      # High-quality, educational
    EVERGREEN = "evergreen"  # Timeless, reference material
    TREND = "trend"          # Current hot topics
    NICHE = "niche"          # Specialized, expert level


class ContentFormat(str, Enum):
    """Content format."""
    VIDEO_SCRIPT = "video_script"      # YouTube (5-15 min)
    SHORT_FORM = "short_form"          # TikTok (15-60 sec)
    TWEET_THREAD = "tweet_thread"      # X/Twitter
    ARTICLE = "article"                # Blog/Medium (2000+ words)
    HOW_TO = "how_to"                  # Tutorial, step-by-step
    CASE_STUDY = "case_study"          # Deep analysis
    OPINION = "opinion"                # Hot takes


@dataclass
class ContentIdea:
    """An idea for content to generate."""
    topic: str
    format: ContentFormat
    tier: ContentTier
    hooks: List[str]  # Opening hooks that work
    trending: bool = False
    estimated_engagement: float = 0.0
    target_keywords: List[str] = field(default_factory=list)


@dataclass
class GeneratedContent:
    """Generated content piece."""
    content_id: str
    topic: str
    format: ContentFormat
    title: str
    content: str
    engagement_score: float = 0.0
    posted: bool = False
    views: int = 0
    likes: int = 0
    comments: int = 0
    engagement_rate: float = 0.0
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def engagement_metrics(self) -> Dict[str, float]:
        """Calculate engagement metrics."""
        total_interactions = self.views + self.likes + self.comments
        if self.views == 0:
            self.engagement_rate = 0.0
        else:
            self.engagement_rate = (self.likes + self.comments) / self.views

        return {
            "views": self.views,
            "likes": self.likes,
            "comments": self.comments,
            "total_engagement": total_interactions,
            "engagement_rate": self.engagement_rate,
        }


class SelfImprovingContentEngine:
    """
    Generates and learns from content performance.

    Learns which:
    - Topics work best
    - Formats engage most
    - Hooks grab attention
    - Lengths optimize for platform
    - Posting times maximize reach
    """

    CONTENT_DIR = Path(PROJECT_ROOT) / "antigravity" / "_content"
    ANALYTICS_FILE = CONTENT_DIR / "analytics.jsonl"
    LEARNING_MODEL_FILE = CONTENT_DIR / "learning_model.json"

    def __init__(self):
        self.claude = OfflineClaude()
        self.generated_content: Dict[str, GeneratedContent] = {}
        self.learning_model = self._load_learning_model()
        self.engagement_history = []

        self._ensure_directories()
        self._load_analytics()

    def _ensure_directories(self) -> None:
        """Create content directories."""
        self.CONTENT_DIR.mkdir(parents=True, exist_ok=True)

    def _load_learning_model(self) -> Dict[str, Any]:
        """Load or create learning model."""
        if self.LEARNING_MODEL_FILE.exists():
            try:
                with open(self.LEARNING_MODEL_FILE) as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                import warnings
                warnings.warn(f"Failed to load learning model: {e}", stacklevel=2)

        # Default learning model
        return {
            "best_formats": {},
            "best_topics": {},
            "best_hooks": [],
            "worst_formats": {},
            "engagement_by_time": {},
            "format_learnings": {
                "video_script": {"best_length": 8, "avg_engagement": 0.0},
                "short_form": {"best_length": 30, "avg_engagement": 0.0},
                "tweet_thread": {"avg_engagement": 0.0},
                "article": {"best_length": 3000, "avg_engagement": 0.0},
            },
            "topic_performance": {},
            "iterations": 0,
        }

    def _load_analytics(self) -> None:
        """Load engagement analytics."""
        if self.ANALYTICS_FILE.exists():
            try:
                with open(self.ANALYTICS_FILE) as f:
                    for line in f:
                        try:
                            data = json.loads(line)
                            self.engagement_history.append(data)
                        except json.JSONDecodeError:
                            continue  # skip corrupt lines
            except OSError as e:
                import warnings
                warnings.warn(f"Failed to load analytics: {e}", stacklevel=2)

    def _save_learning_model(self) -> None:
        """Save updated learning model."""
        with open(self.LEARNING_MODEL_FILE, "w") as f:
            json.dump(self.learning_model, f, indent=2)

    async def analyze_trends(self) -> List[ContentIdea]:
        """
        Analyze current trends and generate content ideas.

        Sources:
        - Twitter trending
        - Google Trends
        - YouTube trending
        - TikTok trending
        """
        print("📊 Analyzing trends...")

        # In production, would query real trend APIs
        # For now, generate based on current time
        ideas = [
            ContentIdea(
                topic="AI Automation for Small Business",
                format=ContentFormat.VIDEO_SCRIPT,
                tier=ContentTier.TREND,
                hooks=[
                    "This AI tool replaced my entire marketing team",
                    "I saved $50K/year with this automation",
                    "The future is now: watch how AI does 90% of my work",
                ],
                trending=True,
                estimated_engagement=0.08,
                target_keywords=["AI", "automation", "SaaS", "productivity"],
            ),
            ContentIdea(
                topic="How to Build a EUR 100M Business",
                format=ContentFormat.ARTICLE,
                tier=ContentTier.QUALITY,
                hooks=[
                    "The 3-year roadmap to 100M revenue",
                    "What billionaires know about scaling",
                ],
                trending=True,
                estimated_engagement=0.06,
                target_keywords=["business", "scaling", "revenue", "startup"],
            ),
            ContentIdea(
                topic="Local LLM vs Claude: Speed & Cost Comparison",
                format=ContentFormat.SHORT_FORM,
                tier=ContentTier.QUALITY,
                hooks=[
                    "Running Claude offline costs $0 (not joking)",
                    "Why I abandoned Claude for Ollama",
                ],
                trending=True,
                estimated_engagement=0.07,
            ),
        ]

        return ideas

    async def generate_content(
        self,
        idea: ContentIdea,
        variations: int = 3,
    ) -> List[GeneratedContent]:
        """Generate multiple variations of content."""
        print(f"\n🎬 Generating {variations} variations of: {idea.topic}")

        contents = []

        for i in range(variations):
            # Choose different hook and angle
            hook = idea.hooks[i % len(idea.hooks)]

            prompt = self._build_generation_prompt(idea, hook)

            result = await self.claude.think(
                task=prompt,
                role=ClaudeRole.CODER,
                context=f"Platform: {idea.format.value}. Topic: {idea.topic}",
            )

            if "response" in result:
                content = GeneratedContent(
                    content_id=f"content_{int(time.time())}_{i}",
                    topic=idea.topic,
                    format=idea.format,
                    title=f"{idea.topic} - Variation {i+1}",
                    content=result["response"],
                    engagement_score=idea.estimated_engagement,
                )

                contents.append(content)
                self.generated_content[content.content_id] = content

                print(f"  ✓ Variation {i+1} generated")

        return contents

    def _build_generation_prompt(
        self,
        idea: ContentIdea,
        hook: str,
    ) -> str:
        """Build generation prompt based on learning model."""
        format_guide = self._get_format_guide(idea.format)
        best_practices = self._get_best_practices_from_learning()

        return f"""Create exceptional {idea.format.value} content.

Topic: {idea.topic}
Opening Hook: "{hook}"

Format Guidelines:
{format_guide}

Best Practices (learned from {self.learning_model['iterations']} iterations):
{best_practices}

Content MUST:
- Grab attention in first 3 seconds
- Be factually accurate
- Provide real value
- Include specific examples
- Have clear CTA
- Sound natural (human, not robotic)

Generate content that will get maximum engagement."""

    def _get_format_guide(self, fmt: ContentFormat) -> str:
        """Get format-specific guidelines."""
        guides = {
            ContentFormat.VIDEO_SCRIPT: """
- Duration: 5-15 minutes optimal
- Hook: 0-15 seconds must grab attention
- Structure: Hook → Problem → Solution → CTA
- Tone: Conversational, authentic
- Include: B-roll descriptions, transitions
- Format: [VISUAL] text | [AUDIO] speech
""",
            ContentFormat.SHORT_FORM: """
- Duration: 15-60 seconds maximum
- Hook: First 3 frames are critical
- Structure: Hook → Action → Result
- Text: Large, readable overlays
- Sound: Trending audio or attention-grabbing
- Pacing: Fast cuts, dynamic movements
""",
            ContentFormat.TWEET_THREAD: """
- Tweet 1: Headline that compels reading
- Tweets 2-5: Breakdown of idea
- Each tweet: Standalone valuable
- Length: 280 chars per tweet
- Include: Numbers, specific examples
- Final tweet: CTA or question to engage
""",
            ContentFormat.ARTICLE: """
- Length: 2000-5000 words optimal
- Headline: Must include keyword
- Structure: Intro → 3-5 sections → Conclusion
- Sections: Subheadings, numbered lists
- Include: Images, code examples, data
- Reader journey: Question → Answer → Action
- SEO: Keywords in headings, natural language
""",
        }

        return guides.get(fmt, "Create engaging content in the specified format.")

    def _get_best_practices_from_learning(self) -> str:
        """Get best practices from learning model."""
        model = self.learning_model

        practices = "1. Use these proven hooks:\n"
        for hook in model.get("best_hooks", [])[:3]:
            practices += f"   - {hook}\n"

        practices += "\n2. Top performing formats:\n"
        for fmt, score in list(model.get("best_formats", {}).items())[:3]:
            practices += f"   - {fmt}: {score}% engagement\n"

        practices += "\n3. Avoid these (low engagement):\n"
        for fmt in list(model.get("worst_formats", {}).keys())[:2]:
            practices += f"   - {fmt}\n"

        return practices

    async def post_all_platforms(
        self,
        content: GeneratedContent,
    ) -> Dict[str, bool]:
        """
        Post content to all platforms.

        In production, would integrate with:
        - YouTube API
        - TikTok API
        - Twitter API
        - Medium API
        """
        print(f"📤 Posting {content.format.value}: {content.title}")

        results = {
            "youtube": False,
            "tiktok": False,
            "twitter": False,
            "blog": False,
        }

        # Would call actual APIs here
        # For now, simulate posting
        await asyncio.sleep(0.1)

        results["youtube"] = True
        results["twitter"] = True
        results["blog"] = True

        if content.format in (
            ContentFormat.SHORT_FORM,
            ContentFormat.VIDEO_SCRIPT,
        ):
            results["tiktok"] = True

        content.posted = True

        # Log post
        self._log_post(content, results)

        return results

    def _log_post(
        self,
        content: GeneratedContent,
        platforms: Dict[str, bool],
    ) -> None:
        """Log posted content."""
        try:
            with open(self.ANALYTICS_FILE, "a") as f:
                log_entry = {
                    "timestamp": time.time(),
                    "content_id": content.content_id,
                    "topic": content.topic,
                    "format": content.format.value,
                    "platforms": platforms,
                    "initial_engagement": content.engagement_score,
                }
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"❌ Error logging post: {e}")

    async def update_with_engagement(
        self,
        content_id: str,
        views: int,
        likes: int,
        comments: int,
    ) -> None:
        """Update content with engagement metrics and learn."""
        if content_id not in self.generated_content:
            return

        content = self.generated_content[content_id]
        content.views = views
        content.likes = likes
        content.comments = comments

        metrics = content.engagement_metrics
        engagement_rate = metrics["engagement_rate"]

        print(f"\n📈 {content.topic}")
        print(f"   Views: {views}")
        print(f"   Engagement: {engagement_rate:.2%}")

        # Update learning model
        self._learn_from_engagement(content, engagement_rate)

    def _learn_from_engagement(
        self,
        content: GeneratedContent,
        engagement_rate: float,
    ) -> None:
        """Learn from engagement to improve future content."""
        model = self.learning_model

        # Track format performance
        fmt = content.format.value
        if fmt not in model["best_formats"]:
            model["best_formats"][fmt] = 0

        model["best_formats"][fmt] = (
            model["best_formats"][fmt] * 0.7 + engagement_rate * 100 * 0.3
        )

        # Track topic performance
        topic = content.topic
        if topic not in model["topic_performance"]:
            model["topic_performance"][topic] = 0

        model["topic_performance"][topic] = engagement_rate * 100

        # Increment learning iteration
        model["iterations"] += 1

        # Save updated model
        self._save_learning_model()

        print(f"   ✓ Learning updated ({model['iterations']} iterations)")

    def get_insights(self) -> Dict[str, Any]:
        """Get insights from learning model."""
        model = self.learning_model

        insights = {
            "total_iterations": model["iterations"],
            "best_format": max(
                model["best_formats"].items(),
                key=lambda x: x[1],
                default=("unknown", 0),
            ),
            "best_topic": max(
                model["topic_performance"].items(),
                key=lambda x: x[1],
                default=("unknown", 0),
            ),
            "top_3_formats": sorted(
                model["best_formats"].items(),
                key=lambda x: x[1],
                reverse=True,
            )[:3],
            "content_generated": len(self.generated_content),
            "content_posted": len([c for c in self.generated_content.values() if c.posted]),
        }

        return insights


# ─── Continuous Content Generation Loop ──────────────────────────────────

async def run_content_engine(hours: float = 24) -> None:
    """Run self-improving content engine."""
    engine = SelfImprovingContentEngine()

    print("\n" + "=" * 60)
    print("🎬 Self-Improving Content Engine Started")
    print("=" * 60 + "\n")

    start_time = time.time()

    try:
        while True:
            elapsed = (time.time() - start_time) / 3600

            if elapsed > hours:
                print(f"⏱️  Runtime limit reached ({elapsed:.1f}h)")
                break

            # Step 1: Analyze trends
            ideas = await engine.analyze_trends()
            print(f"\n📊 Found {len(ideas)} trending topics\n")

            # Step 2: Generate content variations
            for idea in ideas[:2]:  # Top 2 trends
                contents = await engine.generate_content(idea, variations=2)

                # Step 3: Post to platforms
                for content in contents:
                    await engine.post_all_platforms(content)

            # Step 4: Simulate engagement data (in production, would fetch real data)
            for content in list(engine.generated_content.values())[-5:]:
                import random

                views = random.randint(1000, 50000)
                likes = int(views * random.uniform(0.02, 0.1))
                comments = int(views * random.uniform(0.001, 0.03))

                await engine.update_with_engagement(
                    content.content_id,
                    views,
                    likes,
                    comments,
                )

            # Step 5: Show insights
            insights = engine.get_insights()
            print(f"\n💡 Insights: {json.dumps(insights, indent=2)}\n")

            # Wait before next cycle
            print("⏳ Waiting before next content batch...\n")
            await asyncio.sleep(300)  # 5 minutes

    except KeyboardInterrupt:
        print("\n⏹️  Content engine stopped")
    finally:
        print("✓ Engine shut down cleanly")


if __name__ == "__main__":
    import sys

    hours = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
    asyncio.run(run_content_engine(hours))
