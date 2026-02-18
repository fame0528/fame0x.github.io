# Changelog

All notable changes to the Income Bot project.

---

## [Unreleased] — Infrastructure Refinement Sprint (2026-02-18)

### Added
- **Production-grade resilience layer**
  - Exponential backoff retry with jitter (`retry_handler.py`)
  - Circuit breaker for Gemini API (`circuit_breaker.py`)
  - Persistent SQLite job queue (`job_queue.py`) for crash recovery

- **State management**
  - Full database schema (`database.py`) with keywords, articles, publish_log, metrics, audit_log, job_queue
  - Atomic state transitions and checkpointing
  - Audit trail for all actions

- **Observability**
  - Structured JSON logging with multiple handlers (`logger.py`)
  - Metrics collector (`metrics.py`) tracking articles, API calls, tokens, errors
  - Auto-generated HTML health dashboard (`health_dashboard.html`) with auto-refresh

- **Testing & Validation**
  - Unit test suite in `tests/` (pytest)
  - Integration test with mocked APIs (`tests/integration_test.py`)
  - Pre-publish validation (article length, link presence, code block balance)
  - Post-publish verification (coming in v0.2)

- **Security**
  - Config file permission enforcement (`security.py`)
  - Optional config encryption using Fernet (not enabled by default)
  - Log redaction for sensitive fields

- **Performance**
  - TTL cache for product research (`cache.py`) — 24h cache reduces duplicate fetches
  - Parallel I/O for independent operations (`parallel.py`) — thread pool for image fetching
  - Gemini prompt optimization — estimated 40% token reduction

- **Deployment Polish**
  - CLI entry point (`run.py`) with modes: `--once`, `--health`, `--test`, `--setup`
  - GitHub Actions workflow with validation tests before publishing
  - Windows installer script (`install.ps1`) for cron setup
  - Rollback script (`rollback.ps1`) for emergency recovery
  - Daily report generation in `reports/` directory

- **Documentation**
  - INFRASTRUCTURE-REFINEMENT.md — sprint plan and completion status
  - ARCHITECTURE.md — system diagrams and component interactions (TODO)
  - TROUBLESHOOTING.md — decision tree format
  - DEPLOYMENT.md — step-by-step activation guide for Spencer
  - CHANGELOG.md — this file

### Changed
- `scheduler.py` refactored to use all new infrastructure components
- `content_generator.py` now tracks `last_tokens_used` and has retry/circuit breaker
- `product_fetcher.py` now caches results
- `publisher.py` now logs commits to database and has improved error handling
- `keyword_researcher.py` now uses persistent database instead of JSON file
- All modules accept Database dependency for state persistence

### Fixed
- Removed hardcoded paths and secrets
- Improved error handling throughout
- Graceful degradation when dependencies fail

---

## [0.1.0] — Initial Prototype (2026-02-18)

### Added
- Basic content generation pipeline using Gemini 2.0 Flash
- Keyword research, product fetching, image sourcing, publishing
- Jekyll/GitHub Pages target
- Simple scheduler script
- Initial `EMPIRE-READY-STRATEGY.md` documentation
- Core `income_bot/` directory structure

### Notes
This was the proof-of-concept version that demonstrated viability but lacked resilience, monitoring, and security hardening.

---

## Versioning Scheme

We use [Semantic Versioning](https://semver.org/):
- **MAJOR** — Incompatible changes (e.g., switch from Jekyll to Hugo)
- **MINOR** — New features in a backward-compatible manner (e.g., add new niche)
- **PATCH** — Bug fixes and minor improvements

Current: **0.2.0-unreleased** (Infrastructure Sprint)

---

## Up Next (Post-Infrastructure)

- **v0.2.0** — Production deployment with real credentials
- **v0.3.0** — Multi-niche support, content rotation
- **v0.4.0** — Enhanced SEO (schema markup, auto-internal linking)
- **v0.5.0** — Earnings tracking dashboard integration
- **v1.0.0** — Fully autonomous Income Bot v1 — STABLE

---