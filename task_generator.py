#!/usr/bin/env python3
"""
AUTOMATIC TASK GENERATOR
Generates diverse tasks automatically for the AI Empire team
Uses open source tools and AI APIs to create work for 12+ hours
Maurice's AI Empire - 2026
"""

import yaml
import os
from pathlib import Path
from datetime import datetime
import random

MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY", "")
TASKS_DIR = Path(__file__).parent / "atomic-reactor" / "tasks"

# Concrete task definitions for different categories
TASK_DEFINITIONS = [
    # Content tasks (High ROI)
    {
        "title": "Generate 20 X/Twitter posts about AI automation",
        "type": "content",
        "priority": "high",
        "time": 2,
        "objective": "Create engaging X/Twitter content that drives engagement and generates leads for AI Empire services.",
        "prompts": ["Generate 20 X/Twitter posts about AI automation. Mix educational, controversial, and behind-the-scenes content. Include hooks and CTAs. Format as numbered list."]
    },
    {
        "title": "Create 7-day LinkedIn content calendar for BMA automation",
        "type": "content",
        "priority": "high",
        "time": 3,
        "objective": "Develop a week of LinkedIn content targeting fire alarm system professionals.",
        "prompts": ["Create a 7-day LinkedIn content calendar for BMA/fire alarm automation. Each post should target facility managers, fire safety engineers. Include DIN 14675 references."]
    },
    {
        "title": "Write 5 blog articles on OpenClaw automation",
        "type": "content",
        "priority": "medium",
        "time": 4,
        "objective": "Create SEO-optimized blog content about OpenClaw for organic traffic.",
        "prompts": ["Write 5 blog article outlines (500-1000 words each) about OpenClaw: 1) What is OpenClaw 2) Setup guide 3) vs other tools 4) Use cases 5) Monetization"]
    },
    {
        "title": "Develop viral thread templates for AI topics",
        "type": "content",
        "priority": "high",
        "time": 2,
        "objective": "Create reusable thread templates that can be customized for different AI topics.",
        "prompts": ["Create 10 viral X/Twitter thread templates for AI automation topics. Each template should have: Hook, 5-7 tweet structure, CTA. Make them fill-in-the-blank style."]
    },
    {
        "title": "Generate 30 Reddit post ideas for r/automation",
        "type": "content",
        "priority": "medium",
        "time": 2,
        "objective": "Create value-first Reddit posts that build authority and generate leads.",
        "prompts": ["Generate 30 Reddit post ideas for r/automation, r/ArtificialIntelligence, r/entrepreneur. Mix: questions, case studies, tutorials, tool comparisons. No spam."]
    },
    
    # Research tasks (Intelligence gathering)
    {
        "title": "Analyze 20 AI automation competitors pricing",
        "type": "research",
        "priority": "high",
        "time": 3,
        "objective": "Understand competitive pricing landscape to optimize our offers.",
        "prompts": ["Research 20 AI automation consultants/agencies. Find: company name, pricing model, services offered, target market, unique selling points. Format as JSON."]
    },
    {
        "title": "Find 50 hot leads on X needing AI automation",
        "type": "research",
        "priority": "high",
        "time": 2,
        "objective": "Identify potential clients actively looking for AI automation help.",
        "prompts": ["Search X/Twitter for people tweeting about: 'need automation', 'manual process killing me', 'looking for AI consultant'. Find 50 leads with username, tweet, lead score 1-10."]
    },
    {
        "title": "Research BMA automation market in Germany",
        "type": "research",
        "priority": "medium",
        "time": 4,
        "objective": "Size the German fire alarm automation market and identify key players.",
        "prompts": ["Research BMA (Brandmeldeanlage) automation market in Germany. Find: market size, key players, pain points, regulations (DIN 14675), pricing, opportunities."]
    },
    {
        "title": "Analyze 100 top keywords for AI automation SEO",
        "type": "research",
        "priority": "medium",
        "time": 3,
        "objective": "Identify high-value keywords for SEO and content strategy.",
        "prompts": ["Research 100 keywords for AI automation niche. Include: search volume estimate, difficulty, CPC, intent (commercial/informational), content angle. Format as table."]
    },
    {
        "title": "Find 20 partnership opportunities in AI space",
        "type": "research",
        "priority": "medium",
        "time": 2,
        "objective": "Identify potential partners, affiliates, or collaboration opportunities.",
        "prompts": ["Find 20 potential partners in AI/automation space: YouTubers, newsletter owners, course creators, tool builders. Include: audience size, contact info, partnership angle."]
    },
    
    # Code/Technical tasks
    {
        "title": "Build Telegram bot for GitHub issue notifications",
        "type": "code",
        "priority": "high",
        "time": 4,
        "objective": "Get real-time notifications for GitHub issues and PRs on Telegram.",
        "prompts": ["Create Python script: Telegram bot that sends notifications for new GitHub issues/PRs/comments. Use webhooks. Include setup instructions."]
    },
    {
        "title": "Create automated lead scoring script",
        "type": "code",
        "priority": "high",
        "time": 3,
        "objective": "Automatically score leads based on BANT criteria using AI.",
        "prompts": ["Build Python script: analyze lead data (company, role, tweet/message) and score 1-10 using Kimi API. Save to SQLite. Include batch processing."]
    },
    {
        "title": "Develop GitHub Actions workflow for daily reports",
        "type": "code",
        "priority": "medium",
        "time": 2,
        "objective": "Automate daily business reports via GitHub Actions.",
        "prompts": ["Create GitHub Actions workflow: runs daily at 9 AM, generates report (tasks completed, revenue, leads), posts as issue. Use Kimi API for summary."]
    },
    {
        "title": "Build CLI tool for batch content generation",
        "type": "code",
        "priority": "medium",
        "time": 4,
        "objective": "Create reusable CLI tool for generating content at scale.",
        "prompts": ["Create Python CLI tool: `aiempire content --type twitter --count 20 --topic \"AI automation\"`. Uses Kimi API, saves to files, supports templates."]
    },
    {
        "title": "Optimize Kimi API usage to reduce costs by 50%",
        "type": "code",
        "priority": "high",
        "time": 3,
        "objective": "Implement caching, batching, and smarter prompts to cut API costs.",
        "prompts": ["Analyze current Kimi API usage. Implement: response caching, request batching, prompt optimization, fallback to Ollama for simple tasks. Measure savings."]
    },
    
    # Business/Revenue tasks
    {
        "title": "Create 5 Gumroad digital products",
        "type": "business",
        "priority": "high",
        "time": 6,
        "objective": "Develop ready-to-sell digital products for immediate revenue.",
        "prompts": ["Design 5 Gumroad products: 1) OpenClaw Quick Start (€49) 2) AI Automation Blueprint (€79) 3) BMA+AI Guide (€149) 4) Docker Troubleshooting (€99) 5) Prompt Library (€29). Include outlines."]
    },
    {
        "title": "Design 3 Fiverr service packages",
        "type": "business",
        "priority": "high",
        "time": 3,
        "objective": "Create competitive Fiverr offerings for services revenue.",
        "prompts": ["Create 3 Fiverr gigs: 1) AI Automation Setup (€50/150/500) 2) SEO Content Writing (€30/80/200) 3) AI Consultation (€100/300/1000). Full descriptions, FAQ, requirements."]
    },
    {
        "title": "Develop pricing strategy for EUR 25K/month",
        "type": "business",
        "priority": "high",
        "time": 2,
        "objective": "Create pricing model across all revenue streams to hit monthly target.",
        "prompts": ["Design pricing strategy to reach €25K/month from: Gumroad products, Fiverr services, consulting, X leads. Include volume projections, conversion rates, LTV."]
    },
    {
        "title": "Plan cold outreach campaign for 100 leads",
        "type": "business",
        "priority": "medium",
        "time": 3,
        "objective": "Design and execute outreach campaign to qualified leads.",
        "prompts": ["Plan cold outreach campaign: 100 leads via X DMs and email. Include: lead criteria, message templates, follow-up sequence, tracking system, success metrics."]
    },
    {
        "title": "Create consultation offer for BMA companies",
        "type": "business",
        "priority": "high",
        "time": 4,
        "objective": "Package BMA automation consulting for German fire safety market.",
        "prompts": ["Create BMA automation consultation offer: target (facility managers, fire safety companies), pain points, solution, deliverables, pricing (€5K-50K), case study template."]
    },
    
    # Optimization tasks
    {
        "title": "Automate social media posting workflow",
        "type": "optimization",
        "priority": "high",
        "time": 3,
        "objective": "Remove manual work from social media management.",
        "prompts": ["Design automation for social posting: content generation → approval → scheduling → posting → engagement tracking. Use GitHub Actions, Kimi API, and scheduling tools."]
    },
    {
        "title": "Reduce task execution time by 30%",
        "type": "optimization",
        "priority": "medium",
        "time": 2,
        "objective": "Optimize atomic reactor task processing for faster execution.",
        "prompts": ["Analyze atomic-reactor/run_tasks.py. Optimize: parallel task execution, faster API calls, better error handling, progress reporting. Measure before/after."]
    },
    {
        "title": "Automate revenue tracking and reporting",
        "type": "optimization",
        "priority": "high",
        "time": 3,
        "objective": "Get real-time revenue visibility without manual work.",
        "prompts": ["Build automated revenue tracker: Gumroad API, Fiverr scraping, manual entry form → SQLite → daily dashboard → alerts. GitHub Actions for automation."]
    },
    {
        "title": "Optimize GitHub Actions workflow costs",
        "type": "optimization",
        "priority": "medium",
        "time": 2,
        "objective": "Reduce GitHub Actions minutes usage while maintaining functionality.",
        "prompts": ["Audit .github/workflows/ for optimization: consolidate workflows, reduce run frequency, use caching, implement conditional execution. Calculate savings."]
    },
    {
        "title": "Implement automated lead qualification pipeline",
        "type": "optimization",
        "priority": "high",
        "time": 4,
        "objective": "Automatically score, route, and nurture leads without manual intervention.",
        "prompts": ["Design lead pipeline: capture (X/form) → score (BANT via AI) → route (high=sales, low=nurture) → auto-follow-up → CRM update. Build with Python + GitHub Actions."]
    },
]


class TaskGenerator:
    """Automatic task generator for AI Empire."""
    
    def __init__(self):
        self.task_counter = self._get_next_task_number()
    
    def _get_next_task_number(self) -> int:
        """Get the next task number based on existing tasks."""
        existing_tasks = list(TASKS_DIR.glob("T-*.yaml"))
        if not existing_tasks:
            # No existing tasks, start from 1 (or 6 if there are 5 pre-existing tasks)
            return 6
        
        numbers = []
        for task in existing_tasks:
            try:
                num = int(task.stem.split('-')[1])
                numbers.append(num)
            except (IndexError, ValueError):
                continue
        
        return max(numbers, default=5) + 1
    
    def create_task_from_definition(self, task_def: dict) -> dict:
        """Create a task from a definition."""
        task_id = f"T-{self.task_counter:03d}"
        self.task_counter += 1
        
        task = {
            "id": task_id,
            "title": task_def["title"],
            "type": task_def["type"],
            "priority": task_def["priority"],
            "model": "kimi",
            "estimated_time": f"{task_def['time']} hours",
            "objective": task_def["objective"],
            "prompts": task_def["prompts"],
            "acceptance": [
                "Task completed within estimated time",
                "Output meets quality standards",
                "Results documented and saved",
                "Next steps identified"
            ],
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "auto_generated": True,
                "category": task_def["type"]
            }
        }
        
        return task
    
    def save_task(self, task: dict):
        """Save task to YAML file."""
        TASKS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Clean title for filename
        clean_title = task['title'][:40].lower()
        clean_title = clean_title.replace(' ', '-').replace('/', '-')
        # Remove any remaining special characters
        clean_title = ''.join(c for c in clean_title if c.isalnum() or c in ('-', '_'))
        
        task_file = TASKS_DIR / f"{task['id']}-{clean_title}.yaml"
        
        with open(task_file, 'w') as f:
            yaml.dump(task, f, default_flow_style=False, allow_unicode=True)
        
        return task_file
    
    def generate_tasks(self, count: int = 25) -> list:
        """Generate tasks from predefined definitions."""
        tasks = []
        
        # Shuffle task definitions for variety
        task_defs = random.sample(TASK_DEFINITIONS, min(count, len(TASK_DEFINITIONS)))
        
        for task_def in task_defs:
            task = self.create_task_from_definition(task_def)
            task_file = self.save_task(task)
            tasks.append({
                "task": task,
                "file": task_file.name
            })
        
        return tasks


async def main():
    """Generate tasks automatically."""
    print("=" * 70)
    print("AI EMPIRE - AUTOMATIC TASK GENERATOR")
    print("=" * 70)
    print()
    
    # Check for API key (optional, for future AI-powered generation)
    if not MOONSHOT_API_KEY:
        print("⚠️  MOONSHOT_API_KEY not set - AI-powered generation disabled")
        print("   Using predefined task templates instead")
        print()
    
    generator = TaskGenerator()
    
    # Generate 25 tasks (approximately 12-15 hours of work)
    count = min(25, len(TASK_DEFINITIONS))
    print(f"Generating {count} diverse tasks...")
    print()
    
    tasks = generator.generate_tasks(count=count)
    
    # Summary
    print("=" * 70)
    print("TASK GENERATION COMPLETE")
    print("=" * 70)
    print(f"Total tasks generated: {len(tasks)}")
    print()
    
    # Group by category
    by_category = {}
    for item in tasks:
        category = item["task"]["type"]
        if category not in by_category:
            by_category[category] = []
        by_category[category].append({
            "title": item["task"]["title"],
            "time": item["task"]["estimated_time"],
            "priority": item["task"]["priority"]
        })
    
    for category, task_list in sorted(by_category.items()):
        print(f"\n{category.upper()} ({len(task_list)} tasks):")
        for t in task_list:
            priority_icon = "🔥" if t["priority"] == "high" else "📋"
            print(f"  {priority_icon} {t['title']} ({t['time']})")
    
    print()
    print(f"All tasks saved to: {TASKS_DIR}")
    print()
    print("Next steps:")
    print("1. Review generated tasks")
    print("2. Run: python3 atomic-reactor/run_tasks.py")
    print("3. Check reports in atomic-reactor/reports/")
    print()
    
    # Estimate total work time
    total_hours = sum(
        int(item["task"]["estimated_time"].split()[0])
        for item in tasks
    )
    print(f"📊 Estimated total work time: {total_hours} hours")
    print()
    
    # Show high priority tasks
    high_priority = [
        item for item in tasks
        if item["task"]["priority"] == "high"
    ]
    print(f"🔥 High priority tasks: {len(high_priority)}/{len(tasks)}")
    print()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
