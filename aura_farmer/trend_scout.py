"""
TREND SCOUT
Finds the hottest topics for the Aura Farmer to harvest.
"""

import random

class TrendScout:
    def __init__(self):
        self.hyped_topics = [
            "The Dark Psychology of Silence",
            "Why You Are Still Broke (It's Not Your Fault)",
            "The 3am Motivation You Need",
            "Matrix Glitches Caught on Camera",
            "Stoic Rules for a Strong Mind",
            "Financial Freedom Secrets They Hide",
            "The Art of Not Caring",
            "5 Signs Someone is Manipulating You",
            "How to Disappear Completely (Digital Ghost)",
            "The 'Monk Mode' Protocol"
        ]

    def get_hot_topic(self):
        """Returns a random hyped topic."""
        return random.choice(self.hyped_topics)
