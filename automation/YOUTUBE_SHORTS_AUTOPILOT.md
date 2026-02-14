# YouTube Shorts Autopilot

## Goal
Build a low-cost, self-improving Shorts machine that runs with local models first and upgrades decisions from feedback.

## Core path
1. Trend scan (`trends.json`)
2. Draft generation (`drafts.json`)
3. Gemini video render (`video_renders.json` + `videos/*.mp4`)
4. Publish queue (`publish_queue.csv`)
5. Performance snapshot (`metrics.json`)
6. Adaptation plan (`feedback_plan.md`)

## Commands
```bash
# Single run (dry run, no API spend)
python3 -m automation run --workflow youtube_shorts

# Single run with local model execution
python3 -m automation run --workflow youtube_shorts --execute

# 10h autopilot (every 30 min)
automation/scripts/run_youtube_autopilot.sh 10 30

# 10h autopilot with local model execution
EXECUTE_MODE=1 automation/scripts/run_youtube_autopilot.sh 10 30
```

## Required env
- `YOUTUBE_API_KEY` (optional but needed for real trend and stats pull)
- `YOUTUBE_CHANNEL_ID` (optional but needed for own-channel feedback loop)
- `OLLAMA_API_KEY` (for local OpenAI-compatible endpoint, typically `local`)
- `GEMINI_API_KEY` (needed to produce real MP4 videos via Veo)

## Outputs
- `content_factory/deliverables/youtube_shorts/latest.json`
- `content_factory/deliverables/youtube_shorts/<run_id>/trends.json`
- `content_factory/deliverables/youtube_shorts/<run_id>/drafts.json`
- `content_factory/deliverables/youtube_shorts/<run_id>/video_renders.json`
- `content_factory/deliverables/youtube_shorts/<run_id>/videos/*.mp4`
- `content_factory/deliverables/youtube_shorts/<run_id>/publish_queue.csv`
- `content_factory/deliverables/youtube_shorts/<run_id>/metrics.json`
- `content_factory/deliverables/youtube_shorts/<run_id>/feedback_plan.md`

## Safety constraints
- Banned-term filter for hate/racism topics.
- No direct copying of source videos; only structural adaptation.

## Optimization logic
- If avg views/hour is below target -> stronger hooks + shorter scripts + new angles.
- If like rate is low -> improve emotional framing in first 5 seconds.
- If comment rate is low -> CTA changed to explicit binary or one-word prompts.

## Practical note
`publish_queue.csv` now includes `video_file`, `video_status`, `video_operation`, `video_error`.
Use this directly for YouTube Studio QA and/or automated publish steps via API.
