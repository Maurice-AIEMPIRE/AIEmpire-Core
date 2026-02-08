#!/usr/bin/env python3
"""
NIGHT TASKS CONFIG - 1000 Tasks für System-Improvement
20 Kategorien × 50 Tasks = 1000 Tasks
Kimi Moonshot Swarm + 100 Claude Agents
Maurice's AI Empire - 2026
"""

# 20 Task Categories, each generating 50 task variants = 1000 total
TASK_CATEGORIES = [
    # ═══════════════════════════════════════════
    # CATEGORY 1-4: LEAD GENERATION (200 tasks)
    # ═══════════════════════════════════════════
    {
        "id": "CAT-01",
        "name": "high_value_lead_research",
        "count": 50,
        "agent": "kimi",
        "priority": "critical",
        "revenue_potential": 5000,
        "prompt": """Du bist ein Elite B2B Lead Research Agent. Generiere ein REALISTISCHES Premium-Lead-Profil.
Zielgruppe: Enterprise/Mid-Market Unternehmen die 10K-100K+ EUR für AI-Automation ausgeben können.
Branchen: SaaS, E-Commerce, Manufacturing, Finance, Healthcare
Variante: {variant}

OUTPUT als JSON:
{{
    "handle": "@beispiel_firma",
    "company": "Firmenname",
    "industry": "Branche",
    "company_size": "50-500 employees",
    "annual_revenue": "5M-50M EUR",
    "pain_points": ["Problem 1", "Problem 2", "Problem 3"],
    "ai_opportunity": "Konkrete AI-Lösung",
    "estimated_project_value": "25000 EUR",
    "decision_maker": "CTO/CEO title",
    "outreach_hook": "Personalisierter erster Satz",
    "bant_score": 8
}}"""
    },
    {
        "id": "CAT-02",
        "name": "linkedin_lead_mining",
        "count": 50,
        "agent": "kimi",
        "priority": "high",
        "revenue_potential": 3000,
        "prompt": """Du bist ein LinkedIn Lead Mining Agent. Identifiziere ein ideales Lead-Profil.
Fokus: CTOs, VPs Engineering, Heads of Digital bei DACH-Unternehmen.
Variante: {variant}

OUTPUT als JSON:
{{
    "name": "Max Mustermann",
    "title": "CTO",
    "company": "Firma GmbH",
    "linkedin_keywords": ["AI", "Automation", "Digital Transformation"],
    "company_tech_stack": ["Python", "AWS", "Kubernetes"],
    "outreach_message": "Personalisierte LinkedIn-Nachricht",
    "pain_signal": "Warum sie AI brauchen",
    "estimated_deal_size": "15000 EUR",
    "priority": "high"
}}"""
    },
    {
        "id": "CAT-03",
        "name": "cold_email_sequences",
        "count": 50,
        "agent": "kimi",
        "priority": "high",
        "revenue_potential": 2000,
        "prompt": """Erstelle eine Cold Email Sequence für AI-Automation Outreach.
Ziel: Termin für Discovery Call. 3 Emails im Abstand von 3-5 Tagen.
Branche: {variant}

OUTPUT als JSON:
{{
    "sequence_name": "Name",
    "target_industry": "Branche",
    "email_1_subject": "Betreff",
    "email_1_body": "Text mit Personalisierung",
    "email_2_subject": "Follow-up Betreff",
    "email_2_body": "Follow-up Text",
    "email_3_subject": "Break-up Email Betreff",
    "email_3_body": "Letzte Email",
    "expected_reply_rate": "15-25%"
}}"""
    },
    {
        "id": "CAT-04",
        "name": "referral_partner_identification",
        "count": 50,
        "agent": "kimi",
        "priority": "medium",
        "revenue_potential": 4000,
        "prompt": """Identifiziere einen idealen Referral Partner für AI-Automation Services.
Partners: IT-Berater, Unternehmensberater, Software-Häuser, Agenturen.
Variante: {variant}

OUTPUT als JSON:
{{
    "partner_type": "IT-Beratung/Agentur/etc",
    "ideal_profile": "Beschreibung",
    "value_proposition": "Was wir bieten",
    "commission_model": "20-30% Referral Fee",
    "outreach_strategy": "Wie ansprechen",
    "expected_referrals_per_month": 3,
    "average_deal_size": "20000 EUR"
}}"""
    },

    # ═══════════════════════════════════════════
    # CATEGORY 5-8: CONTENT & MARKETING (200 tasks)
    # ═══════════════════════════════════════════
    {
        "id": "CAT-05",
        "name": "viral_x_content",
        "count": 50,
        "agent": "kimi",
        "priority": "high",
        "revenue_potential": 1000,
        "prompt": """Generiere einen VIRALEN X/Twitter Post für AI-Automation Business.
Format: Thread/Single/Meme/Story - Variante {variant}
Ziel: Max. Engagement + Lead-Gen Hook

OUTPUT als JSON:
{{
    "format": "thread/single/meme/story",
    "hook": "Attention-grabbing erster Satz",
    "main_content": "Story/Insight/Take mit konkreten Zahlen",
    "cta": "Call to Action mit Lead-Magnet",
    "hashtags": ["#AI", "#Automation", "#BuildInPublic"],
    "viral_score": 8,
    "estimated_reach": 50000
}}"""
    },
    {
        "id": "CAT-06",
        "name": "blog_seo_content",
        "count": 50,
        "agent": "kimi",
        "priority": "medium",
        "revenue_potential": 800,
        "prompt": """Erstelle einen SEO-optimierten Blog-Artikel-Outline für AI-Automation.
Keyword-Fokus: AI Automation für deutsche Unternehmen.
Variante: {variant}

OUTPUT als JSON:
{{
    "title": "SEO-optimierter Titel",
    "meta_description": "155 Zeichen Meta-Description",
    "target_keyword": "Haupt-Keyword",
    "secondary_keywords": ["Keyword 2", "Keyword 3"],
    "outline": ["H2: Abschnitt 1", "H2: Abschnitt 2", "H2: Abschnitt 3"],
    "word_count_target": 2000,
    "internal_links": ["Verwandte Seiten"],
    "cta": "Lead-Magnet am Ende"
}}"""
    },
    {
        "id": "CAT-07",
        "name": "case_study_generator",
        "count": 50,
        "agent": "kimi",
        "priority": "high",
        "revenue_potential": 3000,
        "prompt": """Generiere eine überzeugende AI-Automation Case Study (fiktiv aber realistisch).
Branche: {variant}

OUTPUT als JSON:
{{
    "client_industry": "Branche",
    "client_size": "Mitarbeiterzahl",
    "challenge": "Problem vor AI-Automation",
    "solution": "Implementierte Lösung",
    "results": {{
        "time_saved": "40 Stunden/Monat",
        "cost_reduction": "30%",
        "revenue_increase": "25%",
        "roi_period": "3 Monate"
    }},
    "testimonial": "Zitat vom Kunden",
    "key_metrics": ["Metric 1", "Metric 2"]
}}"""
    },
    {
        "id": "CAT-08",
        "name": "youtube_video_scripts",
        "count": 50,
        "agent": "kimi",
        "priority": "medium",
        "revenue_potential": 1500,
        "prompt": """Erstelle ein YouTube Video Script über AI-Automation.
Ziel: Thought Leadership + Lead-Gen. Länge: 8-12 Minuten.
Variante: {variant}

OUTPUT als JSON:
{{
    "title": "Clickbait-freier aber ansprechender Titel",
    "thumbnail_concept": "Thumbnail-Idee",
    "hook": "Erste 30 Sekunden",
    "sections": [
        {{"time": "0:00-0:30", "content": "Hook"}},
        {{"time": "0:30-3:00", "content": "Problem"}},
        {{"time": "3:00-8:00", "content": "Lösung"}},
        {{"time": "8:00-10:00", "content": "CTA"}}
    ],
    "cta": "Call to Action",
    "seo_tags": ["Tag1", "Tag2"]
}}"""
    },

    # ═══════════════════════════════════════════
    # CATEGORY 9-12: SYSTEM OPTIMIZATION (200 tasks)
    # ═══════════════════════════════════════════
    {
        "id": "CAT-09",
        "name": "code_improvement_suggestions",
        "count": 50,
        "agent": "claude",
        "priority": "critical",
        "revenue_potential": 2000,
        "prompt": """Du bist ein Senior Python/Node.js Engineer. Analysiere ein AI-Automation System.
Fokus: Performance, Skalierbarkeit, Fehlerbehandlung, Security.
Bereich: {variant}

OUTPUT als JSON:
{{
    "area": "Bereich",
    "current_issues": ["Issue 1", "Issue 2"],
    "improvements": [
        {{
            "title": "Verbesserung",
            "description": "Details",
            "priority": "high/medium/low",
            "effort": "1-3 Stunden",
            "impact": "Performance +30%"
        }}
    ],
    "code_snippets": ["Beispiel-Code"],
    "estimated_improvement": "30% schneller"
}}"""
    },
    {
        "id": "CAT-10",
        "name": "api_integration_design",
        "count": 50,
        "agent": "claude",
        "priority": "high",
        "revenue_potential": 3000,
        "prompt": """Designe eine API-Integration für das AI-Empire System.
Ziel: Neue Datenquellen und Services einbinden.
Integration: {variant}

OUTPUT als JSON:
{{
    "integration_name": "Name",
    "api_provider": "Provider",
    "use_case": "Wofür",
    "endpoint_design": [
        {{
            "method": "POST",
            "path": "/api/v1/resource",
            "description": "Beschreibung"
        }}
    ],
    "auth_method": "API Key/OAuth2",
    "rate_limits": "Limits beachten",
    "error_handling": "Retry-Strategie",
    "estimated_value": "5000 EUR/Monat"
}}"""
    },
    {
        "id": "CAT-11",
        "name": "monitoring_alerting_setup",
        "count": 50,
        "agent": "claude",
        "priority": "high",
        "revenue_potential": 1500,
        "prompt": """Designe ein Monitoring & Alerting System für AI-Empire.
Bereich: {variant}

OUTPUT als JSON:
{{
    "monitoring_area": "Bereich",
    "metrics_to_track": ["Metric 1", "Metric 2"],
    "alert_conditions": [
        {{
            "condition": "Wenn X > Y",
            "severity": "critical/warning/info",
            "action": "Was tun"
        }}
    ],
    "dashboard_widgets": ["Widget 1", "Widget 2"],
    "tools": ["Prometheus", "Grafana"],
    "implementation_steps": ["Step 1", "Step 2"]
}}"""
    },
    {
        "id": "CAT-12",
        "name": "database_optimization",
        "count": 50,
        "agent": "claude",
        "priority": "medium",
        "revenue_potential": 1000,
        "prompt": """Optimiere die Datenbank-Architektur für AI-Empire.
Aktuell: SQLite + Redis. Skalierung geplant.
Bereich: {variant}

OUTPUT als JSON:
{{
    "optimization_area": "Bereich",
    "current_bottleneck": "Problem",
    "proposed_solution": "Lösung",
    "migration_steps": ["Step 1", "Step 2"],
    "performance_gain": "5x schneller",
    "data_model_changes": ["Änderung 1"],
    "indexing_strategy": "Index-Empfehlungen"
}}"""
    },

    # ═══════════════════════════════════════════
    # CATEGORY 13-16: REVENUE OPTIMIZATION (200 tasks)
    # ═══════════════════════════════════════════
    {
        "id": "CAT-13",
        "name": "pricing_strategy",
        "count": 50,
        "agent": "kimi",
        "priority": "critical",
        "revenue_potential": 10000,
        "prompt": """Entwickle eine Pricing-Strategie für AI-Automation Services.
Fokus: Value-Based Pricing, Upsells, Recurring Revenue.
Variante: {variant}

OUTPUT als JSON:
{{
    "service_tier": "Starter/Growth/Enterprise",
    "monthly_price": "2000-20000 EUR",
    "included_features": ["Feature 1", "Feature 2"],
    "upsell_opportunities": ["Upsell 1", "Upsell 2"],
    "annual_discount": "20%",
    "roi_for_client": "5x in 6 Monaten",
    "competitive_positioning": "Positionierung"
}}"""
    },
    {
        "id": "CAT-14",
        "name": "fiverr_gig_optimization",
        "count": 50,
        "agent": "kimi",
        "priority": "high",
        "revenue_potential": 2000,
        "prompt": """Optimiere einen Fiverr Gig für AI-Automation Services.
Ziel: Top-Ranking, Maximum Conversions, Premium Pricing.
Variante: {variant}

OUTPUT als JSON:
{{
    "gig_title": "Optimierter Titel",
    "category": "Fiverr Kategorie",
    "tags": ["Tag1", "Tag2", "Tag3", "Tag4", "Tag5"],
    "description": "Überzeugende Beschreibung",
    "packages": {{
        "basic": {{"price": 100, "delivery": "3 days", "features": ["F1"]}},
        "standard": {{"price": 300, "delivery": "5 days", "features": ["F1", "F2"]}},
        "premium": {{"price": 800, "delivery": "7 days", "features": ["F1", "F2", "F3"]}}
    }},
    "faq": [{{"question": "Q", "answer": "A"}}]
}}"""
    },
    {
        "id": "CAT-15",
        "name": "revenue_stream_ideas",
        "count": 50,
        "agent": "kimi",
        "priority": "critical",
        "revenue_potential": 15000,
        "prompt": """Identifiziere einen neuen Revenue Stream für AI-Empire.
Kategorien: SaaS, Consulting, Templates, Courses, Affiliates.
Variante: {variant}

OUTPUT als JSON:
{{
    "stream_type": "SaaS/Consulting/etc",
    "name": "Name des Revenue Streams",
    "description": "Beschreibung",
    "target_mrr": "5000 EUR/Monat",
    "setup_time": "2 Wochen",
    "setup_cost": "500 EUR",
    "automation_level": "90%",
    "scalability": "10x ohne Mehraufwand",
    "first_steps": ["Step 1", "Step 2", "Step 3"]
}}"""
    },
    {
        "id": "CAT-16",
        "name": "client_retention_strategy",
        "count": 50,
        "agent": "claude",
        "priority": "high",
        "revenue_potential": 8000,
        "prompt": """Entwickle eine Client Retention Strategie für AI-Automation Kunden.
Ziel: 95%+ Retention, Upsells, Lifetime Value maximieren.
Variante: {variant}

OUTPUT als JSON:
{{
    "strategy_name": "Name",
    "trigger_event": "Wann aktivieren",
    "actions": [
        {{
            "timing": "Tag 1/Woche 1/Monat 1",
            "action": "Was tun",
            "channel": "Email/Call/Meeting",
            "template": "Nachricht"
        }}
    ],
    "success_metrics": ["Metric 1", "Metric 2"],
    "automation_potential": "80% automatisierbar",
    "expected_retention_lift": "+15%"
}}"""
    },

    # ═══════════════════════════════════════════
    # CATEGORY 17-20: STRATEGIC & INNOVATION (200 tasks)
    # ═══════════════════════════════════════════
    {
        "id": "CAT-17",
        "name": "market_analysis",
        "count": 50,
        "agent": "kimi",
        "priority": "medium",
        "revenue_potential": 5000,
        "prompt": """Analysiere einen AI-Automation Markt-Segment.
Region: DACH + International. Fokus auf Wachstumspotenzial.
Segment: {variant}

OUTPUT als JSON:
{{
    "segment": "Markt-Segment",
    "market_size": "500M EUR",
    "growth_rate": "35% CAGR",
    "key_players": ["Player 1", "Player 2"],
    "entry_barriers": "Niedrig/Mittel/Hoch",
    "opportunity_window": "12-18 Monate",
    "recommended_approach": "Strategie",
    "estimated_market_share": "2-5% in Year 1"
}}"""
    },
    {
        "id": "CAT-18",
        "name": "partnership_opportunities",
        "count": 50,
        "agent": "kimi",
        "priority": "high",
        "revenue_potential": 20000,
        "prompt": """Identifiziere eine strategische Partnership für AI-Empire.
Typen: Technology, Distribution, Co-Selling, White-Label.
Variante: {variant}

OUTPUT als JSON:
{{
    "partner_type": "Technology/Distribution/etc",
    "partner_profile": "Ideales Profil",
    "value_proposition": "Win-Win Proposition",
    "revenue_model": "Revenue Share/Referral/License",
    "estimated_annual_value": "50000 EUR",
    "first_outreach_approach": "Wie initiieren",
    "strategic_value": "Langfristiger Nutzen"
}}"""
    },
    {
        "id": "CAT-19",
        "name": "automation_blueprint",
        "count": 50,
        "agent": "claude",
        "priority": "critical",
        "revenue_potential": 5000,
        "prompt": """Erstelle einen Automation Blueprint für ein Business-Prozess.
Ziel: End-to-End Automation mit AI. Kein manueller Eingriff.
Prozess: {variant}

OUTPUT als JSON:
{{
    "process_name": "Prozess-Name",
    "current_manual_steps": ["Step 1", "Step 2", "Step 3"],
    "automated_workflow": [
        {{
            "step": 1,
            "tool": "n8n/Python/API",
            "action": "Was passiert",
            "ai_model": "Kimi/Claude/Ollama"
        }}
    ],
    "time_savings": "20 Stunden/Woche",
    "cost_savings": "3000 EUR/Monat",
    "implementation_time": "1-2 Wochen",
    "tech_stack": ["Tool 1", "Tool 2"]
}}"""
    },
    {
        "id": "CAT-20",
        "name": "competitor_weakness_analysis",
        "count": 50,
        "agent": "claude",
        "priority": "high",
        "revenue_potential": 3000,
        "prompt": """Analysiere Schwachstellen von AI-Automation Konkurrenten.
Ziel: Differenzierung und Competitive Advantage finden.
Konkurrent-Typ: {variant}

OUTPUT als JSON:
{{
    "competitor_type": "Typ",
    "typical_weaknesses": ["Schwäche 1", "Schwäche 2"],
    "exploitation_strategy": "Wie ausnutzen",
    "differentiation_points": ["Punkt 1", "Punkt 2"],
    "messaging": "Marketing-Message gegen diesen Typ",
    "win_rate_improvement": "+20% durch Differenzierung",
    "battle_card": {{
        "we_win_when": "Situation",
        "we_lose_when": "Situation",
        "key_objections": ["Einwand 1"]
    }}
}}"""
    },
]

# Varianten für Task-Diversifizierung (50 je Kategorie)
TASK_VARIANTS = {
    "industries": [
        "SaaS", "E-Commerce", "Manufacturing", "Finance", "Healthcare",
        "Real Estate", "Legal", "Education", "Logistics", "Retail",
        "Insurance", "Energy", "Telecom", "Automotive", "Construction",
        "Pharma", "Media", "Travel", "Food & Beverage", "Agriculture",
        "Cybersecurity", "IoT", "Blockchain", "AR/VR", "Robotics",
        "CleanTech", "BioTech", "FinTech", "EdTech", "PropTech",
        "MarTech", "HRTech", "LegalTech", "InsurTech", "RegTech",
        "GovTech", "MedTech", "FoodTech", "AgriTech", "SpaceTech",
        "Fashion", "Gaming", "Sports", "Music", "Film",
        "Consulting", "Recruiting", "Accounting", "Architecture", "Engineering"
    ],
    "processes": [
        "Lead Qualification", "Proposal Generation", "Invoice Processing",
        "Customer Onboarding", "Support Ticket Triage", "Content Scheduling",
        "Competitor Monitoring", "Social Media Management", "Email Marketing",
        "Data Entry", "Report Generation", "Meeting Scheduling",
        "Contract Review", "Expense Tracking", "Inventory Management",
        "Quality Assurance", "Employee Onboarding", "Performance Reviews",
        "Budget Planning", "Project Planning", "Risk Assessment",
        "Compliance Checking", "Vendor Management", "Supply Chain",
        "Customer Feedback Analysis", "Market Research", "Sales Forecasting",
        "Price Optimization", "A/B Testing", "User Research",
        "Bug Triage", "Code Review Automation", "Deployment Pipeline",
        "Security Scanning", "Log Analysis", "Capacity Planning",
        "Disaster Recovery", "Backup Verification", "API Monitoring",
        "Documentation Updates", "Knowledge Base", "FAQ Generation",
        "Chatbot Training", "Sentiment Analysis", "Churn Prediction",
        "Upsell Detection", "Cross-sell Recommendation", "Loyalty Program",
        "Referral Tracking", "NPS Survey Analysis", "Customer Segmentation"
    ],
    "content_formats": [
        "Twitter Thread", "LinkedIn Post", "Blog Article", "Case Study",
        "YouTube Script", "Podcast Outline", "Newsletter", "Whitepaper",
        "Infographic Brief", "Webinar Outline", "Tutorial", "How-To Guide",
        "Industry Report", "Comparison Guide", "Buying Guide",
        "Templates Pack", "Checklist", "Cheat Sheet", "Mind Map",
        "Slide Deck Outline", "Press Release", "Guest Post Pitch",
        "Reddit AMA Prep", "Quora Answers", "Medium Article",
        "Product Hunt Launch", "HackerNews Post", "Dev.to Article",
        "Email Course", "Mini Course", "Workshop Outline",
        "Webinar Script", "Conference Talk", "Podcast Interview Prep",
        "Brand Story", "Origin Story", "Customer Story",
        "Behind The Scenes", "Day In Life", "Tool Review",
        "Comparison Post", "Prediction Post", "Trend Analysis",
        "Weekly Roundup", "Monthly Report", "Quarterly Review",
        "Annual Report", "Mission Statement", "Vision Document",
        "Culture Post", "Team Spotlight", "Milestone Celebration"
    ],
}


def generate_task_list():
    """Generate all 1000 tasks with variants."""
    tasks = []
    task_id = 1

    for category in TASK_CATEGORIES:
        variants = TASK_VARIANTS.get("industries", TASK_VARIANTS["industries"])

        # Use different variant lists based on category
        if "content" in category["name"] or "blog" in category["name"] or "youtube" in category["name"]:
            variants = TASK_VARIANTS["content_formats"]
        elif "automation" in category["name"] or "monitoring" in category["name"] or "database" in category["name"]:
            variants = TASK_VARIANTS["processes"]

        for i in range(category["count"]):
            variant = variants[i % len(variants)]
            tasks.append({
                "task_id": f"NIGHT-{task_id:04d}",
                "category_id": category["id"],
                "category_name": category["name"],
                "agent": category["agent"],
                "priority": category["priority"],
                "revenue_potential": category["revenue_potential"],
                "prompt": category["prompt"].format(variant=variant),
                "variant": variant,
            })
            task_id += 1

    return tasks


# Quick validation
if __name__ == "__main__":
    tasks = generate_task_list()
    print(f"Generated {len(tasks)} tasks")

    kimi_tasks = [t for t in tasks if t["agent"] == "kimi"]
    claude_tasks = [t for t in tasks if t["agent"] == "claude"]
    print(f"  Kimi tasks:   {len(kimi_tasks)}")
    print(f"  Claude tasks: {len(claude_tasks)}")

    categories = {}
    for t in tasks:
        cat = t["category_name"]
        categories[cat] = categories.get(cat, 0) + 1
    print(f"\nCategories ({len(categories)}):")
    for cat, count in categories.items():
        print(f"  {cat}: {count}")
