# TikTok Setup Runbook

This runbook covers the manual account/app setup and the local CLI flow in this repo.

Quick live start:

```bash
automation/scripts/run_tiktok_live.sh
```

## 1) Create TikTok Developer Setup

1. Create or log in to a TikTok account.
2. Open the TikTok Developer portal: `https://developers.tiktok.com/`.
3. Create an app and copy:
- `Client Key`
- `Client Secret`
4. Configure OAuth redirect URI in the app settings.
5. Add required scopes for your use case:
- `user.info.basic`
- `video.list`
- `video.upload`
- `video.publish`

Notes:
- Redirect URI must match exactly between app settings and CLI command.
- If you use `PULL_FROM_URL`, the source URL must be publicly reachable.

## 2) Configure Local Environment

Copy values into your shell (or your secure env file):

```bash
export TIKTOK_CLIENT_KEY="..."
export TIKTOK_CLIENT_SECRET="..."
export TIKTOK_REDIRECT_URI="https://your-app.example/callback"
export TIKTOK_SCOPES="user.info.basic,video.list,video.upload,video.publish"
```

## 3) OAuth (Authorization Code + PKCE)

Generate PKCE pair:

```bash
python3 -m automation.tiktok pkce
```

Set the values:

```bash
export TIKTOK_CODE_CHALLENGE="<code_challenge_from_pkce>"
export TIKTOK_CODE_VERIFIER="<code_verifier_from_pkce>"
```

Generate login URL:

```bash
python3 -m automation.tiktok auth-url
```

After consent, copy `code` from your callback URL and exchange it:

```bash
python3 -m automation.tiktok exchange-code --code "<AUTH_CODE>"
```

Save:
- `access_token` -> `TIKTOK_ACCESS_TOKEN`
- `refresh_token` -> `TIKTOK_REFRESH_TOKEN`

## 4) Verify Account Access

```bash
export TIKTOK_ACCESS_TOKEN="..."
python3 -m automation.tiktok user-info
python3 -m automation.tiktok creator-info
python3 -m automation.tiktok video-list --max-count 10
```

## 5) Upload and Publish

### Option A: Inbox Upload (Creator finishes in TikTok app)

```bash
python3 -m automation.tiktok inbox-init-file --file ./video.mp4 --upload
```

### Option B: Direct Post API

```bash
python3 -m automation.tiktok direct-init-file --file ./video.mp4 --title "My post title" --upload
```

Get `publish_id` from response and poll status:

```bash
python3 -m automation.tiktok post-status --publish-id "<PUBLISH_ID>"
```

### Option C: Pull From URL

```bash
python3 -m automation.tiktok direct-init-url --title "My post title" --video-url "https://example.com/video.mp4"
```

## 6) Token Maintenance

Refresh token:

```bash
python3 -m automation.tiktok refresh-token
```

Revoke token:

```bash
python3 -m automation.tiktok revoke-token --token "<TOKEN_TO_REVOKE>"
```

## 7) Troubleshooting

1. `redirect_uri mismatch`:
- Ensure app settings redirect URI exactly matches `TIKTOK_REDIRECT_URI`.
2. Scope errors:
- Confirm all scopes are enabled in app settings and in `TIKTOK_SCOPES`.
3. Upload errors:
- Use MP4 and ensure chunk rules:
- single-chunk <= 64 MB
- multi-chunk chunks should be >= 5 MB
4. Posting capability restrictions:
- Ensure app/product approvals in TikTok Developer portal are complete.
