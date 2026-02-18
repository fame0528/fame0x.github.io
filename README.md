# Income Bot - Zero-Cost Automated Affiliate Content

**Status:** Production-Ready, Infrastructure-Hardened  
**License:** For Spencer's Empire Building Mission

This is the implementation of the AI-Powered Niche Affiliate Content Automation system, now enhanced with resilience, monitoring, testing, and security layers.

## Quick Start

1. **Clone your GitHub Pages repository** to `live_site` folder (see DEPLOYMENT.md)
2. **Copy** `config.yaml.example` → `config.yaml` and fill in your API keys and paths
3. **Install dependencies:** `pip install -r requirements.txt`
4. **Initialize database:** `python run.py --setup`
5. **Test run:** `python run.py --once`
6. **Check health:** `python run.py --health`
7. **Configure GitHub Actions** (add `GEMINI_API_KEY` secret) for daily automation
8. **Apply to affiliate programs** (Amazon Associates, etc.) and add tracking IDs

See `EMPIRE-READY-STRATEGY.md` (workspace root) for full strategic context, or `DEPLOYMENT.md` in this folder for step-by-step activation.

## CLI Reference

```powershell
python run.py --once      # Generate & publish one article (default)
python run.py --setup     # Initialize database and seed keywords
python run.py --health    # Run health checks
python run.py --test      # Run integration test suite
```

## Directory Structure

```
income_bot/
├── src/                    # Core modules
│   ├── database.py       # SQLite state management
│   ├── logger.py         # Structured JSON logging + Discord alerts
│   ├── metrics.py        # Metrics collection
│   ├── retry_handler.py  # Exponential backoff retry
│   ├── circuit_breaker.py  # API failure circuit breaker
│   ├── job_queue.py      # Persistent job queue
│   ├── cache.py          # TTL caching layer
│   ├── parallel.py       # Parallel I/O helper
│   ├── security.py       # Config encryption/redaction
│   ├── keyword_researcher.py
│   ├── product_fetcher.py
│   ├── content_generator.py
│   ├── image_fetcher.py
│   └── publisher.py
├── tests/                 # Test suite (pytest)
├── .github/workflows/    # GitHub Actions (daily.yml)
├── health_dashboard.html # Self-contained monitoring dashboard
├── ARCHITECTURE.md       # System design and data flow
├── TROUBLESHOOTING.md    # Decision tree for issues
├── RUNBOOKS.md           # Incident response procedures
├── DEPLOYMENT.md         # Step-by-step activation guide
├── CHANGELOG.md          # Version history
├── config.yaml           # YOUR configuration (create from example)
├── config.yaml.example   # Template
├── requirements.txt      # Python dependencies
├── run.py                # Main CLI entry point
├── scheduler.py          # Legacy (use run.py)
├── health_check.py       # Health check module
├── install.ps1           # Windows installer for Task Scheduler
├── rollback.ps1          # Emergency rollback script
├── reports/              # Daily reports (auto-generated)
└── logs/                 # JSON log files (auto-generated)

```

## Key Features

- **Resilient:** Retry logic, circuit breaker, crash recovery via job queue
- **Observable:** Structured JSON logs, daily metrics, Discord alerts, HTML dashboard
- **Tested:** Unit tests + integration test suite, pre-publish validation
- **Secure:** No hardcoded secrets, config encryption optional, log redaction
- **Hands-Off:** After setup, runs autonomously via GitHub Actions

## Monitoring

- **Health status:** `health_status.json` (updated after each run)
- **Dashboard:** Copy `health_dashboard.html` to your live site for real-time view
- **Logs:** `logs/YYYY-MM-DD.jsonl` — one JSON entry per line
- **Daily reports:** `reports/YYYY-MM-DD.md`

## Support

- First, consult `TROUBLESHOOTING.md` (decision tree)
- Then check `RUNBOOKS.md` for incident procedures
- Review `ARCHITECTURE.md` for system understanding
- Archive full documentation in Obsidian: `Resources/IncomeBot/`

---

**Ready to build your empire?** Start with `DEPLOYMENT.md`. 🗺️