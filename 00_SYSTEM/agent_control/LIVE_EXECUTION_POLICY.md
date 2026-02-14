# Live Execution Policy (Global)

This repository runs in **live mode**. All agents must follow these rules:

1. No simulation placeholders for operational runs.
2. Use `EXECUTE_MODE=1` for production/autopilot loops.
3. Prefer local-first routing (Ollama) for cost control, but keep real execution.
4. Auto-publish is enabled with controlled limits and kill-switches.
5. Report real cashflow from Stripe separately from projections.

Operational note:
- Revenue projections (`money_model.json`) are forecasts.
- Real revenue source of truth is Stripe sync output:
  `content_factory/deliverables/revenue/stripe/latest.json`.
