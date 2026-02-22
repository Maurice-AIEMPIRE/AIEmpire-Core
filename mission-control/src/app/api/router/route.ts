import { NextResponse } from "next/server";

export async function GET() {
  const muscles = {
    brain: { model: "Gemini Pro", provider: "gemini", cost: "paid" },
    coding: { model: "Qwen 2.5 Coder 14B", provider: "ollama", cost: "free" },
    research: { model: "Kimi K2.5", provider: "moonshot", cost: "free" },
    creative: { model: "Gemini Flash", provider: "gemini", cost: "cheap" },
    reasoning: { model: "DeepSeek R1 7B", provider: "ollama", cost: "free" },
    fast: { model: "Qwen 2.5 Coder 7B", provider: "ollama", cost: "free" },
  };

  return NextResponse.json({
    status: "multi-muscle-active",
    muscles,
    strategy: "Use the right model for each task type to save money and improve quality",
  });
}
