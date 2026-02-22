"use client";

import { useEffect, useState } from "react";

interface SystemStatus {
  name: string;
  status: "online" | "offline" | "unknown";
  url?: string;
}

interface RouterMuscle {
  name: string;
  calls: number;
  tokens: number;
  primary: string;
}

const CARD_STYLE: React.CSSProperties = {
  backgroundColor: "#161616",
  border: "1px solid #2a2a2a",
  borderRadius: "12px",
  padding: "20px",
  marginBottom: "16px",
};

const GRID_STYLE: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))",
  gap: "16px",
};

export default function Dashboard() {
  const [systems, setSystems] = useState<SystemStatus[]>([
    { name: "Ollama (LLMs)", status: "unknown", url: "http://localhost:11434" },
    { name: "LiteLLM Proxy", status: "unknown", url: "http://localhost:4000" },
    { name: "CRM", status: "unknown", url: "http://localhost:3500" },
    { name: "Atomic Reactor", status: "unknown", url: "http://localhost:8888" },
    { name: "Redis", status: "unknown", url: "http://localhost:6379" },
    { name: "ChromaDB", status: "unknown", url: "http://localhost:8000" },
  ]);

  const [muscles] = useState<RouterMuscle[]>([
    { name: "Brain", calls: 0, tokens: 0, primary: "Gemini Pro" },
    { name: "Coding", calls: 0, tokens: 0, primary: "Qwen 14B (local)" },
    { name: "Research", calls: 0, tokens: 0, primary: "Kimi K2.5" },
    { name: "Creative", calls: 0, tokens: 0, primary: "Gemini Flash" },
    { name: "Reasoning", calls: 0, tokens: 0, primary: "DeepSeek R1 (local)" },
    { name: "Fast", calls: 0, tokens: 0, primary: "Qwen 7B (local)" },
  ]);

  useEffect(() => {
    async function checkSystems() {
      const updated = await Promise.all(
        systems.map(async (sys) => {
          try {
            const res = await fetch(`/api/status?url=${encodeURIComponent(sys.url || "")}`, {
              signal: AbortSignal.timeout(3000),
            });
            const data = await res.json();
            return { ...sys, status: data.ok ? "online" as const : "offline" as const };
          } catch {
            return { ...sys, status: "offline" as const };
          }
        })
      );
      setSystems(updated);
    }
    checkSystems();
    const interval = setInterval(checkSystems, 30000);
    return () => clearInterval(interval);
  }, []);

  const onlineCount = systems.filter((s) => s.status === "online").length;

  return (
    <div>
      <h1 style={{ fontSize: "28px", marginBottom: "8px" }}>
        Dashboard
      </h1>
      <p style={{ color: "#888", marginBottom: "24px" }}>
        AI Empire system overview — {onlineCount}/{systems.length} systems online
      </p>

      <div style={GRID_STYLE}>
        {/* System Status Card */}
        <div style={CARD_STYLE}>
          <h2 style={{ fontSize: "16px", color: "#7dd3fc", marginTop: 0 }}>
            System Status
          </h2>
          {systems.map((sys) => (
            <div
              key={sys.name}
              style={{
                display: "flex",
                justifyContent: "space-between",
                padding: "8px 0",
                borderBottom: "1px solid #222",
              }}
            >
              <span>{sys.name}</span>
              <span
                style={{
                  color:
                    sys.status === "online"
                      ? "#4ade80"
                      : sys.status === "offline"
                      ? "#f87171"
                      : "#fbbf24",
                }}
              >
                {sys.status === "online"
                  ? "● Online"
                  : sys.status === "offline"
                  ? "● Offline"
                  : "● Checking..."}
              </span>
            </div>
          ))}
        </div>

        {/* Multi-Muscle Router Card */}
        <div style={CARD_STYLE}>
          <h2 style={{ fontSize: "16px", color: "#7dd3fc", marginTop: 0 }}>
            Multi-Muscle Router
          </h2>
          <p style={{ color: "#888", fontSize: "13px", marginBottom: "12px" }}>
            Each task type routes to a specialized model
          </p>
          {muscles.map((m) => (
            <div
              key={m.name}
              style={{
                display: "flex",
                justifyContent: "space-between",
                padding: "8px 0",
                borderBottom: "1px solid #222",
              }}
            >
              <span>
                🦾 {m.name}
              </span>
              <span style={{ color: "#888", fontSize: "13px" }}>
                {m.primary}
              </span>
            </div>
          ))}
        </div>

        {/* Revenue Pipeline Card */}
        <div style={CARD_STYLE}>
          <h2 style={{ fontSize: "16px", color: "#7dd3fc", marginTop: 0 }}>
            Revenue Pipeline
          </h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {[
              { channel: "Gumroad Products", range: "27-149 EUR", status: "Ready" },
              { channel: "Fiverr/Upwork", range: "50-5000 EUR", status: "Ready" },
              { channel: "BMA Consulting", range: "2000-10000 EUR", status: "Ready" },
              { channel: "Agent Builders Club", range: "29 EUR/mo", status: "Ready" },
              { channel: "X/Twitter Leads", range: "Organic", status: "Draft Only" },
            ].map((ch) => (
              <div
                key={ch.channel}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  padding: "8px 0",
                  borderBottom: "1px solid #222",
                }}
              >
                <span>{ch.channel}</span>
                <span style={{ color: "#fbbf24", fontSize: "13px" }}>
                  {ch.range} — {ch.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Cron Jobs Card */}
        <div style={CARD_STYLE}>
          <h2 style={{ fontSize: "16px", color: "#7dd3fc", marginTop: 0 }}>
            Cron Jobs (OpenClaw)
          </h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {[
              { time: "07:00", name: "Reverse Prompt (3x/day)", type: "strategy" },
              { time: "07:30", name: "System Health Check", type: "ops" },
              { time: "08:00", name: "Trend Scan", type: "research" },
              { time: "09:00", name: "Short-Form Scripts", type: "content" },
              { time: "10:00", name: "Offer Packaging", type: "product" },
              { time: "12:00", name: "Content Calendar", type: "content" },
              { time: "14:00", name: "YouTube Outline", type: "content" },
              { time: "17:00", name: "Engagement Playbook", type: "community" },
              { time: "19:00", name: "KPI Snapshot", type: "analytics" },
            ].map((job) => (
              <div
                key={job.name}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  padding: "4px 0",
                  fontSize: "13px",
                }}
              >
                <span>
                  <span style={{ color: "#4ade80" }}>{job.time}</span>{" "}
                  {job.name}
                </span>
                <span style={{ color: "#888" }}>{job.type}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div style={{ ...CARD_STYLE, marginTop: "16px" }}>
        <h2 style={{ fontSize: "16px", color: "#7dd3fc", marginTop: 0 }}>
          Quick Actions
        </h2>
        <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
          {[
            { label: "Trigger Reverse Prompt", endpoint: "/api/reverse-prompt" },
            { label: "Check Router Status", endpoint: "/api/router" },
            { label: "Run Vibe Code", endpoint: "#vibe" },
          ].map((action) => (
            <button
              key={action.label}
              onClick={() => {
                if (action.endpoint.startsWith("/api")) {
                  fetch(action.endpoint).then((r) => r.json()).then(alert);
                }
              }}
              style={{
                padding: "10px 20px",
                backgroundColor: "#1e3a5f",
                color: "#7dd3fc",
                border: "1px solid #2563eb",
                borderRadius: "8px",
                cursor: "pointer",
                fontSize: "14px",
              }}
            >
              {action.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
