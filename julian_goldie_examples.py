#!/usr/bin/env python3
"""
JULIAN GOLDIE CONTENT INTEGRATION
Integration examples for Maurice's AI Empire systems
"""

import asyncio
import sys
from pathlib import Path

# Add paths for integration
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent / "x-lead-machine"))

from julian_goldie_content_generator import JulianGoldieContentGenerator


async def example_1_daily_x_content():
    """
    Example 1: Generate daily X/Twitter content using Julian's strategies
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: Daily X Content with GEO Principles")
    print("="*70 + "\n")
    
    generator = JulianGoldieContentGenerator()
    
    # Generate GEO-optimized tweet thread
    content = await generator.generate_multi_platform_content(
        core_topic="5 AI Tools That Saved Me 20 Hours This Week",
        platforms=["twitter"]
    )
    
    print("📱 Generated Twitter Content:")
    print("-" * 70)
    print(content["platforms"]["twitter"])
    print("-" * 70)
    print(f"\n✅ Strategy applied: {content['strategy']}")
    print(f"📊 Cross-promotion plan: {content['cross_promotion']['approach']}")
    

async def example_2_linkedin_authority():
    """
    Example 2: Create LinkedIn authority post
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: LinkedIn Authority Building")
    print("="*70 + "\n")
    
    generator = JulianGoldieContentGenerator()
    
    # Generate LinkedIn thought leadership post
    content = await generator.generate_multi_platform_content(
        core_topic="Why 90% of AI Automation Projects Fail (And How to Be in the 10%)",
        platforms=["linkedin"]
    )
    
    print("💼 Generated LinkedIn Content:")
    print("-" * 70)
    print(content["platforms"]["linkedin"])
    print("-" * 70)
    

async def example_3_geo_blog_post():
    """
    Example 3: Create GEO-optimized blog post for AI citations
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: GEO-Optimized Blog Post")
    print("="*70 + "\n")
    
    generator = JulianGoldieContentGenerator()
    
    # Generate citation-worthy blog content
    content = await generator.generate_geo_optimized_content(
        topic="The Complete Guide to AI Automation for Small Business in 2026",
        target_keyword="AI automation small business 2026"
    )
    
    print("📝 Generated GEO Content Preview:")
    print("-" * 70)
    # Show first 500 chars
    print(content["content"][:500] + "...")
    print("-" * 70)
    print(f"\n✅ Optimization Strategy: {content['strategy']}")
    print(f"🎯 Target Keyword: {content['keyword']}")
    print("\n📋 GEO Principles Applied:")
    for principle in content["principles"]:
        print(f"   - {principle}")
    

async def example_4_complete_workflow():
    """
    Example 4: Generate complete AI SEO workflow for a business niche
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: Complete AI SEO Workflow")
    print("="*70 + "\n")
    
    generator = JulianGoldieContentGenerator()
    
    # Generate complete workflow
    workflow = await generator.generate_ai_seo_workflow(
        business_niche="AI Automation Agency"
    )
    
    print("🔄 Generated AI SEO Workflow Preview:")
    print("-" * 70)
    # Show first 800 chars
    print(workflow["workflow"][:800] + "...")
    print("-" * 70)
    print(f"\n✅ Workflow Strategy: {workflow['strategy']}")
    print(f"🎯 Niche: {workflow['niche']}")
    print(f"📚 Based on: {workflow['based_on']}")
    

async def example_5_multi_platform_campaign():
    """
    Example 5: Create complete multi-platform campaign
    """
    print("\n" + "="*70)
    print("EXAMPLE 5: Multi-Platform Campaign")
    print("="*70 + "\n")
    
    generator = JulianGoldieContentGenerator()
    
    # Generate content for all platforms
    campaign = await generator.generate_multi_platform_content(
        core_topic="I Replaced My Entire Marketing Team with AI (Here's What Happened)",
        platforms=["twitter", "linkedin", "reddit", "youtube"]
    )
    
    print("🌐 Multi-Platform Campaign Generated:")
    print("-" * 70)
    for platform, content in campaign["platforms"].items():
        print(f"\n📱 {platform.upper()}:")
        print(content[:200] + "...")
        print()
    print("-" * 70)
    print(f"\n✅ Strategy: {campaign['strategy']}")
    print("\n📊 Cross-Promotion Plan:")
    for step in campaign['cross_promotion']['strategy']:
        print(f"   - {step}")
    

async def example_6_weekly_content_plan():
    """
    Example 6: Generate weekly content plan with Julian's principles
    """
    print("\n" + "="*70)
    print("EXAMPLE 6: Weekly Content Plan")
    print("="*70 + "\n")
    
    generator = JulianGoldieContentGenerator()
    
    # Week's worth of content topics
    weekly_topics = [
        ("Monday: Case Study", "How I Generated $10K MRR with AI Automation"),
        ("Wednesday: Tutorial", "Setting Up Your First AI Agent Swarm"),
        ("Friday: Controversial", "Why Most AI Tools Are Useless (And Which Ones Aren't)"),
    ]
    
    print("📅 Generating Weekly Content Plan...\n")
    
    for day_topic, topic in weekly_topics:
        print(f"📌 {day_topic}")
        content = await generator.generate_multi_platform_content(
            core_topic=topic,
            platforms=["twitter"]
        )
        print(f"   Strategy: GEO + Multi-Platform")
        print(f"   Preview: {content['platforms']['twitter'][:100]}...")
        print()
    
    print("-" * 70)
    print("✅ Weekly plan complete!")
    print("💡 Each piece optimized for AI citations and multi-platform distribution")
    

async def run_all_examples():
    """Run all integration examples"""
    
    print("\n" + "="*70)
    print("JULIAN GOLDIE CONTENT INTEGRATION EXAMPLES")
    print("For Maurice's AI Empire")
    print("="*70)
    
    examples = [
        ("Daily X Content", example_1_daily_x_content),
        ("LinkedIn Authority", example_2_linkedin_authority),
        ("GEO Blog Post", example_3_geo_blog_post),
        ("Complete Workflow", example_4_complete_workflow),
        ("Multi-Platform Campaign", example_5_multi_platform_campaign),
        ("Weekly Content Plan", example_6_weekly_content_plan),
    ]
    
    print("\nAvailable Examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"{i}. {name}")
    print(f"{len(examples) + 1}. Run All Examples")
    print()
    
    choice = input("Select example (1-7): ").strip()
    
    if choice == str(len(examples) + 1):
        # Run all
        for name, example_func in examples:
            await example_func()
            input("\nPress Enter to continue to next example...")
    elif choice.isdigit() and 1 <= int(choice) <= len(examples):
        # Run selected example
        _, example_func = examples[int(choice) - 1]
        await example_func()
    else:
        print("Invalid choice. Running Example 1...")
        await example_1_daily_x_content()
    
    print("\n" + "="*70)
    print("✅ EXAMPLES COMPLETE")
    print("="*70)
    print("\nNext Steps:")
    print("1. Review generated content in julian_goldie_content/ directory")
    print("2. Customize the generators for your specific needs")
    print("3. Integrate with X Auto Poster and other systems")
    print("4. Monitor AI citation rates and iterate")
    print("\n💡 Remember: Optimize for AI citations, not just rankings!")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(run_all_examples())
    except KeyboardInterrupt:
        print("\n\n⚠️  Examples interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
