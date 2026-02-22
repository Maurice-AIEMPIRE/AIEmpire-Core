"use client";

export default function SystemsTool() {
  const systems = [
    { name: "Antigravity", modules: 26, status: "PRODUCTION", files: "268KB" },
    { name: "Workflow System", modules: 3, status: "PRODUCTION", files: "72KB" },
    { name: "Empire Engine", modules: 1, status: "PRODUCTION", files: "12KB" },
    { name: "Kimi Swarm", modules: 2, status: "READY", files: "45KB" },
    { name: "X Lead Machine", modules: 2, status: "DRAFT ONLY", files: "24KB" },
    { name: "Atomic Reactor", modules: 2, status: "PRODUCTION", files: "10KB" },
    { name: "CRM", modules: 1, status: "PRODUCTION", files: "32KB" },
    { name: "Brain System", modules: 7, status: "PRODUCTION", files: "20KB" },
    { name: "Gemini Mirror", modules: 2, status: "PRODUCTION", files: "114KB" },
    { name: "BMA Academy", modules: 9, status: "PRODUCT READY", files: "25KB" },
    { name: "OpenClaw Config", modules: 3, status: "PRODUCTION", files: "15KB" },
    { name: "Gold Nuggets", modules: 15, status: "COMPLETE", files: "125KB" },
    { name: "Auto-Repair", modules: 1, status: "PRODUCTION", files: "16KB" },
    { name: "Mission Control", modules: 4, status: "NEW", files: "~10KB" },
  ];

  const statusColor = (s: string) => {
    if (s === "PRODUCTION") return "#4ade80";
    if (s === "READY" || s === "PRODUCT READY" || s === "COMPLETE") return "#fbbf24";
    if (s === "DRAFT ONLY") return "#f87171";
    return "#7dd3fc";
  };

  return (
    <div>
      <h1 style={{ fontSize: "28px", marginBottom: "8px" }}>System Inventory</h1>
      <p style={{ color: "#888", marginBottom: "24px" }}>
        {systems.length} systems — {systems.filter((s) => s.status === "PRODUCTION").length} in production
      </p>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
          gap: "12px",
        }}
      >
        {systems.map((sys) => (
          <div
            key={sys.name}
            style={{
              backgroundColor: "#161616",
              border: "1px solid #2a2a2a",
              borderRadius: "12px",
              padding: "16px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ fontWeight: 600 }}>{sys.name}</span>
              <span style={{ color: statusColor(sys.status), fontSize: "12px" }}>
                {sys.status}
              </span>
            </div>
            <div style={{ color: "#888", fontSize: "13px", marginTop: "8px" }}>
              {sys.modules} module{sys.modules > 1 ? "s" : ""} • {sys.files}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
