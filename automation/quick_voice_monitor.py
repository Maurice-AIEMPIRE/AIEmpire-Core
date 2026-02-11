#!/usr/bin/env python3
"""
Quick Voice Monitor Dashboard - Maurice's AI Empire
6 parallel monitoring windows + voice control
"""

import os
import sys
import time
import subprocess
import threading
import speech_recognition as sr
from datetime import datetime

class VoiceMonitor:
    def __init__(self):
        self.tmux_session = "empire_monitor"
        self.has_microphone = False

        # Try to setup microphone (optional)
        try:
            import speech_recognition as sr
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            # Calibrate microphone
            print("🎤 Calibrating microphone... Speak for 2 seconds")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
            print("✅ Microphone calibrated")
            self.has_microphone = True
        except (ImportError, OSError) as e:
            print(f"⚠️  No microphone available: {e}")
            print("💡 Running in dashboard-only mode")
            self.has_microphone = False)

    def setup_tmux_dashboard(self):
        """Setup 6-window tmux dashboard"""
        try:
            # Kill existing session if exists
            subprocess.run(["tmux", "kill-session", "-t", self.tmux_session],
                         capture_output=True, check=False)

            # Create new session
            subprocess.run(["tmux", "new-session", "-d", "-s", self.tmux_session],
                         check=True)

            # Create windows
            windows = [
                ("services", "watch -n 5 'docker ps --format \"table {{.Names}}\\t{{.Status}}\"'"),
                ("ollama", "watch -n 10 'curl -s http://localhost:11434/api/tags | jq -r \".models[].name\"'"),
                ("git", "watch -n 30 'git status --porcelain | wc -l && echo \"---\" && git log --oneline -5'"),
                ("queue", "watch -n 15 'ls -la automation/runs/ | tail -10'"),
                ("system", "watch -n 5 'top -l 1 | head -10'"),
                ("logs", "tail -f /tmp/empire_monitor.log 2>/dev/null || echo \"No logs yet\"")
            ]

            for i, (name, command) in enumerate(windows):
                if i == 0:
                    # First window already exists
                    subprocess.run(["tmux", "rename-window", "-t", f"{self.tmux_session}:0", name], check=True)
                    subprocess.run(["tmux", "send-keys", "-t", f"{self.tmux_session}:{name}", command, "C-m"], check=True)
                else:
                    subprocess.run(["tmux", "new-window", "-t", self.tmux_session, "-n", name], check=True)
                    subprocess.run(["tmux", "send-keys", "-t", f"{self.tmux_session}:{name}", command, "C-m"], check=True)

            print(f"✅ Tmux dashboard created: tmux attach -t {self.tmux_session}")

        except subprocess.CalledProcessError as e:
            print(f"❌ Tmux setup failed: {e}")

    def listen_for_commands(self):
        """Listen for voice commands (only if microphone available)"""
        if not self.has_microphone:
            print("⚠️  Voice control disabled - no microphone")
            return

        self.is_listening = True
        print("🎤 Listening for voice commands...")

        while self.is_listening:
            try:
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)

                try:
                    command = self.recognizer.recognize_google(audio, language='de-DE').lower()
                    print(f"🎤 Heard: {command}")
                    self.process_command(command)

                except sr.UnknownValueError:
                    pass  # No speech detected
                except sr.RequestError as e:
                    print(f"❌ Speech recognition error: {e}")

            except sr.WaitTimeoutError:
                pass  # Timeout, continue listening

    def process_command(self, command):
        """Process voice commands"""
        if "status" in command:
            print("📊 Running status check...")
            self.run_command("git status && echo '---' && docker ps")

        elif "commit" in command:
            print("💾 Running auto-commit...")
            self.run_command("python3 automation/scripts/auto_commit.py")

        elif "push" in command:
            print("⬆️ Pushing to remote...")
            self.run_command("git push origin master")

        elif "render" in command and "video" in command:
            print("🎬 Starting TikTok render...")
            self.run_command("bash automation/scripts/run_tiktok_live.sh")

        elif "content" in command:
            print("📝 Starting content factory...")
            self.run_command("python3 -m automation run --workflow content_factory")

        elif "stop" in command:
            print("🛑 Stopping voice monitor...")
            self.is_listening = False

        else:
            print(f"❓ Unknown command: {command}")

    def run_command(self, cmd):
        """Run shell command and log output"""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd="/Users/maurice/Documents/New project")
            if result.returncode == 0:
                print(f"✅ Command successful: {cmd}")
                if result.stdout:
                    print(result.stdout[:500])  # Limit output
            else:
                print(f"❌ Command failed: {cmd}")
                if result.stderr:
                    print(result.stderr[:500])
        except Exception as e:
            print(f"❌ Error running command: {e}")

    def start(self):
        """Start the voice monitor"""
        print("🚀 Starting Voice Monitor Dashboard...")

        # Setup tmux dashboard
        self.setup_tmux_dashboard()

        # Start voice listening only if microphone available
        if self.has_microphone:
            voice_thread = threading.Thread(target=self.listen_for_commands, daemon=True)
            voice_thread.start()
            print("✅ Voice Monitor active!")
            print("🎤 Say commands like: 'status', 'commit', 'push', 'render video', 'create content'")
        else:
            print("✅ Dashboard Monitor active!")
            print("💡 Voice control disabled - use tmux dashboard only")

        print("🖥️ Dashboard: tmux attach -t empire_monitor")

        # Keep main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping Voice Monitor...")
            if hasattr(self, 'is_listening'):
                self.is_listening = False

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Voice Monitor Dashboard")
    parser.add_argument("--tmux-only", action="store_true", help="Setup tmux dashboard only")
    parser.add_argument("--voice-only", action="store_true", help="Voice control only")

    args = parser.parse_args()

    monitor = VoiceMonitor()

    if args.tmux_only:
        monitor.setup_tmux_dashboard()
        print("✅ Tmux dashboard ready. Attach with: tmux attach -t empire_monitor")
    elif args.voice_only:
        monitor.listen_for_commands()
    else:
        monitor.start()