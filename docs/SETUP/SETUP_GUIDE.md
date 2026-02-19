# SETUP GUIDE - GitHub Control System

## 🚀 Schnellstart (5 Minuten)

### Schritt 1: GitHub Secrets einrichten

1. Gehe zu Repository Settings
2. Klicke auf "Secrets and variables" → "Actions"
3. Füge folgende Secrets hinzu:

```
MOONSHOT_API_KEY = dein-kimi-api-key
ANTHROPIC_API_KEY = dein-claude-api-key (optional)
```

> **Hinweis:** `GITHUB_TOKEN` ist automatisch verfügbar!

### Schritt 2: Workflows aktivieren

Die Workflows sind bereits konfiguriert und werden automatisch ausgeführt:

- ✅ Jede 4 Stunden: Content Generation
- ✅ Jede 30 Minuten: Claude Health Check
- ✅ Täglich 7 AM: X Auto Poster
- ✅ Täglich 9 AM: Revenue Tracking
- ✅ Bei jedem Issue/Comment: Command Bot

### Schritt 3: Ersten Command testen

1. Erstelle ein neues Issue
2. Gib ihm einen beliebigen Titel
3. Kommentiere:
   ```
   @bot status
   ```
4. Warte 10-30 Sekunden
5. Der Bot antwortet automatisch!

## 📋 Verfügbare Commands

### System
```
@bot status              # System Status anzeigen
@bot help               # Alle Commands anzeigen
```

### Content
```
@bot generate-content   # 5 X/Twitter Posts generieren
@bot post-x            # X Posting Guide
```

### Business
```
@bot revenue-report    # Revenue Overview
@bot create-gig        # Fiverr Gig Descriptions
```

## 🎯 Erste Schritte nach Setup

### Tag 1: Content starten

1. Command: `@bot generate-content`
2. Kopiere die Posts
3. Poste auf X/Twitter (8am, 12pm, 5pm, 7pm, 9pm)
4. Engagiere mit Kommentaren

### Tag 2: Fiverr Gigs

1. Command: `@bot create-gig`
2. Gehe zu Fiverr.com
3. Create 3 Gigs mit den Descriptions
4. Set pricing (EUR 50-500)
5. Publish!

### Tag 3: Revenue Tracking

1. Command: `@bot revenue-report`
2. Checke tägliche Reports (9 AM UTC)
3. Update manual revenue if needed
4. Track growth

## 🔄 Claude Failover Prozess

### Automatisch

Das System prüft Claude API alle 30 Minuten:

```
Claude OK? → Weitermachen wie bisher
Claude Limit? → Automatisch zu GitHub Mode wechseln
```

### Manuell prüfen

```
@bot status
```

Wenn GitHub Mode aktiv:
- Alle Commands funktionieren weiter
- Kimi API wird als Primary genutzt
- System schaltet automatisch zurück wenn Claude verfügbar

## 💰 Monetization Setup

### 1. Gumroad (Digital Products)

**Jetzt:**
1. Gehe zu gumroad.com
2. Create Product
3. Titel: "OpenClaw Quick Start Guide"
4. Preis: EUR 49
5. Description von `@bot create-gig` anpassen

**Weitere Produkte:**
- AI Automation Blueprint (EUR 79)
- BMA + AI Integration (EUR 149)
- Workflow Templates Pack (EUR 27)

### 2. Fiverr (Services)

**Jetzt:**
1. Command: `@bot create-gig`
2. Kopiere die 3 Gig Descriptions
3. Create auf Fiverr
4. Publish!

**Pricing:**
- Basic: EUR 50-100
- Standard: EUR 150-300
- Premium: EUR 500-1000

### 3. X/Twitter (Leads)

**Täglich:**
1. Command: `@bot generate-content` oder warte auf Auto-Generation (7 AM)
2. Poste 5 Posts über den Tag verteilt
3. Reply auf 10-20 relevante Tweets
4. DM hot leads

**Hashtags:**
#AIAutomation #BuildInPublic #AIAgents #NoCode #Automation

### 4. Consulting (High Value)

**Offer erstellen:**
1. Basierend auf Fiverr Gig 3
2. 30-Min Discovery Call (EUR 100)
3. Strategy Session (EUR 300)
4. Full Implementation (EUR 1000+)

**Outreach:**
- LinkedIn: 10 personalized messages/day
- X DMs: 5 qualified leads/day
- Email: Cold outreach to companies

## 🛠️ Lokale Installation (Optional)

Für lokales Testing:

```bash
# Clone repo
git clone https://github.com/mauricepfeifer-ctrl/AIEmpire-Core.git
cd AIEmpire-Core

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export MOONSHOT_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
export GITHUB_TOKEN="your-token"

# Test systems
python3 github_control_interface.py
python3 claude_failover_system.py
python3 x_auto_poster.py
```

## 📱 Mobile Workflow

**Von iPhone/Android:**

1. Öffne GitHub App
2. Navigate zu AIEmpire-Core
3. Gehe zu Issues
4. Erstelle Issue oder kommentiere
5. Commands:
   ```
   @bot generate-content
   @bot revenue-report
   ```
6. System antwortet automatisch!

**Desktop Browser:**
- github.com/mauricepfeifer-ctrl/AIEmpire-Core/issues

## 🔍 Monitoring

### System Status

**Check:** `@bot status`

**Zeigt:**
- Service Status (✅/❌)
- Recent Activity
- Quick Stats
- Available Commands

### Workflows

**Check:** github.com/mauricepfeifer-ctrl/AIEmpire-Core/actions

**Siehst:**
- Letzte Workflow Runs
- Success/Failure Status
- Logs bei Errors

### Revenue

**Daily Report:** Automatisch um 9 AM UTC

**Manual:** `@bot revenue-report`

## 🚨 Troubleshooting

### Bot antwortet nicht

1. Check Actions Tab → Sind Workflows enabled?
2. Check Secrets → Sind Keys gesetzt?
3. Workflow Logs anschauen

### Content Generation schlägt fehl

1. Check MOONSHOT_API_KEY
2. Check Budget auf moonshot.cn
3. Try `@bot generate-content` manuell

### GitHub Rate Limits

- Sehr unwahrscheinlich (großzügige Limits)
- Falls doch: Cron Intervalle erhöhen
- Enterprise Kontakt bei Bedarf

## 📞 Support

**Issues erstellen:**
github.com/mauricepfeifer-ctrl/AIEmpire-Core/issues

**Commands testen:**
`@bot help` in jedem Issue

**Documentation:**
- [GITHUB_CONTROL_SYSTEM.md](./GITHUB_CONTROL_SYSTEM.md)
- [COPILOT_BRIEFING.md](./COPILOT_BRIEFING.md)
- [HANDOFF_PROTOCOL.md](./HANDOFF_PROTOCOL.md)

## 🎯 Next Steps

### Diese Woche:

- [ ] Setup Secrets ✅
- [ ] Ersten Command testen ✅
- [ ] 20+ X Posts erstellen
- [ ] 3 Fiverr Gigs live
- [ ] 1-2 Gumroad Products
- [ ] Erste Leads generieren

### Dieser Monat:

- [ ] EUR 25,000 Revenue
- [ ] 500+ Leads in CRM
- [ ] 20+ Consulting Calls
- [ ] 10+ Fiverr Orders
- [ ] 100+ Gumroad Sales

### Dieses Jahr:

- [ ] EUR 500,000+ Revenue
- [ ] Full Automation
- [ ] Team aufbauen
- [ ] Multiple Products
- [ ] AI Empire Complete

---

**READY TO START! 🚀💰**
