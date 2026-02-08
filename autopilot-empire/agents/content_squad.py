#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════
AUTOPILOT EMPIRE - Content Squad
Maurice's AI Business System - Content Generation Service
═══════════════════════════════════════════════════════════════

Content Master Agent + Worker Agents
Generiert kontinuierlich viralen Content für:
- TikTok (15 Videos/Tag)
- YouTube Shorts (5/Tag)
- Twitter Threads (3/Tag)

"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, List
import aiohttp

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama-master:11434")
CONTENT_MODEL = "qwen2.5"  # Multilingual & Creative

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/content.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# CONTENT TEMPLATES
# ═══════════════════════════════════════════════════════════════

TIKTOK_HOOKS = [
    "This AI tool makes me €100/day...",
    "Nobody talks about this AI secret...",
    "I automated my income with this...",
    "POV: You discover AI in 2026...",
    "This changed everything for me...",
]

TOPICS = [
    "AI automation for beginners",
    "Making money with ChatGPT",
    "Building an AI empire",
    "Passive income with AI",
    "Free AI tools that print money",
    "AI business ideas 2026",
    "Automating everything with AI",
    "AI side hustles that work",
]

# ═══════════════════════════════════════════════════════════════
# OLLAMA CLIENT
# ═══════════════════════════════════════════════════════════════

async def generate_with_ollama(prompt: str, system: str = "") -> str:
    """Generate content with Ollama"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{OLLAMA_HOST}/api/generate"
            payload = {
                "model": CONTENT_MODEL,
                "prompt": prompt,
                "system": system,
                "stream": False
            }
            
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("response", "")
                else:
                    logger.error(f"Ollama Error: {response.status}")
                    return ""
    except Exception as e:
        logger.error(f"Generate Error: {e}")
        return ""

# ═══════════════════════════════════════════════════════════════
# CONTENT GENERATORS
# ═══════════════════════════════════════════════════════════════

async def generate_tiktok_script(topic: str, hook: str) -> Dict:
    """Generiert TikTok Video Script"""
    prompt = f"""
Create a viral TikTok script (30-60 seconds) about: {topic}

HOOK (first 3 seconds): {hook}

Structure:
1. Hook (3 sec) - grab attention immediately
2. Problem (5 sec) - what people struggle with
3. Solution (15 sec) - your AI method/tool
4. Proof (10 sec) - results/benefits
5. CTA (7 sec) - follow for more tips

Make it conversational, energetic, and value-packed.
Include: pause moments, emphasis words, and viral phrases.
"""
    
    system = "You are a viral TikTok content creator. Create engaging, hook-optimized scripts."
    script = await generate_with_ollama(prompt, system)
    
    return {
        "platform": "tiktok",
        "topic": topic,
        "hook": hook,
        "script": script,
        "estimated_duration": "45s",
        "viral_score": 8
    }

async def generate_youtube_short(topic: str) -> Dict:
    """Generiert YouTube Shorts Script"""
    prompt = f"""
Create a YouTube Shorts script (60 seconds) about: {topic}

Structure:
1. Pattern Interrupt (0-3s) - shocking statement
2. Value Delivery (3-45s) - main content with 3-5 key points
3. Strong CTA (45-60s) - subscribe + like + comment

Include:
- B-roll suggestions
- Text overlay ideas
- Thumbnail concept
- Keywords for SEO
"""
    
    system = "You are a YouTube Shorts expert. Create high-retention content."
    script = await generate_with_ollama(prompt, system)
    
    return {
        "platform": "youtube_shorts",
        "topic": topic,
        "script": script,
        "duration": "60s",
        "viral_score": 7
    }

async def generate_twitter_thread(topic: str) -> Dict:
    """Generiert Twitter Thread"""
    prompt = f"""
Create a viral Twitter thread (7 tweets) about: {topic}

Tweet 1 (Hook): Bold statement + thread announcement 🧵
Tweets 2-6: Value bombs - one insight per tweet
Tweet 7: Summary + CTA (follow for more)

Rules:
- Max 280 characters per tweet
- Use emojis strategically
- Include line breaks
- Add hashtags only in last tweet
- Make each tweet standalone valuable
"""
    
    system = "You are a Twitter growth expert. Create engaging threads."
    thread = await generate_with_ollama(prompt, system)
    
    return {
        "platform": "twitter",
        "topic": topic,
        "thread": thread,
        "tweet_count": 7,
        "viral_score": 8
    }

# ═══════════════════════════════════════════════════════════════
# CONTENT GENERATION LOOP
# ═══════════════════════════════════════════════════════════════

async def content_generation_loop():
    """Main content generation loop"""
    logger.info("✍️  Content Squad started - Generating viral content 24/7")
    
    cycle = 0
    
    while True:
        try:
            cycle += 1
            logger.info(f"\n{'='*60}")
            logger.info(f"Content Generation Cycle #{cycle} - {datetime.now()}")
            logger.info(f"{'='*60}\n")
            
            # TikTok Scripts (3 per cycle)
            logger.info("📱 Generating TikTok Scripts...")
            tiktok_tasks = []
            for i in range(3):
                topic = TOPICS[cycle % len(TOPICS)]
                hook = TIKTOK_HOOKS[i % len(TIKTOK_HOOKS)]
                tiktok_tasks.append(generate_tiktok_script(topic, hook))
            
            tiktok_scripts = await asyncio.gather(*tiktok_tasks)
            logger.info(f"✅ Generated {len(tiktok_scripts)} TikTok scripts")
            
            # YouTube Shorts (1 per cycle)
            logger.info("🎥 Generating YouTube Short...")
            yt_short = await generate_youtube_short(TOPICS[(cycle + 1) % len(TOPICS)])
            logger.info(f"✅ Generated YouTube Short: {yt_short['topic'][:50]}...")
            
            # Twitter Thread (1 per cycle)
            logger.info("🐦 Generating Twitter Thread...")
            twitter = await generate_twitter_thread(TOPICS[(cycle + 2) % len(TOPICS)])
            logger.info(f"✅ Generated Twitter Thread: {twitter['topic'][:50]}...")
            
            # TODO: Store in database
            # TODO: Auto-post if APIs available
            
            logger.info(f"\n✅ Cycle #{cycle} completed. Content generated:")
            logger.info(f"  - {len(tiktok_scripts)} TikTok scripts")
            logger.info(f"  - 1 YouTube Short")
            logger.info(f"  - 1 Twitter Thread")
            logger.info(f"\nWaiting 15 minutes for next cycle...\n")
            
            await asyncio.sleep(900)  # 15 Minuten
            
        except Exception as e:
            logger.error(f"❌ Content Generation Error: {e}")
            await asyncio.sleep(60)

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

async def main():
    """Main entry point"""
    logger.info("🚀 Content Squad initializing...")
    
    # Check Ollama connection
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{OLLAMA_HOST}/api/tags") as response:
                if response.status == 200:
                    logger.info("✅ Ollama connected")
                else:
                    logger.error("❌ Ollama not available")
                    return
    except Exception as e:
        logger.error(f"❌ Ollama connection failed: {e}")
        return
    
    # Start generation loop
    await content_generation_loop()

if __name__ == "__main__":
    asyncio.run(main())
