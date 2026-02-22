import { NextResponse } from "next/server";

export async function GET() {
  const prompts = [
    "Based on what you know about me and my goals, what is the single highest-impact task we can work on RIGHT NOW?",
    "What is blocked or stalled that needs immediate attention?",
    "What quick win could we knock out in under 15 minutes?",
    "Is there anything I should know that I probably don't?",
    "Which revenue channel is closest to generating its first sale?",
    "What system is underperforming and how can we fix it?",
  ];

  const selected = prompts[Math.floor(Math.random() * prompts.length)];

  return NextResponse.json({
    reversePrompt: selected,
    allPrompts: prompts,
    tip: "Send this to your OpenClaw instead of giving it instructions. Let IT tell YOU what to work on.",
  });
}
