# Free Network (Local + Offline)

## Ziel

Kostenloses lokales Netzwerk mit:
1. Mic-Button im Browser
2. Llama-Chat ueber lokale Ollama-Modelle
3. Kein Cloud-Zwang fuer den Chat-Flow

## Start

```bash
automation/scripts/run_free_network_live.sh
```

## Nutzung

1. Oeffne `http://127.0.0.1:8765`.
2. Druecke `Mic Start`, sprich, dann `Mic Stop`.
3. Druecke `Senden`.

## Komponenten

1. UI + API-Proxy: `automation/free_network_server.py`
2. Starter: `automation/scripts/run_free_network_live.sh`
3. Modell-Backend: `ollama` auf `http://127.0.0.1:11434`

## Modell wechseln

```bash
FREE_NETWORK_MODEL="phi4-mini:latest" automation/scripts/run_free_network_live.sh
```

## Stoppen

Der Starter schreibt PID in `automation/runs/free_network_<run_id>/README.txt`.
Beispiel:

```bash
kill <PID>
```
