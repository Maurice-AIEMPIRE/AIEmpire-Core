"""
CONTENT ENGINE
The heart of Aura Farmer. 
Generates scripts, audio, and assembles the final video.
"""

import os
import subprocess
import logging
from pathlib import Path
import random
import time

logger = logging.getLogger(__name__)

class ContentEngine:
    def __init__(self, assets_dir, temp_dir, output_dir):
        self.assets_dir = Path(assets_dir)
        self.temp_dir = Path(temp_dir)
        self.output_dir = Path(output_dir)
        self.model = "phi4-mini:latest" # Updated to available model

    def produce_video(self, topic):
        """Orchestrates the creation of a single video."""
        timestamp = int(time.time())
        
        # 1. Script Generation
        script = self._generate_script(topic)
        if not script:
            return None
        
        script_path = self.temp_dir / f"script_{timestamp}.txt"
        with open(script_path, "w") as f:
            f.write(script)
            
        # 2. Audio Generation
        audio_path = self.temp_dir / f"audio_{timestamp}.aiff" # 'say' outputs aiff by default
        self._generate_audio(script, audio_path)
        
        # 3. Choose Background
        bg_video = self._get_random_background()
        if not bg_video:
            logger.error("❌ No background video found in assets/backgrounds!")
            return None

        # 4. Assembly
        output_filename = f"aura_farm_{timestamp}.mp4"
        final_video_path = self.output_dir / output_filename
        self._assemble_video(audio_path, bg_video, final_video_path)
        
        return final_video_path

    def _generate_script(self, topic):
        """Calls local Ollama model to write a short viral script."""
        prompt = f"""Write a script for a 30-second viral TikTok video about: "{topic}".
        Style: Punchy, controversial, 'sigma male' grindset, or dark psychology.
        Format: Just the spoken text. No scene descriptions. No 'Host:' labels.
        Max 60 words.
        Start with a strong hook."""
        
        try:
            cmd = ["ollama", "run", self.model, prompt]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Ollama Error: {e}")
            return None
        except FileNotFoundError:
            logger.error("❌ Ollama not found! Is it installed?")
            return None

    def _generate_audio(self, text, output_path):
        """Uses macOS 'say' command for TTS."""
        # Voices: 'Daniel' (British), 'Fred' (Robot), 'Samantha' (US)
        # We can use 't' to check available voices: `say -v ?`
        try:
            cmd = ["say", "-v", "Daniel", "-o", str(output_path), text]
            subprocess.run(cmd, check=True)
            logger.info(f"🗣️ Audio generated: {output_path}")
        except Exception as e:
            logger.error(f"❌ TTS Error: {e}")

    def _get_random_background(self):
        """Picks a random .mp4 from assets/backgrounds. Generates a placeholder if empty."""
        bg_dir = self.assets_dir / "backgrounds"
        videos = list(bg_dir.glob("*.mp4"))
        
        if not videos:
            logger.warning("⚠️ No background videos found. Generating synthetic background for testing...")
            placeholder_path = self.temp_dir / "synthetic_bg.mp4"
            if not placeholder_path.exists():
                # Generate a 60s synthetic video using libavfilter
                # Mandelbrot pattern or simple color cycle
                cmd = [
                    "ffmpeg", "-f", "lavfi", "-i", "mandelbrot=s=1080x1920:r=30",
                    "-t", "60", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-y", str(placeholder_path)
                ]
                try:
                    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    logger.info("✅ Synthetic background created.")
                except subprocess.CalledProcessError:
                    return None
            return placeholder_path

        return random.choice(videos)

    def _assemble_video(self, audio_path, bg_path, output_path):
        """
        Uses FFmpeg to:
        1. Loop background video.
        2. Trim to audio length.
        3. Add audio.
        4. Add subtitles (Hardcoded simple centered text for MVP).
        """
        # Note: Complex subtitle styling requires a .ass file or complex filters.
        # For MVP, we will just merge audio and video.
        # Subtitles can be added by the user in TikTok editor or by a more advanced version later.
        
        try:
            # 1. Get audio duration
            # We can use ffprobe, but let's just let ffmpeg handle it with -shortest
            
            cmd = [
                "ffmpeg",
                "-y", # Overwrite
                "-stream_loop", "-1", # Loop input 0 (background)
                "-i", str(bg_path),
                "-i", str(audio_path),
                "-map", "0:v:0",
                "-map", "1:a:0",
                # "-c:v", "copy", # REMOVED: Cannot copy with filters
                # Re-encoding is needed to cut exactly or we use -shortest.
                # But -c:v copy + -shortest often fails to be exact with loop.
                # Let's try re-encoding for safety (slower but works).
                # Actually, specialized filter for subtitles would go here.
                "-shortest", # Stop when the shortest stream ends (audio)
                "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1", # Force 9:16
                str(output_path)
            ]
            
            # Subtitle attempt (simple drawtext if we wanted, but requires font config)
            # cmd.extend(["-vf", "subtitles=..."])
            
            logger.info(f"🎬 Assembling video...")
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logger.info(f"✨ Video Ready: {output_path}")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ FFmpeg Error: {e}")
        except FileNotFoundError:
             logger.error("❌ FFmpeg not found! Please install it.")
