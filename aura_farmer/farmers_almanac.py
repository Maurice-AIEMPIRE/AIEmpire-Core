#!/usr/bin/env python3
"""
FARMER'S ALMANAC (Aura Farmer Manager)
The central command for the Aura Farmer TikTok Automation.
"""

import os
import time
import random
import logging
from pathlib import Path
from trend_scout import TrendScout
from content_engine import ContentEngine

# --- Configuration ---
BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp"

# Ensure directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Logger setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AuraFarmer:
    def __init__(self):
        self.scout = TrendScout()
        self.engine = ContentEngine(ASSETS_DIR, TEMP_DIR, OUTPUT_DIR)

    def daily_harvest(self, count=1):
        """Generates 'count' videos."""
        logger.info(f"🌾 Starting Harvest: {count} videos planned.")
        
        for i in range(count):
            logger.info(f"--- Processing Video {i+1}/{count} ---")
            
            # 1. Scout Trend
            topic = self.scout.get_hot_topic()
            logger.info(f"🔥 Trend Found: {topic}")
            
            # 2. Generate Content
            try:
                video_path = self.engine.produce_video(topic)
                if video_path:
                    logger.info(f"✅ Harvested: {video_path}")
                else:
                    logger.error("❌ Failed to produce video.")
            except Exception as e:
                logger.error(f"❌ Critical Error: {e}")

            # 3. Rest (to avoid rate limits or CPU overload)
            time.sleep(2)

if __name__ == "__main__":
    farmer = AuraFarmer()
    # In a real scenario, this might run on a schedule or loop
    # For now, we run 1 harvest cycle
    farmer.daily_harvest(count=1)
