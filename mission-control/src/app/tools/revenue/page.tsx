"use client";

export default function RevenueTool() {
  const channels = [
    {
      name: "Gumroad Digital Products",
      products: ["BMA Checklisten (27-49 EUR)", "AI Agent Kit (99 EUR)", "Empire Blueprint (149 EUR)"],
      status: "Product Ready",
      nextAction: "Launch first product, set up Gumroad storefront",
    },
    {
      name: "Fiverr/Upwork AI Services",
      products: ["AI Agent Setup (50-500 EUR)", "BMA + AI Consulting (500-5000 EUR)"],
      status: "Profile Ready",
      nextAction: "Create 3 gig listings, set competitive pricing",
    },
    {
      name: "BMA + AI Consulting",
      products: ["DIN 14675 AI Audit (2000 EUR)", "Full BMA Digital Twin (5000-10000 EUR)"],
      status: "Unique Niche",
      nextAction: "Create landing page, reach out to 10 BMA companies",
    },
    {
      name: "Agent Builders Club",
      products: ["Monthly Membership (29 EUR/mo)"],
      status: "Concept",
      nextAction: "Set up Discord server, create first 3 tutorials",
    },
  ];

  return (
    <div>
      <h1 style={{ fontSize: "28px", marginBottom: "8px" }}>Revenue Pipeline Tool</h1>
      <p style={{ color: "#888", marginBottom: "24px" }}>
        Track and activate all revenue channels
      </p>

      {channels.map((ch) => (
        <div
          key={ch.name}
          style={{
            backgroundColor: "#161616",
            border: "1px solid #2a2a2a",
            borderRadius: "12px",
            padding: "20px",
            marginBottom: "16px",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h2 style={{ fontSize: "18px", margin: 0 }}>{ch.name}</h2>
            <span
              style={{
                backgroundColor: "#1e3a5f",
                color: "#7dd3fc",
                padding: "4px 12px",
                borderRadius: "20px",
                fontSize: "12px",
              }}
            >
              {ch.status}
            </span>
          </div>
          <div style={{ margin: "12px 0" }}>
            {ch.products.map((p) => (
              <div key={p} style={{ color: "#aaa", padding: "4px 0", fontSize: "14px" }}>
                • {p}
              </div>
            ))}
          </div>
          <div
            style={{
              backgroundColor: "#1a1a2e",
              padding: "12px",
              borderRadius: "8px",
              fontSize: "14px",
              color: "#fbbf24",
            }}
          >
            Next Action: {ch.nextAction}
          </div>
        </div>
      ))}
    </div>
  );
}
