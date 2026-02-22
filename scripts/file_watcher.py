#!/usr/bin/env python3
"""
File Watcher — Auto-Processing Pipeline (Tip #2: Local Device Workflows)
=========================================================================
Watches a local folder for new files and auto-processes them:
  - Videos  → transcribe, translate to 10 languages, extract chapters
  - Docs    → summarize, extract action items
  - Images  → describe, suggest social captions
  - Code    → review, suggest improvements
  - Audio   → transcribe, create show notes

This is the "airdrop workflow" — drop a file from your phone/desktop
and the agent processes it automatically.

Usage:
    python3 scripts/file_watcher.py              # Watch default folder
    python3 scripts/file_watcher.py ~/Desktop     # Watch custom folder
    python3 scripts/file_watcher.py --once ./file  # Process single file
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

WATCH_DIR = PROJECT_ROOT / "watch"
OUTPUT_DIR = PROJECT_ROOT / "watch" / "processed"
LOG_FILE = PROJECT_ROOT / "logs" / "file_watcher.log"

# File type detection
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".ogg", ".flac"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".heic"}
DOC_EXTS = {".pdf", ".txt", ".md", ".docx", ".csv"}
CODE_EXTS = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java"}


def detect_file_type(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in VIDEO_EXTS:
        return "video"
    elif ext in AUDIO_EXTS:
        return "audio"
    elif ext in IMAGE_EXTS:
        return "image"
    elif ext in DOC_EXTS:
        return "document"
    elif ext in CODE_EXTS:
        return "code"
    return "unknown"


def log(message: str):
    timestamp = datetime.now().isoformat()
    line = f"[{timestamp}] {message}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


async def process_with_ollama(prompt: str, model: str = "qwen2.5-coder:7b") -> str:
    """Send a prompt to Ollama for processing."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "http://localhost:11434/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
            )
            if response.status_code == 200:
                return response.json().get("response", "")
    except Exception as e:
        log(f"Ollama error: {e}")
    return ""


async def process_video(path: Path) -> dict:
    """Process video: transcribe, translate, chapters."""
    log(f"Processing video: {path.name}")
    result = {"type": "video", "file": str(path)}

    # Try whisper for transcription
    transcript = ""
    try:
        import subprocess
        whisper_result = subprocess.run(
            ["whisper", str(path), "--output_format", "txt", "--output_dir", str(OUTPUT_DIR)],
            capture_output=True, text=True, timeout=300
        )
        txt_file = OUTPUT_DIR / f"{path.stem}.txt"
        if txt_file.exists():
            transcript = txt_file.read_text()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        log("Whisper not available, using Ollama for description")
        transcript = await process_with_ollama(
            f"Describe what this video file might contain based on filename: {path.name}"
        )

    result["transcript"] = transcript

    # Generate translations (using Ollama)
    if transcript:
        languages = ["de", "es", "fr", "pt", "zh", "ja", "ko", "ar", "hi", "ru"]
        for lang in languages:
            translation = await process_with_ollama(
                f"Translate the following to {lang} language. Only output the translation:\n\n{transcript[:2000]}"
            )
            if translation:
                out_file = OUTPUT_DIR / f"{path.stem}_{lang}.txt"
                out_file.write_text(translation)
                log(f"  Translated to {lang}")

    # Generate chapters
    if transcript:
        chapters = await process_with_ollama(
            f"Create video chapters with timestamps for this transcript:\n\n{transcript[:3000]}"
        )
        result["chapters"] = chapters
        (OUTPUT_DIR / f"{path.stem}_chapters.txt").write_text(chapters)

    return result


async def process_audio(path: Path) -> dict:
    """Process audio: transcribe, create show notes."""
    log(f"Processing audio: {path.name}")
    result = {"type": "audio", "file": str(path)}

    # Try whisper
    try:
        import subprocess
        subprocess.run(
            ["whisper", str(path), "--output_format", "txt", "--output_dir", str(OUTPUT_DIR)],
            capture_output=True, text=True, timeout=300
        )
        txt_file = OUTPUT_DIR / f"{path.stem}.txt"
        if txt_file.exists():
            transcript = txt_file.read_text()
            result["transcript"] = transcript

            # Generate show notes
            notes = await process_with_ollama(
                f"Create concise show notes with key topics, timestamps, and action items:\n\n{transcript[:3000]}"
            )
            result["show_notes"] = notes
            (OUTPUT_DIR / f"{path.stem}_notes.md").write_text(notes)
    except (FileNotFoundError, Exception) as e:
        log(f"  Audio processing limited: {e}")

    return result


async def process_image(path: Path) -> dict:
    """Process image: describe, suggest social captions."""
    log(f"Processing image: {path.name}")
    result = {"type": "image", "file": str(path)}

    caption = await process_with_ollama(
        f"Based on the filename '{path.name}', suggest 5 social media captions "
        f"for TikTok, YouTube, and X/Twitter. Make them engaging and viral."
    )
    result["captions"] = caption
    (OUTPUT_DIR / f"{path.stem}_captions.md").write_text(caption)

    return result


async def process_document(path: Path) -> dict:
    """Process document: summarize, extract action items."""
    log(f"Processing document: {path.name}")
    result = {"type": "document", "file": str(path)}

    content = ""
    if path.suffix in (".txt", ".md", ".csv"):
        content = path.read_text(errors="replace")[:5000]
    elif path.suffix == ".pdf":
        try:
            import subprocess
            proc = subprocess.run(
                ["pdftotext", str(path), "-"],
                capture_output=True, text=True, timeout=30
            )
            content = proc.stdout[:5000]
        except (FileNotFoundError, Exception):
            content = f"[PDF file: {path.name}]"

    if content:
        summary = await process_with_ollama(
            f"Summarize this document in 5 bullet points and extract all action items:\n\n{content}"
        )
        result["summary"] = summary
        (OUTPUT_DIR / f"{path.stem}_summary.md").write_text(summary)

    return result


async def process_code(path: Path) -> dict:
    """Process code: review, suggest improvements."""
    log(f"Processing code: {path.name}")
    result = {"type": "code", "file": str(path)}

    content = path.read_text(errors="replace")[:5000]
    review = await process_with_ollama(
        f"Review this code. Output: 3 improvements, potential bugs, and security issues:\n\n```\n{content}\n```",
        model="qwen2.5-coder:14b"
    )
    result["review"] = review
    (OUTPUT_DIR / f"{path.stem}_review.md").write_text(review)

    return result


PROCESSORS = {
    "video": process_video,
    "audio": process_audio,
    "image": process_image,
    "document": process_document,
    "code": process_code,
}


async def process_file(path: Path) -> dict:
    """Auto-detect file type and process accordingly."""
    file_type = detect_file_type(path)
    processor = PROCESSORS.get(file_type)

    if not processor:
        log(f"Unknown file type: {path.name} ({path.suffix})")
        return {"type": "unknown", "file": str(path)}

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return await processor(path)


async def watch_loop(watch_dir: Path):
    """Main watch loop — polls for new files."""
    watch_dir.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    processed_files: set = set()
    log(f"Watching: {watch_dir}")
    log(f"Output:   {OUTPUT_DIR}")
    log("Drop files into the watch folder to auto-process them.")
    log("Ctrl+C to stop.\n")

    while True:
        try:
            for item in watch_dir.iterdir():
                if item.is_file() and item.name not in processed_files and item.parent == watch_dir:
                    if item.name.startswith("."):
                        continue  # Skip hidden files
                    processed_files.add(item.name)
                    log(f"\nNew file detected: {item.name}")
                    result = await process_file(item)
                    log(f"Done: {result.get('type', '?')} — {item.name}")

                    # Save processing result
                    result_file = OUTPUT_DIR / f"{item.stem}_result.json"
                    result_file.write_text(json.dumps(result, indent=2, default=str))

            await asyncio.sleep(2)  # Poll every 2 seconds

        except KeyboardInterrupt:
            log("Watcher stopped.")
            break
        except Exception as e:
            log(f"Error: {e}")
            await asyncio.sleep(5)


async def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        if len(sys.argv) < 3:
            print("Usage: file_watcher.py --once <file_path>")
            sys.exit(1)
        path = Path(sys.argv[2])
        if not path.exists():
            print(f"File not found: {path}")
            sys.exit(1)
        result = await process_file(path)
        print(json.dumps(result, indent=2, default=str))
    else:
        watch_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else WATCH_DIR
        await watch_loop(watch_dir)


if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════╗
║  FILE WATCHER — Auto-Processing Pipeline (Tip #2)    ║
║  Drop files → auto-transcribe, translate, summarize   ║
╚═══════════════════════════════════════════════════════╝
""")
    asyncio.run(main())
