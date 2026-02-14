# REVENUE EXECUTION BOARD 30D (Hybrid 70/30)

## 1) Modus + Baseline
- Datum Start: `2026-02-14`
- Modus: `70% Service-Cashflow`, `30% Shorts-Autopilot`
- Baseline aus Snapshot:
  - `real_revenue_eur = 0.0`
  - `projected_revenue_eur_24h = 5.4`
  - `shorts_published_this_run = 0`
  - YouTube OAuth unvollständig, Stripe-Key fehlt.
  - Launchd läuft im TCC-sicheren Fallback-Modus; produktive Workflows müssen in launchd-taugliche Pfade migriert werden.

## 2) 30-Tage Ziele
- Ziel A (Cash): erster dokumentierter Echtgeld-Umsatz <= Tag 7.
- Ziel B (Service): mindestens `EUR 3,000` realer Service-Umsatz bis Tag 30.
- Ziel C (Autopilot): ab Tag 10 tägliche Publishes auf mindestens einem Kanal.
- Ziel D (Governance): täglicher 08:00 Audit und wöchentlicher Consolidation Report.

## 3) KPI-Scoreboard (Daily)
| KPI | Daily Target | Track |
|---|---|---|
| Neue Outreach-Nachrichten | 30 | Service (70%) |
| Qualifizierte Antworten | 6 | Service (70%) |
| Gebuchte Calls | 2 | Service (70%) |
| Gesendete Angebote | 2 | Service (70%) |
| Closings | 1 alle 3 Tage | Service (70%) |
| Reale Stripe-Einnahmen | >0 ab Tag 7 | Service (70%) |
| Shorts produziert | 4 | Shorts (30%) |
| Shorts veröffentlicht (YT/TikTok gesamt) | 2 | Shorts (30%) |
| Endpoint-Health grün (`5678`,`11434`,`18789`,`3333`) | 100% | Ops |
| Kritische LaunchAgents mit `exit=0` | 8/8 | Ops |

## 4) Tagesroutine (Europe/Berlin)
- `08:00` Runtime-Audit:
  - `launchctl`-safe Daily Snapshot: `~/Library/Application Support/ai-empire/infra/SYSTEM_INVENTORY_latest.json`
  - Manueller Full Snapshot (vor Tagesplanung): `python3 /Users/maurice/Documents/New\ project/automation/scripts/audit_infra_runtime.py --mode snapshot --output /Users/maurice/Documents/New\ project/00_SYSTEM/infra/SYSTEM_INVENTORY_$(date +%F).json --redact-secrets true`
- `08:15` P0/P1-Check und Tagesprioritäten in Board aktualisieren.
- `09:00-13:00` Service-Sales Sprint (Outreach, Follow-ups, Calls, Offers).
- `14:00-16:00` Delivery/Case-Produktion für laufende Deals.
- `16:00-18:00` Shorts-Autopilot (Produktion/Publish/Engagement-Review).
- `20:00` KPI-Abschluss und `First-cash`-Tracking.

## 5) 30-Tage Ausführung

### Tage 1-3 (Infrastructure + Offer Readiness)
| Tag | Fokus | Konkrete Deliverables |
|---|---|---|
| 1 | Runtime reparieren | 8 kritische LaunchAgents geladen; Degradations-Fallback aktiv; Endpoint `5001`/`8080` geklärt |
| 2 | Credentials schließen | YouTube OAuth vollständig; `STRIPE_SECRET_KEY` gesetzt; `N8N_API_KEY` ergänzt |
| 3 | Revenue SoT aktivieren | `content_factory/deliverables/revenue/stripe/latest.json` wird geschrieben; real revenue KPI live |

### Tage 4-7 (First Cash Window)
| Tag | Fokus | Konkrete Deliverables |
|---|---|---|
| 4 | Offer-Funnel | 2 klar bepreiste Service-Angebote (Core + Upsell) mit kurzer Landing-Message |
| 5 | Outreach-Welle 1 | 30 neue Kontakte, 6 Replies, 2 Calls |
| 6 | Follow-up-Welle | 2 Angebote raus, Einwandbehandlung vorbereitet |
| 7 | Close-Day | Erster bezahlter Deal dokumentiert (`Datum`, `Quelle`, `Betrag`) |

### Woche 2 (Tage 8-14)
- Service (70%): täglicher Outreach/Follow-up-Takt, Ziel `EUR 1,000+` kumuliert.
- Shorts (30%): Publish-Flow stabil, Ziel `>= 10` Publishes in Woche.
- Ops: Safety-Guard kalibriert, keine Dauer-Skip-Loops.

### Woche 3 (Tage 15-21)
- Service: Angebotspakete hochstufen, Ziel `EUR 2,000+` kumuliert.
- Shorts: Hook-Varianten testen, Engagement-Baselines dokumentieren.
- Ops: Weekly Consolidation inklusive `running jobs`, `real revenue`, `publish counts`.

### Woche 4 (Tage 22-30)
- Service: Closing-Intensivphase auf offene Pipeline.
- Shorts: nur Formate mit positiver Retention und Conversion weiterfahren.
- Zielabschluss: `EUR 3,000` realer Umsatz, stabiler Daily Audit, Shadow-Systeme reduziert.

## 6) Deal-Pipeline (Service 70%)
| Stage | KPI | Exit-Kriterium |
|---|---|---|
| Lead identifiziert | 30/Tag | Kontakt mit klarem ICP-Match |
| Erstkontakt | 30/Tag | Nachricht versendet |
| Reply | 6/Tag | qualifizierte Antwort erhalten |
| Call | 2/Tag | Termin gebucht |
| Angebot | 2/Tag | Preis + Scope verschickt |
| Close | 1/3 Tage | Zahlung eingegangen |

## 7) Shorts-Pipeline (30%)
| Schritt | KPI | Gate |
|---|---|---|
| Topic + Script | 4/Tag | Content-Safety bestanden |
| Render + Package | 4/Tag | Asset vollständig |
| Publish | 2/Tag | OAuth/API verfügbar |
| Review | täglich | Retention/CTR dokumentiert |

## 8) Kill-Switch Regeln
- Wenn System-Load dauerhaft kritisch: Autopilot-Cadence drosseln statt komplette Pipeline zu skippen.
- Wenn `real_revenue_eur` 3 Tage unverändert 0: Service-Track auf 80% erhöhen bis erster Cashflow.
- Wenn Publish 3 Tage `0`: Publish-Flow manuell übersteuern, OAuth/API-Checks priorisieren.

## 9) Daily Log Template
| Date | Outreach | Replies | Calls | Offers | Closes | Real EUR | Shorts Published | Notes |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 2026-02-14 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | Baseline |

## 10) First-Cash Pflichtfeld
- Datum:
- Quelle (Service/Shorts/Other):
- Betrag (EUR):
- Nachweisdatei:
