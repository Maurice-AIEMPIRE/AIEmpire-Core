# Jarvis Profile (Voice + Automation)

## Ziel

Dieses Setup gibt dir ein lokales Jarvis-System mit:

1. Wake-Word `jarvis` (im Browser, Desktop + Handy)
2. Audio-Doctor (prueft Input/Output gegen dein Profil)
3. Device-Fix (optional mit `SwitchAudioSource`)
4. Command-Routing in deine bestehenden `automation` und `mission_control` Flows
5. Freie Fragen ueber lokales Ollama-Modell

## 1) Starten

```bash
automation/scripts/run_jarvis_live.sh
```

Danach:

1. Desktop: `http://127.0.0.1:8877`
2. Handy im selben WLAN: `http://<deine-lan-ip>:8877`

## 2) Wake-Word nutzen

Sage im Browser-Mic:

1. `Jarvis status`
2. `Jarvis plan`
3. `Jarvis workflow threads`
4. `Jarvis multi gib mir 5 offer angles fuer AI automation`

Alles, was kein Systembefehl ist, geht als normale Frage an Ollama.

## 3) DJI-Mikrofon erzwingen

Audio-Check:

```bash
python3 -m automation.jarvis --profile automation/config/jarvis_profile.json doctor
```

Optionales Auto-Switching (macOS):

```bash
brew install switchaudio-osx
python3 -m automation.jarvis --profile automation/config/jarvis_profile.json audio-apply
```

Hinweis:

1. Input sollte dein DJI-Mic sein.
2. Output darf AirPods/Lautsprecher sein.

## 4) Profil anpassen

Datei:

`automation/config/jarvis_profile.json`

Wichtige Felder:

1. `wake_word`: Aktivierungswort
2. `audio.preferred_input_contains`: z. B. `"DJI"`
3. `audio.preferred_output_contains`: z. B. `"AirPods"`
4. `assistant.model`: Ollama-Modell
5. `security.api_token`: API-Schutz fuer externe Nutzung

## 5) Zugriff von unterwegs

Wenn `cloudflared` installiert ist, zeigt das Startskript den Tunnel-Befehl.

Beispiel:

```bash
cloudflared tunnel --url http://127.0.0.1:8877
```

Dann kannst du den erzeugten HTTPS-Link auf dem Handy unterwegs nutzen.

## 6) Copilot/Quota-Fehler (402)

Dein Fehler `Quota exceeded` kommt vom jeweiligen Cloud-Agent (nicht von diesem lokalen Jarvis-Flow).

Dieses Jarvis-Setup laeuft lokal mit Ollama weiter, auch wenn der externe Agent kein Kontingent mehr hat.
