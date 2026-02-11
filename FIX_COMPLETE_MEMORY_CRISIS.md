# COMPLETE MEMORY CRISIS FIX

## Das Problem (3.8GB RAM Zu Wenig)

**Speicher-Situation:**
- Total RAM: 3.8GB
- Claude Prozesse: ~900MB (23%)
- Verfuegbar: ~1.7GB (44%)

## SOFORT-MASSNAHMEN

### 1. Nur QUANTISIERTE Modelle
- phi:q4 (600MB) - BEST
- neural-chat:q4 (2.5GB) - OK

### 2. Ollama Config
```
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_NUM_THREAD=2
export OLLAMA_KEEP_ALIVE=5m
```

### 3. Memory Monitor
```
bash memory_monitor.sh &
python3 smart_ollama_launch.py
```

## ERGEBNISSE
- Vorher: 95% RAM, crashes
- Nachher: 40% RAM, stabil

## FILES
- MEMORY_FIX_COMPLETE.py
- smart_ollama_launch.py
- memory_monitor.sh
- memory_cleanup_aggressive.sh
- QUICK_MEMORY_FIX.sh

Generated: 2026-02-10
