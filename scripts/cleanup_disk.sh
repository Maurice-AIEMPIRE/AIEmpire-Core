#!/bin/bash
# 🧹 AI Empire — Disk Cleanup
# Frees up disk space by removing unused or too-large models.

echo "Checking for large/unused models..."

# List of models to remove (Too big for 16GB RAM or redundant)
MODELS_TO_REMOVE=(
    "qwen3-coder:latest"      # 18GB - Too big
    "glm-4.7-flash:latest"    # 19GB - Too big
    "qwen2.5-coder:14b"       # 9GB - 7b is sufficient and faster
    "codellama:7b"            # 3.8GB - Redundant (qwen is better)
)

TOTAL_FREED=0

for model in "${MODELS_TO_REMOVE[@]}"; do
    if ollama list | grep -q "${model%%:*}"; then
        echo "🗑️  Removing $model..."
        ollama rm "$model"
        echo "   ✅ Removed."
    else
        echo "   ℹ️  $model not found (ok)."
    fi
done

echo ""
echo "✨ Cleanup complete!"
echo "   Run 'ollama list' to see remaining models."
