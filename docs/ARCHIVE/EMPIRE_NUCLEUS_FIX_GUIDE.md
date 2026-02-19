# Fix-Guide: empire_nucleus.py — 30+ Pyre2-Fehler

**Datei:** `/Users/maurice/.gemini/antigravity/playground/photonic-schrodinger/empire_nucleus.py`
**Fehler-Quelle:** Pyre2 Type Checker
**Analyse von:** Claude Opus 4.6 | 09.02.2026

---

## Kurzfassung

Die meisten Fehler sind **Pyre2 Type-Checker Probleme**, keine echten Runtime-Bugs. Pyre2 ist strenger als Python selbst. Trotzdem sollten sie behoben werden, weil sie auf potentielle Probleme hinweisen.

**5 Fehler-Kategorien:**

| Kategorie | Anzahl | Schwere | Fix-Aufwand |
|-----------|--------|---------|-------------|
| Fehlende Imports | 2 | Hoch | 2 Min |
| List-Slicing Typ-Fehler | 8 | Niedrig (Pyre2-Bug) | 5 Min |
| Numerische Typ-Fehler | 6 | Mittel | 5 Min |
| Objekt-/Rückgabe-Typ-Fehler | 6 | Hoch | 15 Min |
| Interne Pyre2-Fehler | 8+ | Niedrig | 10 Min |

---

## Kategorie 1: Fehlende Imports (Zeilen 44, 52)

### Problem
```
Could not find import of `ollama_engine`
Could not find import of `aiohttp`
```

### Fix
```python
# Zeile 44 — ollama_engine muss installiert oder als lokales Modul vorhanden sein
# Option A: Wenn ollama_engine ein eigenes Modul ist
# Stelle sicher, dass ollama_engine.py im gleichen Ordner liegt
# oder dass der PYTHONPATH korrekt gesetzt ist

# Option B: Wenn es ein Package ist
pip install ollama  # oder das korrekte Package

# Zeile 52 — aiohttp fehlt
pip install aiohttp
```

**Pyre2-spezifisch:** Erstelle eine `.pyre_configuration` Datei im Projekt-Root:
```json
{
  "search_path": ["."],
  "source_directories": ["."]
}
```

---

## Kategorie 2: List-Slicing Typ-Fehler (Zeilen 137, 231, 232, 959, 980)

### Problem
```
Cannot index into `list[...]`
Argument `slice[int, int, int]` is not assignable to parameter `SupportsIndex`
```

### Ursache
Pyre2 erkennt `list[1:3]` (Slicing) nicht korrekt — es denkt, `__getitem__` akzeptiert nur `SupportsIndex` (einzelner Index), nicht `slice`. Das ist ein **bekannter Pyre2-Bug** mit List-Slicing.

### Fix (alle betroffenen Zeilen)
```python
# Zeile 137 — Vorher:
result = some_list[1::2]

# Option A: Type-Ignore-Kommentar (empfohlen für Pyre2)
result = some_list[1::2]  # pyre-ignore[16]

# Option B: Explizites Slicing
result = list(some_list)[1::2]

# Option C: Slice-Objekt verwenden
result = some_list.__getitem__(slice(1, None, 2))
```

**Betroffene Zeilen:** 137, 231, 232, 959, 980, 1207

---

## Kategorie 3: Numerische Typ-Fehler (Zeilen 213, 229, 411, 1019, 1047, 1188)

### Problem A: min/max mit float (Zeilen 213, 1019)
```
Argument `float` is not assignable to parameter with type `int` in function `min`
```

### Fix
```python
# Zeile 213 — Vorher:
value = min(some_int, some_float_expression)

# Nachher: Explizit casten
value = min(some_int, int(some_float_expression))
# Oder wenn float-Ergebnis gewünscht:
value = min(float(some_int), some_float_expression)
```

### Problem B: round mit ndigits (Zeilen 229, 411)
```
Argument `Literal[3]` is not assignable to parameter `ndigits` with type `None`
```

### Fix
```python
# Zeile 229 — Vorher:
result = round(value, 3)

# Nachher: Typ-Annotation hinzufügen
result: float = round(value, 3)  # pyre-ignore[6]

# Oder: Variablen-Trick
ndigits: int = 3
result = round(value, ndigits)
```

### Problem C: Division int | str (Zeilen 1047, 1188)
```
`/` is not supported between `int | str` and `int`
```

### Fix
```python
# Zeile 1047 — Vorher:
result = some_value / divisor  # some_value könnte str sein

# Nachher: Explizite Typ-Prüfung
if isinstance(some_value, (int, float)):
    result = some_value / divisor
else:
    result = int(some_value) / divisor
```

---

## Kategorie 4: Objekt-/Rückgabe-Typ-Fehler (Zeilen 739, 779, 795, 810)

### Problem A: Not callable (Zeile 739)
```
Expected a callable, got None
```

### Fix
```python
# Zeile 739 — Vorher:
callback = some_dict.get("handler")
callback(args)  # Könnte None sein!

# Nachher: None-Check
callback = some_dict.get("handler")
if callback is not None and callable(callback):
    callback(args)
```

### Problem B: isinstance mit None (Zeile 779)
```
Argument `Error | None` is not assignable to `type` in `isinstance`
```

### Fix
```python
# Zeile 779 — Vorher:
if isinstance(obj, some_error_class):  # some_error_class könnte None sein

# Nachher: None-Guard
if some_error_class is not None and isinstance(obj, some_error_class):
    # handle error
```

### Problem C: Missing attribute .content (Zeile 795)
```
Object of class `object` has no attribute `content`
```

### Fix
```python
# Zeile 795 — Vorher:
text = response.content

# Nachher: Type-Hint oder hasattr
if hasattr(response, 'content'):
    text = response.content

# Oder besserer Typ-Hint bei der Funktionsdefinition:
async def get_response() -> SomeResponseType:  # Statt -> object
```

### Problem D: Bad return type (Zeile 810)
```
Returned type `tuple[Coroutine[...]]` is not assignable to `list[dict[...]]`
```

### Fix
```python
# Zeile 810 — Vorher:
async def some_func() -> list[dict]:
    return (some_coroutine(),)  # Tuple statt List!

# Nachher: Korrekte Rückgabe
async def some_func() -> list[dict]:
    result = await some_coroutine()
    return [result]  # List zurückgeben, nicht Tuple

# Oder wenn mehrere Coroutines:
async def some_func() -> list[dict]:
    results = await asyncio.gather(some_coroutine())
    return list(results)
```

---

## Kategorie 5: Interne Pyre2-Fehler (Zeile 939, 1205, 1207)

### Problem A: += nicht unterstützt (Zeile 939)
```
`+=` is not supported between `@14826` and `Literal[1]`
TODO: Binding::AugAssign attribute base undefined
```

**Das ist ein interner Pyre2-Bug**, kein echter Code-Fehler. Pyre2 kann den Typ nicht inferieren.

### Fix
```python
# Zeile 939 — Vorher:
counter += 1

# Nachher: Typ-Annotation
counter: int = 0  # Am Anfang der Funktion
# ...
counter += 1  # Jetzt kennt Pyre2 den Typ

# Oder: pyre-ignore
counter += 1  # pyre-ignore[58]
```

### Problem B: startswith fehlt (Zeile 1205)
```
attribute base undefined for type: @_ (trying to access startswith)
```

### Fix
```python
# Zeile 1205 — Vorher:
if value.startswith("prefix"):

# Nachher: Typ sicherstellen
if isinstance(value, str) and value.startswith("prefix"):
```

---

## Quick-Fix Cheatsheet

Kopiere diese Zeilen und ersetze die entsprechenden Stellen:

```python
# Für alle List-Slicing-Fehler: pyre-ignore am Ende der Zeile
# Zeile 137:
result = data[start::step]  # pyre-ignore[16]

# Zeile 231:
items = items[:5]  # pyre-ignore[16]

# Zeile 232:
batch = batch[:3]  # pyre-ignore[16]

# Zeile 959:
chunk = results[:10]  # pyre-ignore[16]

# Zeile 980:
recent = history[:20]  # pyre-ignore[16]

# Für round/min/max:
# Zeile 213:
value = min(x, int(y))  # oder float() wenn nötig

# Zeile 229:
score = round(value, 3)  # pyre-ignore[6]

# Zeile 411:
pct = round(ratio, 2)  # pyre-ignore[6]

# Zeile 1019:
cap = max(0, int(computed_value))

# Für None-Safety:
# Zeile 739:
if handler is not None:
    handler(data)

# Zeile 779:
if error_cls is not None and isinstance(exc, error_cls):
    ...

# Zeile 795:
text = getattr(response, 'content', '')
```

---

## Empfehlung

**Sofort machen (5 Min):**
1. `pip install aiohttp` — behebt Zeile 52
2. `ollama_engine` Import-Pfad prüfen — behebt Zeile 44

**Bei Gelegenheit (15 Min):**
3. Alle `# pyre-ignore[16]` für List-Slicing setzen
4. None-Guards für Zeilen 739, 779, 795 einbauen
5. Return-Type in Zeile 810 korrigieren (tuple → list)

**Optional:**
6. `.pyre_configuration` anlegen für bessere Type-Inference
7. Type-Annotations für alle Funktionen hinzufügen

---

*Wenn du mir Zugriff auf den Ordner gibst, kann ich alle Fixes direkt in die Datei einbauen.*
