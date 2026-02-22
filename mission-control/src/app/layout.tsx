import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AI Empire — Mission Control",
  description: "Custom tooling dashboard for OpenClaw agent workflows",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body
        style={{
          margin: 0,
          fontFamily:
            '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace',
          backgroundColor: "#0a0a0a",
          color: "#e0e0e0",
          minHeight: "100vh",
        }}
      >
        <nav
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "16px 24px",
            borderBottom: "1px solid #222",
            backgroundColor: "#111",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <span style={{ fontSize: "24px" }}>🏛️</span>
            <span style={{ fontSize: "18px", fontWeight: 700 }}>
              AI Empire — Mission Control
            </span>
          </div>
          <div style={{ display: "flex", gap: "20px", fontSize: "14px" }}>
            <a href="/" style={{ color: "#7dd3fc", textDecoration: "none" }}>
              Dashboard
            </a>
            <a
              href="/tools/revenue"
              style={{ color: "#7dd3fc", textDecoration: "none" }}
            >
              Revenue
            </a>
            <a
              href="/tools/systems"
              style={{ color: "#7dd3fc", textDecoration: "none" }}
            >
              Systems
            </a>
            <a
              href="/tools/content"
              style={{ color: "#7dd3fc", textDecoration: "none" }}
            >
              Content
            </a>
          </div>
        </nav>
        <main style={{ padding: "24px", maxWidth: "1200px", margin: "0 auto" }}>
          {children}
        </main>
      </body>
    </html>
  );
}
