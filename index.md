# Income Bot — Documentation Index

Welcome to the Income Bot project documentation. This is your starting point for building a zero-cost automated affiliate income stream.

---

## Quick Navigation

| If you want to... | Read this first |
|-------------------|----------------|
| **Understand the overall strategy** | `EMPIRE-READY-STRATEGY.md` (workspace root) |
| **Deploy and activate** | `DEPLOYMENT.md` |
| **Troubleshoot an issue** | `TROUBLESHOOTING.md` (decision tree) |
| **Respond to an incident** | `RUNBOOKS.md` (step-by-step procedures) |
| **Understand how it works** | `ARCHITECTURE.md` (system design) |
| **See what changed recently** | `CHANGELOG.md` |
| **Quick reference** | `README.md` |

---

## Core Documents

### 1. EMPIRE-READY-STRATEGY.md *(Workspace Root)*
The master strategy document produced by the Olympus Swarm. Contains:
- Selected opportunity (AI-Powered Niche Affiliate Content)
- Full 10-phase agent outputs (research, docs, builder, security, etc.)
- Complete source code listing
- Implementation checklist

👉 **Start here if you're new to the project.**

### 2. DEPLOYMENT.md *(This Folder)*
Step-by-step activation guide for Spencer.
- Create GitHub Pages repo
- Get Gemini API key
- Configure `config.yaml`
- Test locally
- Enable GitHub Actions
- Apply to affiliate programs
- Expected revenue timeline

**Follow this after reading the strategy.**

### 3. ARCHITECTURE.md
Technical deep-dive into the system:
- Component diagram
- Data flow
- State persistence (SQLite)
- Resilience mechanisms (retry, circuit breaker, job queue)
- Performance characteristics
- Security model

**Read this if you want to understand how it works under the hood.**

### 4. TROUBLESHOOTING.md
Decision tree for common problems:
- Bot stopped publishing?
- GitHub Actions failing?
- Articles not appearing?
- Low quality content?
- Quota exceeded?
- Affiliate links not working?

**Consult this when something goes wrong.**

### 5. RUNBOOKS.md
Incident response playbooks:
- Bot stopped
- Quota exceeded
- Workflow failing
- Site not updating
- Low quality articles
- Rollback procedure
- Routine maintenance schedule

**Use during an active incident.**

### 6. CHANGELOG.md
Version history and what changed in each release.

---

## Reference Files

- `README.md` — Quick overview and CLI reference
- `config.yaml.example` — Configuration template (copy to `config.yaml`)
- `health_dashboard.html` — Self-contained monitoring dashboard (copy to live site)
- `INFRASTRUCTURE-REFINEMENT.md` *(workspace root)* — Sprint plan and completion report

---

## Code Structure

```
income_bot/
├── src/                    # Modules
│   ├── database.py        # SQLite state
│   ├── logger.py          # JSON + Discord
│   ├── metrics.py         # KPI tracking
│   ├── retry_handler.py   # Retry logic
│   ├── circuit_breaker.py # API protection
│   ├── job_queue.py       # Persistent queue
│   ├── cache.py           # TTL cache
│   ├── parallel.py        # Thread pool
│   ├── security.py        # Config security
│   ├── keyword_researcher.py
│   ├── product_fetcher.py
│   ├── content_generator.py
│   ├── image_fetcher.py
│   └── publisher.py
├── tests/                 # Test suite
├── logs/                  # JSON log files (auto)
├── reports/               # Daily reports (auto)
├── data/                  # SQLite DB (auto)
├── run.py                 # Main CLI entry
├── scheduler.py           # Legacy
├── health_check.py        # Health module
├── install.ps1            # Windows installer
├── rollback.ps1           # Emergency rollback
└── .github/workflows/     # GitHub Actions
```

---

## Getting Started in 5 Minutes

1. **Read** `EMPIR... wait, just go:**
   ```
   open DEPLOYMENT.md
   ```
2. **Follow** the numbered steps 1–8
3. **Run** `python run.py --setup`
4. **Test** `python run.py --once`
5. **Monitor** `python run.py --health`

That's it. The bot will then run daily automatically.

---

## Support

- **First:** Check TROUBLESHOOTING.md
- **Then:** See RUNBOOKS.md for incident response
- **Finally:** Ask Atlas in Discord with context

---

**You've got this. The infrastructure is unbreakable. Now go make money.** 🗺️💰