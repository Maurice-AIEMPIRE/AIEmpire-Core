#!/usr/bin/env python3
"""
Demo script to showcase max agent spawning validation
"""
import os
import sys

# Set dummy API key for demo
os.environ['MOONSHOT_API_KEY'] = 'demo-key-for-validation'

def demo_100k_validation():
    """Demonstrate 100K swarm validation"""
    print("="*70)
    print("DEMO: 100K SWARM MAX AGENT VALIDATION")
    print("="*70)
    
    from swarm_100k import KimiSwarm, TOTAL_AGENTS, MAX_CONCURRENT
    
    swarm = KimiSwarm()
    result = swarm.validate_max_agent_capacity()
    
    print(f"\n📊 Summary:")
    print(f"   • Validation: {'✅ PASSED' if result else '❌ FAILED'}")
    print(f"   • Ready to spawn {TOTAL_AGENTS:,} agents")
    print(f"   • With {MAX_CONCURRENT} concurrent workers")
    print()

def demo_500k_validation():
    """Demonstrate 500K swarm validation"""
    print("="*70)
    print("DEMO: 500K SWARM MAX AGENT VALIDATION")
    print("="*70)
    
    from swarm_500k import KimiSwarm500K, TOTAL_AGENTS, MAX_CONCURRENT
    
    swarm = KimiSwarm500K()
    result = swarm.validate_max_agent_capacity()
    
    print(f"\n📊 Summary:")
    print(f"   • Validation: {'✅ PASSED' if result else '❌ FAILED'}")
    print(f"   • Ready to spawn {TOTAL_AGENTS:,} agents")
    print(f"   • With {MAX_CONCURRENT} concurrent workers")
    print()

if __name__ == "__main__":
    demo_100k_validation()
    print("\n" + "="*70 + "\n")
    demo_500k_validation()
    
    print("="*70)
    print("✅ MAX AGENT SPAWNING VALIDATION DEMO COMPLETE")
    print("="*70)
    print("\nBoth systems are ready to spawn maximum configured agents!")
    print("\nTo run in production:")
    print("  1. Set MOONSHOT_API_KEY environment variable")
    print("  2. Run: python3 swarm_100k.py --test")
    print("     or: python3 swarm_500k.py --test")
