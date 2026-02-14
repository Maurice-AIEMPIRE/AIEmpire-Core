import { useState, useEffect, useCallback, useRef } from "react";
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, AreaChart, Area } from "recharts";

// ── API Config ──
const API_BASE = typeof window !== "undefined" && window.location.port === "3333"
  ? "" : "http://localhost:3333";

async function api(path, opts = {}) {
  try {
    const r = await fetch(`${API_BASE}/api${path}`, {
      headers: { "Content-Type": "application/json" },
      ...opts,
    });
    return await r.json();
  } catch {
    return null;
  }
}

// ── Colors ──
const C = {
  bg: "#0A0A1A", bg2: "#12122A", bg3: "#1A1A3E",
  card: "#161630", border: "#2A2A4A",
  accent: "#E94560", blue: "#4A90D9", gold: "#F5A623",
  green: "#27AE60", cyan: "#00D2FF",
  text: "#E8E8F0", text2: "#8888AA",
};

// ── Notification System ──
function Toast({ message, visible }) {
  return (
    <div style={{
      position: "fixed", top: 80, left: 16, right: 16, zIndex: 999,
      background: C.bg3, border: `1px solid ${C.accent}`, borderRadius: 14,
      padding: "14px 18px", textAlign: "center", fontSize: 13, fontWeight: 600,
      transition: "all .3s", opacity: visible ? 1 : 0,
      transform: visible ? "translateY(0)" : "translateY(-20px)",
      pointerEvents: "none",
    }}>{message}</div>
  );
}

// ── Badge Component ──
function Badge({ status }) {
  const colors = {
    active: { bg: "rgba(39,174,96,.15)", text: C.green },
    offline: { bg: "rgba(233,69,96,.15)", text: C.accent },
    ready: { bg: "rgba(245,166,35,.15)", text: C.gold },
    setup: { bg: "rgba(245,166,35,.15)", text: C.gold },
    restart: { bg: "rgba(245,166,35,.15)", text: C.gold },
  };
  const c = colors[status] || colors.offline;
  return (
    <span style={{
      fontSize: 11, fontWeight: 700, padding: "4px 10px", borderRadius: 20,
      background: c.bg, color: c.text, textTransform: "uppercase", letterSpacing: .5,
    }}>{status}</span>
  );
}

// ── Card ──
function Card({ children, style, onClick }) {
  return (
    <div onClick={onClick} style={{
      background: C.card, border: `1px solid ${C.border}`, borderRadius: 16,
      padding: 16, marginBottom: 12, cursor: onClick ? "pointer" : "default",
      transition: "border-color .15s", ...style,
    }}>{children}</div>
  );
}

// ── Section Header ──
function Section({ title }) {
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 8,
      padding: "20px 0 12px", fontSize: 13, fontWeight: 700,
      textTransform: "uppercase", letterSpacing: 1.5, color: C.text2,
    }}>
      {title}
      <div style={{ flex: 1, height: 1, background: C.border }} />
    </div>
  );
}

// ══════════════════════════════════════════
// DASHBOARD TAB
// ══════════════════════════════════════════
function Dashboard({ health, onAction, revenue }) {
  const rev = revenue?.current_month || 0;
  const target = revenue?.target || 10000;
  const pct = Math.min(100, (rev / target) * 100);

  const chartData = [
    { day: "Mo", v: 0 }, { day: "Di", v: 0 }, { day: "Mi", v: 0 },
    { day: "Do", v: 0 }, { day: "Fr", v: 0 }, { day: "Sa", v: 0 }, { day: "So", v: rev },
  ];

  const activeServices = health ? Object.values(health.services || {}).filter(s => s.status === "active").length : 0;

  return (
    <div>
      {/* Revenue Hero */}
      <Section title="Revenue" />
      <div style={{
        background: `linear-gradient(135deg, ${C.bg3}, ${C.card})`,
        border: `1px solid ${C.accent}`, borderRadius: 16,
        padding: 24, textAlign: "center", marginBottom: 12,
      }}>
        <div style={{ fontSize: 12, color: C.text2, textTransform: "uppercase", letterSpacing: 1 }}>Monatsumsatz</div>
        <div style={{ fontSize: 48, fontWeight: 900, color: C.accent }}>€{rev.toLocaleString()}</div>
        <div style={{ fontSize: 13, color: C.text2, marginTop: 4 }}>Ziel: €{target.toLocaleString()} | Monat 1</div>
        <div style={{ height: 6, background: C.bg, borderRadius: 3, marginTop: 16, overflow: "hidden" }}>
          <div style={{
            height: "100%", borderRadius: 3, width: `${pct}%`,
            background: `linear-gradient(90deg, ${C.accent}, ${C.gold})`, transition: "width .5s",
          }} />
        </div>
      </div>

      {/* Revenue Mini Chart */}
      <Card>
        <div style={{ height: 80 }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={C.accent} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={C.accent} stopOpacity={0} />
                </linearGradient>
              </defs>
              <Area type="monotone" dataKey="v" stroke={C.accent} fill="url(#colorRev)" strokeWidth={2} />
              <XAxis dataKey="day" tick={{ fontSize: 10, fill: C.text2 }} axisLine={false} tickLine={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* Key Stats */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        {[
          { label: "Services", value: `${activeServices}/7`, sub: "Aktiv", color: C.cyan },
          { label: "Tasks Heute", value: "24", sub: "+12 vs. gestern", color: C.gold },
          { label: "Leads", value: "0", sub: "Pipeline", color: C.green },
          { label: "Gold Nuggets", value: "15", sub: "Extrahiert", color: C.gold },
        ].map((s, i) => (
          <div key={i} style={{
            background: C.card, border: `1px solid ${C.border}`,
            borderRadius: 16, padding: 16, textAlign: "center",
          }}>
            <div style={{ fontSize: 12, color: C.text2, textTransform: "uppercase", letterSpacing: 1 }}>{s.label}</div>
            <div style={{ fontSize: 28, fontWeight: 800, color: s.color, margin: "4px 0" }}>{s.value}</div>
            <div style={{ fontSize: 11, color: C.text2 }}>{s.sub}</div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <Section title="Schnellaktionen" />
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
        {[
          { icon: "📝", label: "Content", action: "generate_content" },
          { icon: "🐝", label: "Swarm", action: "swarm_start" },
          { icon: "🏥", label: "Health Check", action: "health_check" },
          { icon: "💰", label: "Revenue Report", action: "revenue_report" },
          { icon: "🔄", label: "Git Push", action: "git_push" },
          { icon: "📋", label: "Neues Issue", action: "create_issue" },
          { icon: "🟢", label: "Redis Start", action: "start_redis" },
          { icon: "🗄️", label: "PostgreSQL", action: "start_postgresql" },
        ].map((a, i) => (
          <div key={i} onClick={() => onAction(a.action)} style={{
            background: C.bg3, border: `1px solid ${C.border}`, borderRadius: 14,
            padding: "16px 12px", textAlign: "center", cursor: "pointer",
          }}>
            <div style={{ fontSize: 28, marginBottom: 6 }}>{a.icon}</div>
            <div style={{ fontSize: 12, fontWeight: 600 }}>{a.label}</div>
          </div>
        ))}
      </div>

      {/* Activity Feed */}
      <Section title="Letzte Aktivität" />
      <Card>
        {[
          { text: "Mobile Command Center gebaut", time: "Gerade eben", color: C.accent },
          { text: "Empire API Server erstellt", time: "Vor 2 Min", color: C.cyan },
          { text: "System-Architektur Dokument (16 S.)", time: "Vor 15 Min", color: C.green },
          { text: "BMA Academy aufgesetzt", time: "Vor 20 Min", color: C.gold },
          { text: "Kimi Bridge + Universal Swarm", time: "Vor 30 Min", color: C.blue },
          { text: "500K Swarm iCloud Sync", time: "Vor 45 Min", color: C.accent },
        ].map((a, i) => (
          <div key={i} style={{
            display: "flex", gap: 12, padding: "10px 0",
            borderBottom: i < 5 ? `1px solid ${C.border}` : "none",
          }}>
            <div style={{ width: 8, height: 8, borderRadius: "50%", background: a.color, marginTop: 6, flexShrink: 0 }} />
            <div>
              <div style={{ fontSize: 13 }}>{a.text}</div>
              <div style={{ fontSize: 11, color: C.text2, marginTop: 2 }}>{a.time}</div>
            </div>
          </div>
        ))}
      </Card>
    </div>
  );
}

// ══════════════════════════════════════════
// SYSTEMS TAB
// ══════════════════════════════════════════
function Systems({ health, brains }) {
  const services = [
    { name: "Claude API", detail: "Opus 4.6 + Sonnet", key: "claude", status: "active" },
    { name: "Ollama", detail: "Port 11434 · qwen2.5", key: "ollama" },
    { name: "OpenClaw", detail: "Port 18789 · Agent", key: "openclaw" },
    { name: "GitHub Actions", detail: "9 Workflows · 24/7", key: "github_actions" },
    { name: "CRM Server", detail: "Port 3500 · Express.js", key: "crm" },
    { name: "Redis", detail: "Port 6379 · Queue", key: "redis" },
    { name: "PostgreSQL", detail: "Port 5432", key: "postgresql" },
  ];

  const brainData = [
    { icon: "🛡", name: "Brainstem", model: "Bash" },
    { icon: "🔭", name: "Neocortex", model: "Kimi" },
    { icon: "👑", name: "Prefrontal", model: "Claude" },
    { icon: "📢", name: "Temporal", model: "Kimi" },
    { icon: "📊", name: "Parietal", model: "Ollama" },
    { icon: "🔥", name: "Limbic", model: "Ollama" },
    { icon: "🔨", name: "Cerebellum", model: "Ollama" },
    { icon: "💾", name: "Hippocampus", model: "SQLite" },
  ];

  return (
    <div>
      {/* Brain System */}
      <Section title="Brain System (8 Hirne)" />
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8 }}>
        {brainData.map((b, i) => (
          <div key={i} style={{
            background: C.bg3, border: `1px solid ${C.border}`, borderRadius: 12,
            padding: "10px 6px", textAlign: "center",
          }}>
            <div style={{ fontSize: 22 }}>{b.icon}</div>
            <div style={{ fontSize: 10, color: C.text2, marginTop: 4, fontWeight: 600 }}>{b.name}</div>
            <div style={{ fontSize: 8, color: C.green, marginTop: 2 }}>{b.model}</div>
          </div>
        ))}
      </div>

      {/* Services */}
      <Section title="Infrastruktur" />
      <Card>
        {services.map((s, i) => {
          const st = s.status || health?.services?.[s.key]?.status || "offline";
          return (
            <div key={i} style={{
              display: "flex", justifyContent: "space-between", alignItems: "center",
              padding: "12px 0", borderBottom: i < services.length - 1 ? `1px solid ${C.border}` : "none",
            }}>
              <div>
                <div style={{ fontSize: 14, fontWeight: 600 }}>{s.name}</div>
                <div style={{ fontSize: 12, color: C.text2 }}>{s.detail}</div>
              </div>
              <Badge status={st === "active" ? "active" : st === "no_token" ? "ready" : "offline"} />
            </div>
          );
        })}
      </Card>

      {/* AI Model Routing */}
      <Section title="AI Modell-Routing" />
      <Card>
        {[
          { name: "Ollama (lokal)", pct: "95%", cost: "GRATIS", dot: "🟢" },
          { name: "Kimi K2.5", pct: "4%", cost: "$0.001/Task", dot: "🟢" },
          { name: "Claude Haiku", pct: "0.9%", cost: "$$", dot: "🟡" },
          { name: "Claude Opus", pct: "0.1%", cost: "$$$", dot: "🔴" },
        ].map((m, i) => (
          <div key={i} style={{
            display: "flex", justifyContent: "space-between", alignItems: "center",
            padding: "10px 0", borderBottom: i < 3 ? `1px solid ${C.border}` : "none",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span>{m.dot}</span>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600 }}>{m.name}</div>
                <div style={{ fontSize: 11, color: C.text2 }}>{m.cost}</div>
              </div>
            </div>
            <span style={{ fontSize: 14, fontWeight: 700, color: C.cyan }}>{m.pct}</span>
          </div>
        ))}
      </Card>

      {/* Swarm Capacity */}
      <Section title="Swarm Kapazität" />
      <Card>
        {[
          { name: "100K Swarm", agents: "100.000", budget: "$15", color: C.blue },
          { name: "Universal Swarm", agents: "Dynamisch", budget: "Variabel", color: C.cyan },
          { name: "500K Swarm", agents: "500.000", budget: "$75", color: C.accent },
        ].map((s, i) => (
          <div key={i} style={{
            display: "flex", justifyContent: "space-between", padding: "10px 0",
            borderBottom: i < 2 ? `1px solid ${C.border}` : "none",
          }}>
            <div>
              <div style={{ fontSize: 14, fontWeight: 600, color: s.color }}>{s.name}</div>
              <div style={{ fontSize: 11, color: C.text2 }}>{s.agents} Agents</div>
            </div>
            <div style={{ fontSize: 13, fontWeight: 700, color: C.text2 }}>{s.budget}</div>
          </div>
        ))}
      </Card>
    </div>
  );
}

// ══════════════════════════════════════════
// TASKS TAB
// ══════════════════════════════════════════
function Tasks() {
  const [tasks, setTasks] = useState({
    critical: [
      { id: 1, text: "Revenue = €0 — Produkte LIVE schalten", meta: "KRITISCH · 2–4h", done: false },
      { id: 2, text: "Redis + PostgreSQL neustarten", meta: "KRITISCH · 2 Min", done: false },
      { id: 3, text: "3 Fiverr Gigs erstellen", meta: "KRITISCH · 1h", done: false },
      { id: 4, text: "YouTube Kanal + erstes Video", meta: "WICHTIG · 2h", done: false },
      { id: 5, text: "Newsletter (Brevo) aufsetzen", meta: "WICHTIG · 1h", done: false },
    ],
    completed: [
      { text: "AI Empire App gebaut", meta: "Heute · React PWA + FastAPI" },
      { text: "Empire Control API erstellt", meta: "Heute · 15+ Endpoints" },
      { text: "Gesamtstruktur dokumentiert", meta: "Heute · 16 Seiten" },
      { text: "BMA Academy 4-Layer Architektur", meta: "Heute" },
      { text: "Kimi Bridge (Ollama + Cloud)", meta: "Heute · FastAPI Gateway" },
      { text: "Universal Swarm implementiert", meta: "Heute" },
      { text: "500K Swarm iCloud Sync", meta: "Heute" },
      { text: "Revenue Engine Launcher", meta: "Heute" },
      { text: "7-Brain System + Synapse Queue", meta: "08.02" },
      { text: "Workflow 5-Step Compound Loop", meta: "08.02" },
      { text: "X Lead Machine (4 Module)", meta: "08.02" },
      { text: "CRM System (Express + SQLite)", meta: "08.02" },
      { text: "n8n Workflows (6 Pipelines)", meta: "08.02" },
      { text: "GitHub Actions (9 Workflows)", meta: "08.02" },
      { text: "Gold Nuggets extrahiert (15+)", meta: "08.02" },
      { text: "OpenClaw Konfiguration", meta: "08.02" },
      { text: "Claude Failover System", meta: "08.02" },
      { text: "Docker Infrastruktur", meta: "08.02" },
    ],
  });

  const toggleTask = (id) => {
    setTasks(prev => ({
      ...prev,
      critical: prev.critical.map(t => t.id === id ? { ...t, done: !t.done } : t),
    }));
  };

  return (
    <div>
      <Section title="Kritische Gaps" />
      <Card>
        {tasks.critical.map((t) => (
          <div key={t.id} onClick={() => toggleTask(t.id)} style={{
            display: "flex", gap: 12, padding: "14px 0", cursor: "pointer",
            borderBottom: `1px solid ${C.border}`,
          }}>
            <div style={{
              width: 22, height: 22, borderRadius: "50%", marginTop: 2, flexShrink: 0,
              display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12,
              ...(t.done
                ? { background: C.green, color: "white" }
                : { border: `2px solid ${C.border}` }),
            }}>{t.done ? "✓" : ""}</div>
            <div>
              <div style={{ fontSize: 14, fontWeight: 600, textDecoration: t.done ? "line-through" : "none", color: t.done ? C.text2 : C.text }}>{t.text}</div>
              <div style={{ fontSize: 12, color: C.text2, marginTop: 2 }}>{t.meta}</div>
            </div>
          </div>
        ))}
      </Card>

      <Section title={`Erledigt (${tasks.completed.length})`} />
      <Card>
        {tasks.completed.map((t, i) => (
          <div key={i} style={{
            display: "flex", gap: 12, padding: "12px 0",
            borderBottom: i < tasks.completed.length - 1 ? `1px solid ${C.border}` : "none",
          }}>
            <div style={{
              width: 22, height: 22, borderRadius: "50%", marginTop: 2, flexShrink: 0,
              background: C.green, color: "white", display: "flex",
              alignItems: "center", justifyContent: "center", fontSize: 12,
            }}>✓</div>
            <div>
              <div style={{ fontSize: 14, fontWeight: 600, color: C.text2, textDecoration: "line-through" }}>{t.text}</div>
              <div style={{ fontSize: 12, color: C.text2, marginTop: 2 }}>{t.meta}</div>
            </div>
          </div>
        ))}
      </Card>
    </div>
  );
}

// ══════════════════════════════════════════
// AI CHAT TAB
// ══════════════════════════════════════════
function AiChat({ onAction }) {
  const [messages, setMessages] = useState([
    { role: "system", text: "Empire AI bereit. Frag mich was oder gib einen Befehl." },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  const send = async () => {
    if (!input.trim() || loading) return;
    const msg = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: "user", text: msg }]);
    setLoading(true);

    const result = await api("/actions", {
      method: "POST",
      body: JSON.stringify({ action: "ollama_chat", params: { prompt: msg } }),
    });

    setMessages(prev => [...prev, {
      role: "ai",
      text: result?.response || result?.error || "Ollama nicht erreichbar. Starte mit: ollama serve",
    }]);
    setLoading(false);
  };

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  return (
    <div style={{ display: "flex", flexDirection: "column", minHeight: "calc(100vh - 180px)" }}>
      <Section title="Empire AI Chat" />

      {/* Quick Commands */}
      <div style={{ display: "flex", gap: 8, overflowX: "auto", paddingBottom: 12 }}>
        {["System Status?", "Content generieren", "Was sind Gold Nuggets?", "Nächste Schritte?"].map((cmd, i) => (
          <div key={i} onClick={() => { setInput(cmd); }} style={{
            flexShrink: 0, padding: "8px 14px", borderRadius: 20,
            background: C.bg3, border: `1px solid ${C.border}`,
            fontSize: 12, cursor: "pointer", whiteSpace: "nowrap",
          }}>{cmd}</div>
        ))}
      </div>

      {/* Messages */}
      <div style={{ flex: 1 }}>
        {messages.map((m, i) => (
          <div key={i} style={{
            display: "flex", justifyContent: m.role === "user" ? "flex-end" : "flex-start",
            marginBottom: 10,
          }}>
            <div style={{
              maxWidth: "85%", padding: "12px 16px", borderRadius: 16, fontSize: 14, lineHeight: 1.5,
              ...(m.role === "user"
                ? { background: C.accent, borderBottomRightRadius: 4 }
                : m.role === "system"
                  ? { background: C.bg3, border: `1px solid ${C.border}`, color: C.text2, fontSize: 13 }
                  : { background: C.card, border: `1px solid ${C.border}`, borderBottomLeftRadius: 4 }),
            }}>{m.text}</div>
          </div>
        ))}
        {loading && (
          <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: 10 }}>
            <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 16, padding: "12px 20px", fontSize: 14, color: C.text2 }}>
              Denke nach...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={{
        display: "flex", gap: 10, padding: "12px 0",
        position: "sticky", bottom: 80, background: C.bg,
      }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && send()}
          placeholder="Frag die Empire AI..."
          style={{
            flex: 1, padding: "14px 16px", borderRadius: 14,
            background: C.card, border: `1px solid ${C.border}`,
            color: C.text, fontSize: 15, outline: "none",
          }}
        />
        <div onClick={send} style={{
          width: 48, height: 48, borderRadius: 14, background: C.accent,
          display: "flex", alignItems: "center", justifyContent: "center",
          cursor: "pointer", fontSize: 20, flexShrink: 0,
        }}>↑</div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════
// REVENUE TAB
// ══════════════════════════════════════════
function Revenue({ revenue }) {
  const channels = [
    { name: "Gumroad", products: "AI Prompt Vault, OpenClaw Guide, Docker, BMA+AI", price: "€27–149", target: "€5K–10K", status: "setup", icon: "🛒" },
    { name: "Fiverr / Upwork", products: "AI Automation, SEO Posts, BMA Docs", price: "€30–1.000", target: "€3K–8K", status: "offline", icon: "💼" },
    { name: "Consulting", products: "BMA+AI Integration, AI Stack, Docker", price: "€1K–5K", target: "€5K–15K", status: "ready", icon: "🤝" },
    { name: "X / Twitter", products: "Lead-Gen → Pipeline → DM-Sequenzen", price: "5 Posts/Tag", target: "+500 Follower", status: "active", icon: "𝕏" },
    { name: "OpenClaw Skills", products: "BMA Expert, SEO Engine, Docker Pack", price: "$20–100", target: "Marketplace", status: "setup", icon: "🧩" },
    { name: "YouTube", products: "AI-Tutorials, BMA-Content, BTS", price: "AdSense", target: "3 Videos", status: "offline", icon: "▶️" },
  ];

  const weeks = [
    { week: "W1", focus: "Revenue-Aktivierung", detail: "3 Gumroad + 3 Fiverr + X-Posts", target: "€500–1K", active: true },
    { week: "W2", focus: "Scaling", detail: "YouTube + Newsletter + Skills", target: "€1.5K–3K" },
    { week: "W3", focus: "Automation", detail: "Cron-Jobs + A/B + Voll-Auto", target: "€3K–5K" },
    { week: "W4", focus: "Scale", detail: "Paid Ads + Affiliates + Community", target: "€5K–10K" },
  ];

  return (
    <div>
      <Section title="Revenue Kanäle" />
      {channels.map((ch, i) => (
        <Card key={i}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontSize: 22 }}>{ch.icon}</span>
              <span style={{ fontSize: 16, fontWeight: 700 }}>{ch.name}</span>
            </div>
            <Badge status={ch.status} />
          </div>
          <div style={{ fontSize: 13, color: C.text2, marginBottom: 8 }}>{ch.products}</div>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12 }}>
            <span style={{ color: C.text2 }}>{ch.price}</span>
            <span style={{ color: C.green, fontWeight: 700 }}>Ziel: {ch.target}</span>
          </div>
        </Card>
      ))}

      <Section title="30-Tage Execution" />
      <Card>
        {weeks.map((w, i) => (
          <div key={i} style={{
            display: "flex", gap: 12, padding: "14px 0",
            borderBottom: i < 3 ? `1px solid ${C.border}` : "none",
          }}>
            <div style={{
              width: 32, height: 32, borderRadius: "50%", flexShrink: 0,
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 11, fontWeight: 700,
              ...(w.active
                ? { border: `2px solid ${C.cyan}`, background: "rgba(0,210,255,.1)", color: C.cyan }
                : { border: `2px solid ${C.border}`, color: C.text2 }),
            }}>{w.week}</div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 14, fontWeight: 600 }}>{w.focus}</div>
              <div style={{ fontSize: 12, color: C.text2, marginTop: 2 }}>{w.detail}</div>
            </div>
            <div style={{ fontSize: 13, fontWeight: 700, color: C.green, alignSelf: "center" }}>{w.target}</div>
          </div>
        ))}
      </Card>

      {/* Monthly Target */}
      <div style={{
        background: "rgba(245,166,35,.08)", border: `2px solid ${C.gold}`,
        borderRadius: 16, padding: 20, textAlign: "center", marginTop: 8,
      }}>
        <div style={{ fontSize: 13, color: C.text2 }}>GESAMTZIEL MONAT 1</div>
        <div style={{ fontSize: 36, fontWeight: 900, color: C.accent, margin: "8px 0" }}>€10.000 – €19.000</div>
        <div style={{ fontSize: 12, color: C.gold }}>6 Kanäle × Automatisierung × 24/7</div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════
// MAIN APP
// ══════════════════════════════════════════
export default function App() {
  const [tab, setTab] = useState("dashboard");
  const [health, setHealth] = useState(null);
  const [revenue, setRevenue] = useState(null);
  const [brains, setBrains] = useState([]);
  const [toast, setToast] = useState({ message: "", visible: false });
  const [time, setTime] = useState(new Date());

  const showToast = (msg) => {
    setToast({ message: msg, visible: true });
    setTimeout(() => setToast(prev => ({ ...prev, visible: false })), 2500);
  };

  const handleAction = async (action) => {
    const labels = {
      generate_content: "Content wird generiert...",
      health_check: "Health Check läuft...",
      git_push: "Git Push gestartet...",
      start_redis: "Redis wird gestartet...",
      start_postgresql: "PostgreSQL wird gestartet...",
      create_issue: "Issue wird erstellt...",
      swarm_start: "Swarm wird initialisiert...",
      revenue_report: "Revenue Report...",
    };
    showToast(labels[action] || "Aktion gestartet...");

    const result = await api("/actions", {
      method: "POST",
      body: JSON.stringify({ action, params: {} }),
    });

    if (result?.status === "success" || result?.content) {
      showToast("Erledigt ✓");
    }
  };

  // Load data
  useEffect(() => {
    api("/health").then(d => d && setHealth(d));
    api("/revenue").then(d => d && setRevenue(d));
    api("/brains").then(d => d?.brains && setBrains(d.brains));

    const interval = setInterval(() => {
      api("/health").then(d => d && setHealth(d));
      setTime(new Date());
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const tabs = [
    { id: "dashboard", icon: "🏠", label: "Home" },
    { id: "systems", icon: "⚙️", label: "Systems" },
    { id: "tasks", icon: "✅", label: "Tasks" },
    { id: "chat", icon: "🤖", label: "AI Chat" },
    { id: "revenue", icon: "💰", label: "Revenue" },
  ];

  return (
    <div style={{
      fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif",
      background: C.bg, color: C.text, minHeight: "100vh",
      maxWidth: 480, margin: "0 auto",
    }}>
      <Toast message={toast.message} visible={toast.visible} />

      {/* Top Bar */}
      <div style={{
        position: "sticky", top: 0, zIndex: 100, padding: "14px 20px",
        background: "rgba(10,10,26,.95)", backdropFilter: "blur(20px)",
        display: "flex", justifyContent: "space-between", alignItems: "center",
      }}>
        <h1 style={{ fontSize: 22, fontWeight: 800, margin: 0 }}>
          <span style={{ color: C.accent }}>AI</span> EMPIRE
        </h1>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 11, color: C.text2 }}>
            {time.getHours().toString().padStart(2, "0")}:{time.getMinutes().toString().padStart(2, "0")}
          </span>
          <div style={{
            width: 10, height: 10, borderRadius: "50%", background: C.green,
            boxShadow: `0 0 8px ${C.green}`,
          }} />
        </div>
      </div>

      {/* Content */}
      <div style={{ padding: "0 16px 100px" }}>
        {tab === "dashboard" && <Dashboard health={health} onAction={handleAction} revenue={revenue} />}
        {tab === "systems" && <Systems health={health} brains={brains} />}
        {tab === "tasks" && <Tasks />}
        {tab === "chat" && <AiChat onAction={handleAction} />}
        {tab === "revenue" && <Revenue revenue={revenue} />}
      </div>

      {/* Bottom Nav */}
      <div style={{
        position: "fixed", bottom: 0, left: 0, right: 0, zIndex: 100,
        background: "rgba(10,10,26,.95)", backdropFilter: "blur(20px)",
        borderTop: `1px solid ${C.border}`, padding: "8px 0 24px",
        display: "flex", justifyContent: "space-around", maxWidth: 480, margin: "0 auto",
      }}>
        {tabs.map(t => (
          <div key={t.id} onClick={() => setTab(t.id)} style={{
            display: "flex", flexDirection: "column", alignItems: "center", gap: 2,
            color: tab === t.id ? C.accent : C.text2, cursor: "pointer",
            padding: "4px 12px", transition: "color .15s",
          }}>
            <span style={{ fontSize: 22 }}>{t.icon}</span>
            <span style={{ fontSize: 10, fontWeight: 600 }}>{t.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
