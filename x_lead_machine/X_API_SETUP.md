# X/Twitter API Setup - Schritt-für-Schritt

## 1. Developer Portal Zugang

### Account-Voraussetzungen
- Verifizierter X-Account (Telefonnummer + E-Mail)
- Account muss mindestens 30 Tage alt sein
- Keine kürzlichen Verstöße gegen X-Richtlinien

### Anmeldung
1. Gehe zu: https://developer.x.com/
2. Klicke "Sign up" (rechts oben)
3. Melde dich mit deinem X-Account an
4. Akzeptiere Developer Agreement
5. Beschreibe deinen Use Case (kurz: "Lead monitoring and engagement automation")

---

## 2. API-Tier Auswahl

| Tier | Kosten | Posts lesen | Posts schreiben | Für Lead-Machine |
|------|--------|-------------|-----------------|------------------|
| **Free** | $0/Monat | 10.000/Monat | 1.500/Monat | Zum Testen |
| **Basic** | $100/Monat | 50.000/Monat | 3.000/Monat | Empfohlen |
| **Pro** | $5.000/Monat | 1.000.000/Monat | 300.000/Monat | Overkill |

### Empfehlung für Lead-Monitoring
**Start mit Free Tier** zum Testen, dann **Basic Tier** für Production.

Free Tier Limits:
- 1.500 Posts/Monat schreiben (= ~50/Tag)
- 10.000 Posts/Monat lesen (= ~330/Tag)
- Rate Limit: 50 Requests/15min

---

## 3. API Keys generieren

### Schritt 1: App erstellen
1. Developer Portal → Projects & Apps → "+ Add App"
2. App Name eingeben (z.B. "LeadMachine-Maurice")
3. App Type: "Production" wählen

### Schritt 2: Keys & Tokens
Nach App-Erstellung siehst du:
- **API Key** (Consumer Key)
- **API Key Secret** (Consumer Secret)

> WICHTIG: Diese werden nur EINMAL angezeigt! Sofort speichern!

### Schritt 3: Access Tokens
1. Gehe zu App Settings → "Keys and tokens"
2. Unter "Authentication Tokens" → "Generate"
3. Du bekommst:
   - **Access Token**
   - **Access Token Secret**

### Schritt 4: Bearer Token
1. Gleiche Seite → "Bearer Token" → "Generate"
2. Speichere den Bearer Token

### Deine .env Datei
```env
X_API_KEY=dein_api_key
X_API_SECRET=dein_api_secret
X_ACCESS_TOKEN=dein_access_token
X_ACCESS_TOKEN_SECRET=dein_access_token_secret
X_BEARER_TOKEN=dein_bearer_token
```

---

## 4. Relevante Endpoints für Lead-Monitoring

### Suche nach Keywords (Leads finden)
```
GET /2/tweets/search/recent
```
- Sucht Tweets der letzten 7 Tage
- Query: `"looking for" OR "need help with" OR "Brandmelder" -is:retweet lang:de`
- Limit: 450 requests/15min (Basic)

### User Lookup (Lead-Profil checken)
```
GET /2/users/:id
GET /2/users/by/username/:username
```
- Follower-Count, Bio, Website
- Verifizierung, Account-Alter

### Tweet erstellen (Antworten/DMs)
```
POST /2/tweets
```
- Antwort auf Lead-Tweet
- Max 280 Zeichen

### User Timeline (Activity checken)
```
GET /2/users/:id/tweets
```
- Letzte Tweets eines Users
- Für Lead-Qualifizierung

### Streaming (Echtzeit-Monitoring)
```
GET /2/tweets/search/stream
```
- Echtzeit-Feed basierend auf Regeln
- Nur in Pro Tier verfügbar!

---

## 5. Quick Test (Python)

```python
import tweepy

# Auth
client = tweepy.Client(
    bearer_token="DEIN_BEARER_TOKEN",
    consumer_key="DEIN_API_KEY",
    consumer_secret="DEIN_API_SECRET",
    access_token="DEIN_ACCESS_TOKEN",
    access_token_secret="DEIN_ACCESS_TOKEN_SECRET"
)

# Suche nach Leads
query = '"suche Elektriker" OR "Brandmelder Problem" -is:retweet lang:de'
tweets = client.search_recent_tweets(query=query, max_results=10)

for tweet in tweets.data:
    print(tweet.text)
```

---

## 6. Rate Limits Übersicht

| Endpoint | Free | Basic | Pro |
|----------|------|-------|-----|
| Search Recent | 60/15min | 450/15min | 450/15min |
| Post Tweet | 17/15min | 100/15min | 100/15min |
| User Lookup | 25/15min | 100/15min | 900/15min |
| User Timeline | 25/15min | 100/15min | 900/15min |

---

## 7. Nächste Schritte

1. [ ] Free Tier Account erstellen
2. [ ] App erstellen und Keys generieren
3. [ ] .env Datei mit Keys füllen
4. [ ] Quick Test laufen lassen
5. [ ] Erste Lead-Suche durchführen
6. [ ] Bei Erfolg: Upgrade auf Basic Tier

---

## Troubleshooting

**"Forbidden 403"** → App-Permissions prüfen (Read + Write nötig)
**"Rate limit exceeded"** → 15 Minuten warten
**"Unauthorized 401"** → Keys/Tokens neu generieren
**"Not found 404"** → Endpoint-URL prüfen

---

*Erstellt: 2026-02-08 | Für: X-Lead-Machine*
