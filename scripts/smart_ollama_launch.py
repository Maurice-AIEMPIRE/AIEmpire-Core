#!/usr/bin/env python3
"""
Smart Ollama Launcher
======================
Intelligent model lifecycle manager for 16GB Apple Silicon Macs.

Features:
  - Auto-selects the best model for the task based on available RAM
  - Pre-loads/unloads models to avoid swap thrashing
  - Monitors memory pressure during inference
  - Supports model pooling with automatic eviction
  - Benchmarks models to find the fastest config for YOUR hardware

Usage:
  python3 scripts/smart_ollama_launch.py                    # Interactive test
  python3 scripts/smart_ollama_launch.py --benchmark        # Benchmark all models
  python3 scripts/smart_ollama_launch.py --optimize         # Auto-configure Ollama
  python3 scripts/smart_ollama_launch.py --clean            # Unload all models

Designed for: Apple M4, 16GB Unified Memory, macOS
"""

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import httpx
import psutil

# ═══════════════════════════════════════════════════════════════════
# Hardware Profile
# ═══════════════════════════════════════════════════════════════════

@dataclass
class HardwareProfile:
    """Detected hardware capabilities."""
    chip: str = ""
    total_ram_gb: float = 0.0
    cpu_cores: int = 0
    perf_cores: int = 0
    eff_cores: int = 0
    gpu_cores: int = 0
    arch: str = ""

    @classmethod
    def detect(cls) -> "HardwareProfile":
        """Auto-detect Mac hardware."""
        profile = cls()

        try:
            profile.chip = subprocess.check_output(
                ["sysctl", "-n", "machdep.cpu.brand_string"], text=True
            ).strip()
        except Exception:
            profile.chip = "Unknown"

        try:
            ram_bytes = int(subprocess.check_output(
                ["sysctl", "-n", "hw.memsize"], text=True
            ).strip())
            profile.total_ram_gb = ram_bytes / (1024 ** 3)
        except Exception:
            profile.total_ram_gb = 16.0

        try:
            profile.cpu_cores = int(subprocess.check_output(
                ["sysctl", "-n", "hw.ncpu"], text=True
            ).strip())
        except Exception:
            profile.cpu_cores = 10

        try:
            profile.perf_cores = int(subprocess.check_output(
                ["sysctl", "-n", "hw.perflevel0.logicalcpu"], text=True
            ).strip())
        except Exception:
            profile.perf_cores = 4

        try:
            profile.eff_cores = int(subprocess.check_output(
                ["sysctl", "-n", "hw.perflevel1.logicalcpu"], text=True
            ).strip())
        except Exception:
            profile.eff_cores = 6

        profile.gpu_cores = 10  # M4 standard
        profile.arch = subprocess.check_output(
            ["uname", "-m"], text=True
        ).strip()

        return profile

    @property
    def safe_model_budget_gb(self) -> float:
        """Max GB we should allocate to models (leave 6GB for macOS + apps)."""
        return max(self.total_ram_gb - 6.0, 4.0)

    @property
    def optimal_threads(self) -> int:
        """Optimal thread count — use only performance cores."""
        return self.perf_cores

    def __str__(self) -> str:
        return (
            f"  Chip: {self.chip}\n"
            f"  RAM: {self.total_ram_gb:.0f}GB (budget: {self.safe_model_budget_gb:.0f}GB for models)\n"
            f"  CPU: {self.cpu_cores} cores ({self.perf_cores}P + {self.eff_cores}E)\n"
            f"  GPU: {self.gpu_cores} cores (Metal 4)\n"
            f"  Arch: {self.arch}"
        )


# ═══════════════════════════════════════════════════════════════════
# Model Registry — Optimized for 16GB
# ═══════════════════════════════════════════════════════════════════

@dataclass
class ModelSpec:
    """Specification for a locally available model."""
    name: str
    size_gb: float
    params: str
    quant: str
    speed_class: str  # "fast", "medium", "slow"
    quality_class: str  # "high", "medium", "low"
    best_for: list[str] = field(default_factory=list)
    priority: int = 0  # Higher = preferred when budget allows

# Optimal model lineup for 16GB M4
# Strategy: Keep only what fits. Prefer quality/speed balance.
RECOMMENDED_MODELS: list[ModelSpec] = [
    # === Tier 1: Daily Drivers (fit comfortably in 10GB budget) ===
    ModelSpec(
        name="qwen2.5-coder:7b",
        size_gb=4.7, params="7B", quant="Q4_K_M",
        speed_class="fast", quality_class="high",
        best_for=["code", "refactor", "fix", "implement"],
        priority=100,
    ),
    ModelSpec(
        name="deepseek-r1:8b",
        size_gb=5.2, params="8B", quant="Q4_K_M",
        speed_class="medium", quality_class="high",
        best_for=["reasoning", "planning", "review", "qa", "architecture"],
        priority=90,
    ),

    # === Tier 2: Lightweight Specialists ===
    ModelSpec(
        name="codellama:7b",
        size_gb=3.8, params="7B", quant="Q4_0",
        speed_class="fast", quality_class="medium",
        best_for=["code", "completion", "infill"],
        priority=60,
    ),
    ModelSpec(
        name="phi4-mini:latest",
        size_gb=2.5, params="3.8B", quant="Q4_K_M",
        speed_class="very_fast", quality_class="medium",
        best_for=["quick_tasks", "formatting", "simple_code", "chat"],
        priority=50,
    ),

    # === Tier 3: Heavy (use only when needed, one at a time) ===
    ModelSpec(
        name="qwen2.5-coder:14b",
        size_gb=9.0, params="14B", quant="Q4_K_M",
        speed_class="slow", quality_class="very_high",
        best_for=["architecture", "complex_refactor", "critical_code"],
        priority=40,  # Lower priority because it eats the whole budget
    ),
    ModelSpec(
        name="deepseek-r1:7b",
        size_gb=4.7, params="7B", quant="Q4_K_M",
        speed_class="medium", quality_class="high",
        best_for=["reasoning", "planning"],
        priority=70,
    ),
]

# Models that are TOO BIG for comfortable use on 16GB
MODELS_TO_AVOID = [
    "qwen3-coder:latest",   # 18GB — will swap like crazy
    "glm-4.7-flash:latest", # 19GB — completely unusable on 16GB
]


# ═══════════════════════════════════════════════════════════════════
# Ollama Manager
# ═══════════════════════════════════════════════════════════════════

class OllamaManager:
    """Intelligent Ollama model lifecycle manager."""

    def __init__(self, base_url: str = "http://127.0.0.1:11434"):
        self.base_url = base_url
        self.hw = HardwareProfile.detect()
        self._client = httpx.Client(timeout=30.0)

    def is_running(self) -> bool:
        """Check if Ollama is running."""
        try:
            r = self._client.get(f"{self.base_url}/api/tags")
            return r.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False

    def start_ollama(self) -> bool:
        """Start Ollama if not running."""
        if self.is_running():
            return True

        print("🚀 Starting Ollama...")
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        for _ in range(30):
            time.sleep(1)
            if self.is_running():
                print("✅ Ollama started")
                return True
        print("❌ Ollama failed to start within 30 seconds")
        return False

    def get_loaded_models(self) -> list[dict[str, Any]]:
        """Get currently loaded models from Ollama."""
        try:
            r = self._client.get(f"{self.base_url}/api/ps")
            r.raise_for_status()
            return r.json().get("models", [])
        except Exception:
            return []

    def get_available_models(self) -> list[str]:
        """Get all downloaded models."""
        try:
            r = self._client.get(f"{self.base_url}/api/tags")
            r.raise_for_status()
            return [m["name"] for m in r.json().get("models", [])]
        except Exception:
            return []

    def get_memory_state(self) -> dict[str, float]:
        """Get current memory state."""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        return {
            "ram_total_gb": mem.total / (1024 ** 3),
            "ram_available_gb": mem.available / (1024 ** 3),
            "ram_used_pct": mem.percent,
            "swap_used_gb": swap.used / (1024 ** 3),
            "swap_total_gb": swap.total / (1024 ** 3),
        }

    def get_loaded_vram_gb(self) -> float:
        """Total VRAM consumed by loaded models."""
        models = self.get_loaded_models()
        total = sum(
            m.get("size_vram", m.get("size", 0)) for m in models
        )
        return total / (1024 ** 3)

    def unload_model(self, model_name: str) -> bool:
        """Unload a specific model from memory."""
        try:
            r = self._client.post(
                f"{self.base_url}/api/generate",
                json={"model": model_name, "keep_alive": 0}
            )
            return r.status_code == 200
        except Exception:
            return False

    def unload_all(self) -> int:
        """Unload all models from memory."""
        models = self.get_loaded_models()
        count = 0
        for m in models:
            name = m.get("name", "")
            if name:
                print(f"  🗑️  Unloading {name}...")
                if self.unload_model(name):
                    count += 1
        return count

    def preload_model(self, model_name: str) -> bool:
        """Pre-load a model into memory (warm it up)."""
        try:
            print(f"  ⏳ Pre-loading {model_name}...")
            r = self._client.post(
                f"{self.base_url}/api/generate",
                json={"model": model_name, "prompt": "", "keep_alive": "10m"},
                timeout=120.0,
            )
            return r.status_code == 200
        except Exception as e:
            print(f"  ❌ Failed to preload {model_name}: {e}")
            return False

    def ensure_model_loaded(self, model_name: str) -> bool:
        """
        Smart model loading: ensure model is in memory, evicting others if needed.
        Only one model at a time for 16GB systems.
        """
        loaded = self.get_loaded_models()
        loaded_names = [m["name"] for m in loaded]

        # Already loaded?
        if model_name in loaded_names:
            return True

        # Need to find model spec to check size
        spec = None
        for s in RECOMMENDED_MODELS:
            if s.name == model_name:
                spec = s
                break

        model_size_gb = spec.size_gb if spec else 5.0  # conservative estimate

        # Check if we have budget
        current_vram = self.get_loaded_vram_gb()
        budget = self.hw.safe_model_budget_gb

        if current_vram + model_size_gb > budget:
            # Evict everything — on 16GB we can only run 1 model at a time
            print(f"  📦 Memory budget exceeded ({current_vram:.1f}+{model_size_gb:.1f} > {budget:.0f}GB)")
            self.unload_all()
            time.sleep(1)

        return self.preload_model(model_name)

    def select_best_model(self, task_type: str = "code") -> str:
        """
        Select the best available model for a task type.
        Considers what's downloaded AND what fits in memory.

        Task types: code, fix, architecture, reasoning, qa, quick, chat
        """
        available = self.get_available_models()

        # Normalize available names (remove :latest suffix for matching)
        available_set = set()
        for a in available:
            available_set.add(a)
            if ":" not in a:
                available_set.add(f"{a}:latest")

        # Find matching models
        candidates: list[ModelSpec] = []
        for spec in RECOMMENDED_MODELS:
            # Check if model is downloaded
            if spec.name not in available_set:
                continue

            # Check if it fits in budget
            if spec.size_gb > self.hw.safe_model_budget_gb:
                continue

            # Check if task matches
            if task_type in spec.best_for or "code" in spec.best_for:
                candidates.append(spec)

        if not candidates:
            # Fallback: just pick the smallest available model
            for spec in sorted(RECOMMENDED_MODELS, key=lambda s: s.size_gb):
                if spec.name in available_set:
                    return spec.name
            return "qwen2.5-coder:7b"  # ultimate fallback

        # Sort by priority (highest first), then by size (smallest first for ties)
        candidates.sort(key=lambda s: (-s.priority, s.size_gb))
        return candidates[0].name

    def chat(
        self,
        model: str,
        prompt: str,
        system: str = "",
        stream: bool = True,
        temperature: float = 0.2,
        num_ctx: int = 4096,
    ) -> str:
        """Send a chat request with optimized parameters."""
        self.ensure_model_loaded(model)

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_ctx": num_ctx,
                "num_thread": self.hw.optimal_threads,
                "num_gpu": 99,  # Offload everything to Metal GPU
                "num_batch": 512,  # Optimal for M4
            },
        }

        if not stream:
            r = self._client.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=300.0,
            )
            r.raise_for_status()
            return r.json().get("message", {}).get("content", "")

        # Streaming response
        full_content = []
        with self._client.stream(
            "POST", f"{self.base_url}/api/chat",
            json=payload, timeout=300.0,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        full_content.append(content)
                        print(content, end="", flush=True)
                    if chunk.get("done"):
                        # Print performance stats
                        duration = chunk.get("total_duration", 0) / 1e9
                        tokens = chunk.get("eval_count", 0)
                        prompt_eval = chunk.get("prompt_eval_count", 0)
                        if duration > 0 and tokens > 0:
                            tps = tokens / duration
                            print(f"\n\n{DIM}⚡ {tokens} tokens in {duration:.1f}s ({tps:.1f} tok/s) | prompt: {prompt_eval} tokens{NC}")
                        break
                except json.JSONDecodeError:
                    continue

        return "".join(full_content)


# ANSI colors (also used in chat output)
DIM = "\033[2m"
NC = "\033[0m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
CYAN = "\033[0;36m"
BOLD = "\033[1m"
MAGENTA = "\033[0;35m"

# ═══════════════════════════════════════════════════════════════════
# Benchmark
# ═══════════════════════════════════════════════════════════════════

def benchmark_models(mgr: OllamaManager) -> None:
    """Benchmark all available models for speed and quality."""
    print(f"\n{BOLD}{CYAN}🏁 Benchmarking Models on {mgr.hw.chip}{NC}\n")

    available = set(mgr.get_available_models())
    test_prompt = "Write a Python function that checks if a number is prime. Include type hints and a docstring."

    results = []

    for spec in RECOMMENDED_MODELS:
        if spec.name not in available:
            continue

        if spec.size_gb > mgr.hw.safe_model_budget_gb:
            print(f"  ⏭️  {spec.name} — skipped (too large: {spec.size_gb}GB)")
            continue

        print(f"\n  📊 Testing {spec.name} ({spec.params}, {spec.quant})...")

        # Unload everything first for clean measurement
        mgr.unload_all()
        time.sleep(2)

        try:
            t0 = time.time()
            # Use non-streaming for accurate timing
            r = mgr._client.post(
                f"{mgr.base_url}/api/chat",
                json={
                    "model": spec.name,
                    "messages": [{"role": "user", "content": test_prompt}],
                    "stream": False,
                    "options": {
                        "temperature": 0.2,
                        "num_ctx": 2048,
                        "num_thread": mgr.hw.optimal_threads,
                        "num_gpu": 99,
                        "num_batch": 512,
                    },
                },
                timeout=180.0,
            )
            t1 = time.time()
            r.raise_for_status()
            data = r.json()

            duration = t1 - t0
            tokens = data.get("eval_count", 0)
            prompt_tokens = data.get("prompt_eval_count", 0)
            tps = tokens / duration if duration > 0 else 0
            content = data.get("message", {}).get("content", "")

            results.append({
                "model": spec.name,
                "params": spec.params,
                "quant": spec.quant,
                "size_gb": spec.size_gb,
                "total_time_s": round(duration, 1),
                "tokens_generated": tokens,
                "tokens_per_sec": round(tps, 1),
                "output_length": len(content),
            })

            print(f"     ⚡ {tokens} tokens in {duration:.1f}s = {tps:.1f} tok/s")

        except Exception as e:
            print(f"     ❌ Failed: {e}")

    # Print results table
    if results:
        print(f"\n{BOLD}{'═' * 76}{NC}")
        print(f"{BOLD}  {'Model':<25} {'Params':<8} {'Size':<7} {'Time':<8} {'Tok/s':<8} {'Tokens'}{NC}")
        print(f"  {'─' * 70}")

        results.sort(key=lambda r_item: r_item["tokens_per_sec"], reverse=True)
        for r_item in results:
            speed_color = GREEN if r_item["tokens_per_sec"] > 20 else (YELLOW if r_item["tokens_per_sec"] > 10 else RED)
            print(
                f"  {r_item['model']:<25} {r_item['params']:<8} {r_item['size_gb']:<7.1f} "
                f"{r_item['total_time_s']:<8.1f} {speed_color}{r_item['tokens_per_sec']:<8.1f}{NC} {r_item['tokens_generated']}"
            )

        print(f"\n  {GREEN}🏆 Fastest: {results[0]['model']} ({results[0]['tokens_per_sec']} tok/s){NC}")
        print(f"  {DIM}💡 Recommendation: Use fastest model as default, switch to larger only for complex tasks{NC}")

        # Save results
        results_path = Path(__file__).parent.parent / "logs" / "benchmark_results.json"
        results_path.parent.mkdir(exist_ok=True)
        with open(results_path, "w") as f:
            json.dump({
                "hardware": str(mgr.hw),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "results": results,
            }, f, indent=2)
        print(f"\n  {DIM}📁 Results saved to {results_path}{NC}")


# ═══════════════════════════════════════════════════════════════════
# Optimizer
# ═══════════════════════════════════════════════════════════════════

def optimize_system(mgr: OllamaManager) -> None:
    """Auto-configure Ollama and system for optimal performance."""
    print(f"\n{BOLD}{CYAN}⚡ Optimizing for {mgr.hw.chip} with {mgr.hw.total_ram_gb:.0f}GB RAM{NC}\n")

    # 1. Check and set env vars
    print(f"  {BOLD}1. Environment Variables{NC}")
    env_vars = {
        "OLLAMA_NUM_PARALLEL": "1",
        "OLLAMA_NUM_THREAD": str(mgr.hw.optimal_threads),
        "OLLAMA_FLASH_ATTENTION": "1",
        "OLLAMA_KV_CACHE_TYPE": "q8_0",
        "OLLAMA_MAX_LOADED_MODELS": "1",
        "OLLAMA_HOST": "http://127.0.0.1:11434",
    }

    zshrc = Path.home() / ".zshrc"
    existing_content = zshrc.read_text() if zshrc.exists() else ""

    updates_needed = []
    for key, value in env_vars.items():
        current = os.environ.get(key)
        if current == value:
            print(f"     {GREEN}✓{NC} {key}={value}")
        else:
            print(f"     {YELLOW}→{NC} {key}={value} (was: {current or 'unset'})")
            updates_needed.append((key, value))

    if updates_needed:
        print(f"\n  {BOLD}Writing to ~/.zshrc...{NC}")
        with open(zshrc, "a") as f:
            f.write("\n# ── AI Empire Ollama Optimization (auto-configured) ──\n")
            for key, value in updates_needed:
                # Remove old entry if exists
                line = f"export {key}={value}"
                if f"export {key}=" not in existing_content:
                    f.write(f"{line}\n")
                    print(f"     {GREEN}✓{NC} Added: {line}")
        print(f"     {DIM}Run: source ~/.zshrc{NC}")

    # 2. Unload heavy models
    print(f"\n  {BOLD}2. Model Cleanup{NC}")
    loaded = mgr.get_loaded_models()
    for m in loaded:
        name = m.get("name", "")
        size_gb = m.get("size_vram", m.get("size", 0)) / (1024 ** 3)
        if name in [avoid for avoid in MODELS_TO_AVOID]:
            print(f"     {RED}✗{NC} Unloading {name} ({size_gb:.1f}GB) — too large for 16GB")
            mgr.unload_model(name)
        else:
            print(f"     {GREEN}✓{NC} {name} ({size_gb:.1f}GB)")

    # 3. Check for oversized downloaded models
    print(f"\n  {BOLD}3. Downloaded Model Audit{NC}")
    available = mgr.get_available_models()
    for avoid_name in MODELS_TO_AVOID:
        if avoid_name in available:
            print(f"     {YELLOW}⚠{NC} {avoid_name} is downloaded but too large for comfortable use")
            print(f"       {DIM}Consider: ollama rm {avoid_name}{NC}")

    # 4. Recommend missing models
    print(f"\n  {BOLD}4. Recommended Models{NC}")
    for spec in RECOMMENDED_MODELS:
        status = f"{GREEN}✓ installed{NC}" if spec.name in available else f"{DIM}not installed{NC}"
        priority_icon = "⭐" if spec.priority >= 90 else "  "
        print(f"     {priority_icon} {spec.name:<25} {spec.size_gb:>4.1f}GB  [{spec.speed_class:<8}] [{spec.quality_class:<9}]  {status}")

    # Check if phi:q4 is available (tiny fast model for quick tasks)
    if "phi:q4" not in available and "phi4-mini:q4_K_M" not in available:
        print(f"\n     {YELLOW}💡 Tip: Pull phi:q4 for ultra-fast simple tasks (only 1.6GB){NC}")
        print(f"        {DIM}ollama pull phi:q4{NC}")

    # 5. Summary
    print(f"\n{BOLD}{'═' * 60}{NC}")
    print(f"  {BOLD}Optimal Config for {mgr.hw.chip} / {mgr.hw.total_ram_gb:.0f}GB:{NC}")
    print(f"  • Daily driver: qwen2.5-coder:7b (fast + high quality)")
    print(f"  • Reasoning:    deepseek-r1:8b (for planning/review)")
    print(f"  • Quick tasks:  phi:q4 (ultra-fast, good enough)")
    print(f"  • Heavy lift:   qwen2.5-coder:14b (only when needed)")
    print(f"  • Max 1 model loaded at a time")
    print(f"  • Threads: {mgr.hw.optimal_threads} (perf cores only)")
    print(f"  • GPU: All layers offloaded to Metal")
    print(f"{BOLD}{'═' * 60}{NC}")


# ═══════════════════════════════════════════════════════════════════
# Interactive Test
# ═══════════════════════════════════════════════════════════════════

def interactive_test(mgr: OllamaManager) -> None:
    """Run an interactive test to verify everything works."""
    print(f"\n{BOLD}{CYAN}🧪 Smart Ollama Launch — Interactive Test{NC}\n")
    print(mgr.hw)
    print()

    # Check memory
    mem = mgr.get_memory_state()
    print(f"  RAM: {mem['ram_used_pct']:.0f}% used ({mem['ram_available_gb']:.1f}GB free)")
    print(f"  Swap: {mem['swap_used_gb']:.1f}GB / {mem['swap_total_gb']:.1f}GB")
    print()

    # Select best model for coding
    model = mgr.select_best_model("code")
    print(f"  📌 Selected model: {BOLD}{model}{NC}")

    # Loaded models
    loaded = mgr.get_loaded_models()
    if loaded:
        print(f"  📦 Currently loaded:")
        for m in loaded:
            size = m.get("size_vram", m.get("size", 0)) / (1024 ** 3)
            print(f"     • {m['name']} ({size:.1f}GB)")
    else:
        print(f"  📦 No models currently loaded")
    print()

    # Quick test
    print(f"{BOLD}{'─' * 60}{NC}")
    print(f"  Testing {model} with a coding task...\n")

    response = mgr.chat(
        model=model,
        prompt="Write a Python one-liner that generates a list of the first 10 Fibonacci numbers using a lambda and reduce.",
        system="You are a Python expert. Be concise. Code only, no explanation.",
        temperature=0.1,
        num_ctx=2048,
    )

    print(f"\n{BOLD}{'─' * 60}{NC}")

    # Post-test memory check
    mem_after = mgr.get_memory_state()
    print(f"\n  RAM after: {mem_after['ram_used_pct']:.0f}% ({mem_after['ram_available_gb']:.1f}GB free)")
    print(f"  Swap after: {mem_after['swap_used_gb']:.1f}GB")

    if mem_after["swap_used_gb"] > 8.0:
        print(f"\n  {RED}⚠ High swap usage! Consider running: python3 {__file__} --optimize{NC}")
    else:
        print(f"\n  {GREEN}✅ System is running well!{NC}")


# ═══════════════════════════════════════════════════════════════════
# CLI Entry Point
# ═══════════════════════════════════════════════════════════════════

def main() -> None:
    """Main CLI entry point."""
    mgr = OllamaManager()

    if not mgr.start_ollama():
        print(f"{RED}❌ Cannot connect to Ollama. Please install and start it.{NC}")
        sys.exit(1)

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "--benchmark":
            benchmark_models(mgr)
        elif cmd == "--optimize":
            optimize_system(mgr)
        elif cmd == "--clean":
            print(f"\n{BOLD}🗑️  Unloading all models...{NC}")
            count = mgr.unload_all()
            print(f"  Unloaded {count} model(s)")
        elif cmd == "--status":
            print(f"\n{BOLD}📊 System Status{NC}\n")
            print(mgr.hw)
            print()
            mem = mgr.get_memory_state()
            print(f"  RAM: {mem['ram_used_pct']:.0f}% | Swap: {mem['swap_used_gb']:.1f}GB")
            loaded = mgr.get_loaded_models()
            print(f"  Models loaded: {len(loaded)}")
            for m in loaded:
                size = m.get("size_vram", m.get("size", 0)) / (1024 ** 3)
                print(f"    • {m['name']} ({size:.1f}GB)")
        elif cmd == "--select":
            task = sys.argv[2] if len(sys.argv) > 2 else "code"
            model = mgr.select_best_model(task)
            print(model)  # Clean output for scripting
        elif cmd == "--help":
            print(__doc__)
        else:
            print(f"Unknown command: {cmd}")
            print(__doc__)
    else:
        interactive_test(mgr)


if __name__ == "__main__":
    main()
