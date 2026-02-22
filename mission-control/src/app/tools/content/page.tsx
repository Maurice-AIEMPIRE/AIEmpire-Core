"use client";

export default function ContentTool() {
  const cronSchedule = [
    { time: "07:00, 13:00, 20:00", job: "Reverse Prompt", desc: "Agent suggests highest-impact next task" },
    { time: "07:30", job: "System Health", desc: "Check all systems, find optimization opportunities" },
    { time: "08:00", job: "Trend Scan", desc: "TikTok/YouTube/X trends, hooks, product angles" },
    { time: "09:00", job: "Short-Form Scripts", desc: "3 video scripts + 5 tweet drafts" },
    { time: "10:00", job: "Offer Packaging", desc: "CTAs, headlines, value bullets" },
    { time: "12:00", job: "Content Calendar", desc: "3 posting slots with topics and CTAs" },
    { time: "14:00", job: "YouTube Outline", desc: "6-10 min video outline with beats" },
    { time: "17:00", job: "Engagement Playbook", desc: "Reply templates, community prompts" },
    { time: "19:00", job: "KPI Snapshot", desc: "Daily metrics, targets, optimization plan" },
    { time: "Mon 11:00", job: "Weekly Revenue Review", desc: "Pipeline status, blockers, top 5 actions" },
    { time: "Mon 15:00", job: "Batch Production Plan", desc: "10 short-form + 3 long-form ideas" },
  ];

  return (
    <div>
      <h1 style={{ fontSize: "28px", marginBottom: "8px" }}>Content Pipeline</h1>
      <p style={{ color: "#888", marginBottom: "24px" }}>
        Automated content generation schedule — {cronSchedule.length} cron jobs
      </p>

      <div
        style={{
          backgroundColor: "#161616",
          border: "1px solid #2a2a2a",
          borderRadius: "12px",
          padding: "20px",
          marginBottom: "16px",
        }}
      >
        <h2 style={{ fontSize: "16px", color: "#7dd3fc", marginTop: 0 }}>
          Daily Schedule
        </h2>
        {cronSchedule.map((job) => (
          <div
            key={job.job}
            style={{
              display: "grid",
              gridTemplateColumns: "140px 200px 1fr",
              padding: "10px 0",
              borderBottom: "1px solid #222",
              fontSize: "14px",
            }}
          >
            <span style={{ color: "#4ade80", fontFamily: "monospace" }}>
              {job.time}
            </span>
            <span style={{ fontWeight: 600 }}>{job.job}</span>
            <span style={{ color: "#888" }}>{job.desc}</span>
          </div>
        ))}
      </div>

      <div
        style={{
          backgroundColor: "#161616",
          border: "1px solid #2a2a2a",
          borderRadius: "12px",
          padding: "20px",
        }}
      >
        <h2 style={{ fontSize: "16px", color: "#f87171", marginTop: 0 }}>
          X/Twitter Safety (Tip #10)
        </h2>
        <p style={{ color: "#888", fontSize: "14px" }}>
          All content is DRAFTED only. No direct API posting to X/Twitter.
          X is cracking down on bots and API usage. Posts should be manually
          reviewed and published by Maurice to avoid account penalties.
        </p>
        <div
          style={{
            backgroundColor: "#1a1a2e",
            padding: "12px",
            borderRadius: "8px",
            fontSize: "14px",
            color: "#fbbf24",
            marginTop: "12px",
          }}
        >
          Workflow: Cron generates drafts → Review in Mission Control → Manual post
        </div>
      </div>
    </div>
  );
}
