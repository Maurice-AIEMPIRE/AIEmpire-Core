#!/usr/bin/env python3
"""
X (TWITTER) AUTO POSTER
Automated posting to X/Twitter with scheduling
Maurice's AI Empire - 2026
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# This would use Twitter API v2
# For now, creates posts in a queue for manual posting
# Future: Integrate with Twitter API when credentials available

TWITTER_API_KEY = os.getenv("TWITTER_API_KEY", "")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET", "")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET", "")
MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY", "")


class XAutoPoster:
    """Automated X/Twitter posting system."""

    def __init__(self):
        self.queue_file = Path(__file__).parent / "x_post_queue.json"
        self.load_queue()

    def load_queue(self):
        """Load post queue."""
        if self.queue_file.exists():
            with open(self.queue_file) as f:
                self.queue = json.load(f)
        else:
            self.queue = {"pending": [], "posted": [], "scheduled": []}

    def save_queue(self):
        """Save post queue."""
        with open(self.queue_file, "w") as f:
            json.dump(self.queue, f, indent=2)

    async def generate_daily_content(self, count: int = 5) -> list:
        """Generate daily content for X."""
        import sys

        sys.path.append(str(Path(__file__).parent / "x-lead-machine"))

        from x_automation import XLeadMachine

        machine = XLeadMachine()

        # Different topics and styles for variety
        topics_styles = [
            ("AI Automation saves hours daily", "value"),
            ("Building my AI Empire in public", "behind_scenes"),
            ("Made EUR X this week with AI", "result"),
            ("How to automate your workflow", "tutorial"),
            ("Why most people fail at AI automation", "controversial"),
        ]

        posts = []
        for topic, style in topics_styles[:count]:
            content = await machine.generate_content(topic, style)
            if content:
                posts.append(
                    {
                        "content": content,
                        "topic": topic,
                        "style": style,
                        "generated_at": datetime.now().isoformat(),
                        "status": "pending",
                    }
                )

        return posts

    def schedule_posts(self, posts: list, start_time: datetime = None):
        """Schedule posts throughout the day."""
        if not start_time:
            start_time = datetime.now()

        # Optimal posting times (hours)
        posting_times = [8, 12, 17, 19, 21]  # 8am, 12pm, 5pm, 7pm, 9pm

        for i, post in enumerate(posts):
            hour = posting_times[i % len(posting_times)]
            scheduled_time = start_time.replace(hour=hour, minute=0, second=0)

            # If time already passed today, schedule for tomorrow
            if scheduled_time < datetime.now():
                scheduled_time += timedelta(days=1)

            post["scheduled_for"] = scheduled_time.isoformat()
            post["status"] = "scheduled"
            self.queue["scheduled"].append(post)

        self.save_queue()
        return len(posts)

    async def post_to_twitter(self, content: str) -> bool:
        """Post to Twitter/X (requires API credentials)."""
        if not all(
            [
                TWITTER_API_KEY,
                TWITTER_API_SECRET,
                TWITTER_ACCESS_TOKEN,
                TWITTER_ACCESS_SECRET,
            ]
        ):
            print("⚠️  Twitter API credentials not configured")
            print(f"📝 Would post: {content}")
            return False

        # Twitter API v2 posting
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.twitter.com/2/tweets",
                    headers={
                        "Authorization": f"Bearer {TWITTER_ACCESS_TOKEN}",
                        "Content-Type": "application/json",
                    },
                    json={"text": content},
                ) as resp:
                    if resp.status == 201:
                        data = await resp.json()
                        tweet_id = data.get("data", {}).get("id", "unknown")
                        print(f"Posted tweet ID: {tweet_id}")
                        return True
                    else:
                        error_text = await resp.text()
                        print(f"Twitter API error {resp.status}: {error_text[:200]}")
                        return False
        except Exception as e:
            print(f"Error posting to X: {e}")
            return False

    def create_posting_guide(self) -> str:
        """Create a guide for manual posting."""
        pending = self.queue.get("pending", [])
        scheduled = self.queue.get("scheduled", [])

        guide = "# X/Twitter Posting Guide\n\n"
        guide += f"**Generated:** {datetime.now().isoformat()}\n"
        guide += f"**Pending Posts:** {len(pending)}\n"
        guide += f"**Scheduled Posts:** {len(scheduled)}\n\n"

        guide += "## Scheduled Posts\n\n"
        for i, post in enumerate(scheduled, 1):
            scheduled_time = datetime.fromisoformat(post["scheduled_for"])
            guide += f"### Post {i} - {scheduled_time.strftime('%H:%M')}\n"
            guide += f"**Topic:** {post['topic']}\n"
            guide += f"**Style:** {post['style']}\n\n"
            guide += f"```\n{post['content']}\n```\n\n"
            guide += "---\n\n"

        guide += "## Posting Tips\n"
        guide += "- Post at scheduled times for maximum engagement\n"
        guide += "- Respond to all comments within 1 hour\n"
        guide += "- Track which posts get most engagement\n"
        guide += "- DM users who show buying signals\n\n"

        return guide

    async def run_daily_generation(self):
        """Run daily content generation."""
        print("\n" + "=" * 60)
        print("X AUTO POSTER - Daily Content Generation")
        print("=" * 60)

        # Generate posts
        print("\n📝 Generating content...")
        posts = await self.generate_daily_content(5)
        print(f"✅ Generated {len(posts)} posts")

        # Schedule posts
        print("\n📅 Scheduling posts...")
        scheduled_count = self.schedule_posts(posts)
        print(f"✅ Scheduled {scheduled_count} posts")

        # Create guide
        print("\n📄 Creating posting guide...")
        guide = self.create_posting_guide()

        # Save guide
        guide_file = Path(__file__).parent / "X_POSTING_GUIDE.md"
        with open(guide_file, "w") as f:
            f.write(guide)

        print(f"✅ Guide saved: {guide_file}")
        print("\n" + "=" * 60)
        print("✅ Daily generation complete!")
        print(f"📂 Check {guide_file} for posting schedule")
        print("=" * 60)

        return guide


async def main():
    """Main entry point."""
    poster = XAutoPoster()

    # Run daily generation
    guide = await poster.run_daily_generation()

    print("\n" + guide[:500] + "...\n")


if __name__ == "__main__":
    asyncio.run(main())
