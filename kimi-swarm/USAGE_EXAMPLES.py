#!/usr/bin/env python3
"""
EXAMPLE USAGE: 500K Swarm with Claude Orchestration
Demonstrates different use cases and configurations
"""

import asyncio

# Example 1: Basic Test Run (100 tasks)
async def example_test_run():
    """Quick test to verify everything works."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Test Run (100 tasks)")
    print("="*60)
    print("Purpose: Quick validation, minimal cost (~$0.05)")
    print("Command: python3 swarm_500k.py --test")
    print()
    print("This will:")
    print("  - Execute 100 tasks across all task types")
    print("  - Create sample outputs in output_500k/")
    print("  - Test the full pipeline including Claude orchestration")
    print("  - Cost: ~$0.05")
    print("  - Time: ~1-2 minutes")
    print()

# Example 2: Lead Generation Sprint
async def example_lead_generation():
    """Generate high-value B2B leads."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Lead Generation Sprint (5,000 tasks)")
    print("="*60)
    print("Purpose: Generate qualified B2B leads")
    print("Command: python3 swarm_500k.py -n 5000")
    print()
    print("Expected Output:")
    print("  - ~1,250 high-value lead profiles (BANT scored)")
    print("  - Pipeline Value: ~€30M")
    print("  - Cost: ~$2.50")
    print("  - Time: ~5-8 minutes")
    print()
    print("Use Case: Fill sales pipeline for outbound campaigns")
    print()

# Example 3: Content Factory
async def example_content_factory():
    """Generate viral content ideas."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Content Factory (10,000 tasks)")
    print("="*60)
    print("Purpose: Mass content creation")
    print("Command: python3 swarm_500k.py -n 10000")
    print()
    print("Expected Output:")
    print("  - ~2,500 viral content ideas")
    print("  - Ready-to-post X/Twitter threads, hooks, CTAs")
    print("  - Cost: ~$5.00")
    print("  - Time: ~10-15 minutes")
    print()
    print("Use Case: Build 3-month content calendar")
    print()

# Example 4: Market Intelligence
async def example_market_intelligence():
    """Comprehensive market and competitor analysis."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Market Intelligence (20,000 tasks)")
    print("="*60)
    print("Purpose: Complete market mapping")
    print("Command: python3 swarm_500k.py -n 20000")
    print()
    print("Expected Output:")
    print("  - ~3,000 competitor profiles")
    print("  - ~3,000 gold nuggets (business insights)")
    print("  - ~3,000 revenue optimization ideas")
    print("  - Cost: ~$10.00")
    print("  - Time: ~20-30 minutes")
    print()
    print("Use Case: Strategic planning, competitive positioning")
    print()

# Example 5: Full Scale Run (WARNING: Expensive)
async def example_full_scale():
    """Full 500K run - maximum scale."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Full Scale (500,000 tasks) ⚠️")
    print("="*60)
    print("Purpose: Maximum scale deployment")
    print("Command: python3 swarm_500k.py --full")
    print()
    print("⚠️  WARNING: This is expensive!")
    print()
    print("Expected Output:")
    print("  - 125,000+ high-value leads")
    print("  - 125,000+ content pieces")
    print("  - 75,000+ gold nuggets")
    print("  - 75,000+ revenue optimization ideas")
    print("  - Pipeline Value: €3+ BILLION")
    print("  - Cost: ~$250 (yes, two hundred fifty dollars)")
    print("  - Time: ~60-90 minutes")
    print()
    print("Use Case: Only for serious production runs")
    print("Recommendation: Start smaller and scale up")
    print()

# Example 6: Custom Configuration
async def example_custom_config():
    """How to customize the swarm."""
    print("\n" + "="*60)
    print("EXAMPLE 6: Custom Configuration")
    print("="*60)
    print()
    print("To customize behavior, edit swarm_500k.py:")
    print()
    print("# Adjust concurrency (line ~25)")
    print("MAX_CONCURRENT = 200  # Lower for stricter rate limits")
    print()
    print("# Change budget (line ~27)")
    print("BUDGET_USD = 30.0  # Set your budget limit")
    print()
    print("# Modify task weights for priority (in run_swarm method)")
    print("self.task_weights = [2.0, 1.0, 0.5, 2.0, 1.5, 1.0]")
    print("# [leads, content, competitors, nuggets, rev_ops, partnerships]")
    print()

# Example 7: Processing Results
async def example_process_results():
    """How to process the output."""
    print("\n" + "="*60)
    print("EXAMPLE 7: Processing Results")
    print("="*60)
    print()
    print("Results are saved in: output_500k/")
    print()
    print("Structure:")
    print("  output_500k/")
    print("  ├── leads/                    # B2B lead profiles (JSON)")
    print("  ├── content/                  # Content ideas (JSON)")
    print("  ├── competitors/              # Competitor analysis (JSON)")
    print("  ├── gold_nuggets/             # Business insights (JSON)")
    print("  ├── revenue_operations/       # Revenue optimizations (JSON)")
    print("  ├── claude_insights/          # Strategic analysis (JSON)")
    print("  └── stats_500k_*.json         # Run statistics")
    print()
    print("Example: Load and analyze leads")
    print()
    print("import json")
    print("from pathlib import Path")
    print()
    print("leads_dir = Path('output_500k/leads')")
    print("high_priority_leads = []")
    print()
    print("for lead_file in leads_dir.glob('*.json'):")
    print("    with open(lead_file) as f:")
    print("        lead = json.load(f)")
    print("        if lead['data'].get('bant_score', 0) >= 8:")
    print("            high_priority_leads.append(lead)")
    print()
    print("print(f'Found {len(high_priority_leads)} high-priority leads')")
    print()

# Example 8: Integration with CRM
async def example_crm_integration():
    """How to integrate with the CRM."""
    print("\n" + "="*60)
    print("EXAMPLE 8: CRM Integration")
    print("="*60)
    print()
    print("Import leads into CRM V2:")
    print()
    print("import json")
    print("import requests")
    print("from pathlib import Path")
    print()
    print("CRM_URL = 'http://localhost:3500/api/leads'")
    print()
    print("leads_dir = Path('output_500k/leads')")
    print("for lead_file in leads_dir.glob('*.json'):")
    print("    with open(lead_file) as f:")
    print("        lead_data = json.load(f)['data']")
    print("        ")
    print("        # Convert to CRM format")
    print("        crm_lead = {")
    print("            'name': lead_data['company'],")
    print("            'contact': lead_data['handle'],")
    print("            'industry': lead_data['industry'],")
    print("            'budget': lead_data.get('estimated_project_value'),")
    print("            'authority': 'high',")
    print("            'need': lead_data['ai_opportunity'],")
    print("            'timeline': 'Q1 2026',")
    print("            'bant_score': lead_data.get('bant_score', 7)")
    print("        }")
    print("        ")
    print("        # POST to CRM")
    print("        requests.post(CRM_URL, json=crm_lead)")
    print()

# Main Examples Runner
async def show_all_examples():
    """Show all examples."""
    print("\n" + "="*80)
    print(" "*20 + "500K KIMI SWARM - USAGE EXAMPLES")
    print("="*80)
    
    examples = [
        example_test_run,
        example_lead_generation,
        example_content_factory,
        example_market_intelligence,
        example_full_scale,
        example_custom_config,
        example_process_results,
        example_crm_integration,
    ]
    
    for example in examples:
        await example()
    
    print("\n" + "="*80)
    print("GETTING STARTED")
    print("="*80)
    print()
    print("1. Set your API key:")
    print("   export MOONSHOT_API_KEY='your-kimi-api-key'")
    print()
    print("2. Optional: Add Claude for enhanced orchestration")
    print("   export ANTHROPIC_API_KEY='your-claude-api-key'")
    print()
    print("3. Run a test:")
    print("   python3 swarm_500k.py --test")
    print()
    print("4. Review outputs:")
    print("   ls -la output_500k/*/")
    print()
    print("5. Scale up:")
    print("   python3 swarm_500k.py -n 5000")
    print()
    print("="*80)
    print()
    print("For detailed documentation, see:")
    print("  - README_500K_SWARM.md")
    print("  - CLAUDE_ORCHESTRATOR_CONFIG.md")
    print()
    print("Questions? Check the troubleshooting section in README.")
    print()
    print("="*80)
    print()

if __name__ == "__main__":
    asyncio.run(show_all_examples())
