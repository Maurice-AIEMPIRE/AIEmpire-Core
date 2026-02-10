#!/usr/bin/env python3
"""
VIDEO RENDERER (MVP)
Role: Converts text scripts to simple MP4 videos.
Dependency: ffmpeg
"""

import os
import time
import subprocess
from pathlib import Path

# Config
SCRIPTS_DIR = Path(__file__).parent / "products" / "TIKTOK_SCRIPTS"
RENDER_DIR = Path(__file__).parent / "products" / "RENDERED"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
CHECK_INTERVAL = 60

def wrap_text(text: str, max_chars: int = 30) -> str:
    """Simple text wrapper."""
    words = text.split()
    lines = []
    current_line: list[str] = []
    current_len = 0
    
    for word in words:
        if current_len + len(word) > max_chars:
            lines.append(" ".join(current_line))
            current_line = [word]
            current_len = len(word)
        else:
            current_line.append(word)
            current_len += len(word) + 1
            
    if current_line:
        lines.append(" ".join(current_line))
    return "\n".join(lines)

def render_video(script_path):
    print(f"🎬 Rendering: {script_path.name}")
    
    # Extract content (Naive parsing)
    with open(script_path, "r") as f:
        content = f.read()
    
    # Create a temporary text image instruction or use drawtext filter directly
    # Ideally we'd parse the 'TEXT OVERLAY' part, but for MVP we just render the whole thing or a summary.
    
    # Sanitize content for drawtext
    # Escape special characters for FFmpeg
    raw_content = wrap_text(content[:500])
    sanitized_content = raw_content.replace(":", "\\:").replace("'", "").replace("%", "")
    
    output_file = RENDER_DIR / f"{script_path.stem}.mp4"
    if output_file.exists():
        return

    # FFmpeg command to create a black video with scrolling text
    # This is a complex command.
    cmd = [
        "ffmpeg",
        "-f", "lavfi", "-i", "color=c=black:s=1080x1920:d=15",
        "-vf", f"drawtext=text='{sanitized_content}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2:line_spacing=20",
        "-y", str(output_file)
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ Render Success: {output_file.name}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Render Failed: {e}")
        # Make a dummy file to avoid retry loop
        with open(output_file, "w") as f:
            f.write("Render Failed")

def run_renderer():
    print("📹 VIDEO RENDERER ACTIVE")
    print(f"📂 Watching: {SCRIPTS_DIR}")
    
    while True:
        # Find scripts that don't have a rendered version
        scripts = list(SCRIPTS_DIR.glob("*.md"))
        for script in scripts:
            rendered_video = RENDER_DIR / f"{script.stem}.mp4"
            if not rendered_video.exists():
                render_video(script)
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    run_renderer()
