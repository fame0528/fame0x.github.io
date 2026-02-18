# Architecture — Income Bot

High-level design and component interactions.

---

## System Overview

Income Bot is an automated content generation and publishing pipeline that produces SEO-optimized affiliate articles for a micro-niche and publishes them to a GitHub Pages site without human intervention.

```
┌─────────────────────────────────────────────────────────────┐
│                         Scheduler                           │
│                    (run.py / GitHub Actions)               │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Job Queue (SQLite)                        │
│          Persists jobs across crashes/restarts             │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                Keyword Researcher                          │
│  1. Query DB for pending keywords                          │
│  2. Mark as assigned                                       │
│  3. Return keyword(s)                                      │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                 Product Fetcher (Cached)                   │
│  1. Look up products for keyword (cache TTL 24h)          │
│  2. If miss, generate mock/product data                   │
│  3. Store in cache                                         │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                Content Generator (Gemini)                  │
│  - Retry with exponential backoff                          │
│  - Circuit breaker opens after 5 failures                  │
│  - Produces E-E-A-T compliant article                      │
│  - Returns Markdown with placeholders                      │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Parallel Image Fetcher                    │
│  - Thread pool (max 2 workers)                             │
│  - Fetch images from pollinations.ai or other free APIs    │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│               Post-Processing & Validation                 │
│  - Replace image placeholders                              │
│  - Replace affiliate link placeholders                     │
│  - Validate length, link presence, no broken formatting   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Publisher (Git)                          │
│  - Write to _posts/{category}/{slug}.md                    │
│  - Git add, commit, push                                   │
│  - Record commit SHA to database                           │
│  - On failure, log error and mark job failed               │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Metrics & Logging                         │
│  - Increment daily counters                               │
│  - Write JSON log entry                                   │
│  - Send Discord alert on failure/critical                 │
│  - Update health_status.json                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow

1. **Input:** Seed keywords from `config.yaml` (e.g., "hip_supplements_for_german_shepherds")
2. **Processing:** Each keyword becomes one article. The system processes keywords serially (one at a time) but parallelizes I/O operations (image fetching).
3. **Output:** Markdown file committed to GitHub repository; GitHub Actions builds static site; public URL contains affiliate links.

---

## State Persistence

All state is stored in SQLite (`data/income_bot.db`) with the following tables:

| Table | Purpose |
|-------|---------|
| `keywords` | List of keywords to process, with status (pending/assigned/completed/failed) |
| `articles` | Records of published articles linked to keywords |
| `publish_log` | Every publish attempt (success/failure) with commit SHA and URL |
| `metrics` | Daily aggregates (articles, api_calls, tokens, errors, earnings) |
| `audit_log` | Immutable log of all system actions for debugging |
| `job_queue` | Persistent job queue for resilient processing |

This enables:
- Crash recovery: if bot dies mid-run, restart picks up next keyword
- Audit trail: can trace any article's history
- Metrics: track production velocity and error rates

---

## Resilience Mechanisms

### Retry with Exponential Backoff
- Applied to Gemini API calls (max 3 attempts)
- Base delay 2s, factor 2, jitter ±20%

### Circuit Breaker (Gemini)
- Failure threshold: 5 errors within short window
- Opens circuit for 2 minutes (fail fast, no calls)
- Half-open test on recovery

### Job Queue
- Each article generation is a job in `job_queue`
- On startup, stale `in_progress` jobs older than 30 minutes are reset to `pending`
- Allows safe restart after crash

### Caching
- Product data cached for 24 hours (same keyword won't refetch)
- Reduces API calls and speeds up processing

---

## Security Model

- **Config file** intended to be chmod 600 (owner read/write only)
- **All secrets** passed via environment variables or encrypted config (optional)
- **No hardcoded credentials** in code
- **Log redaction** prevents accidental exposure in logs
- **SQLite DB** stored in `data/` with same permissions as config
- **GitHub Actions** uses repository secrets for `GEMINI_API_KEY`

**Threat model:** We assume the bot runs on Spencer's machine (trusted) and the main risk is credential leakage via logs or accidental commit. Mitigations above reduce that risk.

---

## Monitoring & Alerting

### Health Check (`run.py --health` or `health_check.py`)
- Checks: recent article published, affiliate links present, git activity
- Writes `health_status.json`

### Dashboard (`health_dashboard.html`)
- Static HTML page (can be hosted on same GitHub Pages)
- Fetches `health_status.json` and displays metrics
- Auto-refresh every 30s

### Alerts
- Discord webhook on ERROR/CRITICAL log events
- Can configure email via GitHub Actions failure notifications (built-in)

---

## Configuration

`config.yaml`:

```yaml
gemini_api_key: "AIza..."    # or use env var GEMINI_API_KEY
repo_path: "C:/path/to/live_site"
niche:
  name: "Specialty Dog Supplements"
  seed_keywords:
    - "hip_supplements_for_german_shepherds"
    - "anxiety_relief_for_rescue_dogs"
amazon_tracking_id: "yourtag-20"
discord_webhook_url: "https://discord.com/api/webhooks/..."
obsidian_vault_path: "C:/Users/spenc/Documents/Obsidian/Vaults/Atlas"
```

---

## Extension Points

### Adding New Niche
1. Change `niche.name` and `niche.seed_keywords`
2. Adjust `ContentGenerator` prompt for new domain (different tone, product types)
3. Update `category` in `publisher.py` call

### Adding Affiliate Networks
1. Modify `ProductFetcher.fetch_products` to use new API (e.g., ShareASale API)
2. Add tracking ID field to config
3. Update placeholder replacement in `scheduler.py` for new link format

### Adding Backup AI Model
1. Add `gemini_backup_api_key` to config
2. In `ContentGenerator.generate_article`, catch specific exception and switch client to backup key

---

## Performance Characteristics

- **Throughput:** 1 article per run (~5-10 minutes including API latency)
- **Concurrency:** Parallel image fetching (2 threads) reduces total time by ~30%
- **Token usage:** ~2000 tokens/article at ~2000 chars/token → 4M chars per article
- **Cost:** $0 (free tier)
- **Storage:** SQLite DB grows ~1KB per article

---

## Limitations

- **Single article per run** — to stay within free tier quotas
- **Mock product data** — would need real Amazon PA-API integration for production
- **No backlink building** — assumes SEO will eventually bring traffic; may need manual promotion
- **No earnings tracking** — affiliate dashboards are external; could integrate via APIs later

---

**Next:** See DEPLOYMENT.md for activation instructions. 🗺️