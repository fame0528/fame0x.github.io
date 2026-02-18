# Runbooks — Income Bot

Runbooks are step-by-step procedures for responding to incidents.

---

## Incident: Bot Has Stopped Publishing

**Symptoms:** No new articles for >2 days, health check shows no recent activity.

### Steps

1. **Check if scheduler is configured**
   ```powershell
   # GitHub Actions: go to repo → Actions → verify workflow is scheduled
   # Local cron: open Task Scheduler → check task runs daily
   ```

2. **Run manually to see error**
   ```powershell
   cd C:\Users\spenc\.openclaw\workspace\income_bot
   python run.py --once
   ```
   Observe output error.

3. **Common causes & fixes:**
   - **No pending keywords:** Add more seed keywords to `config.yaml` and run `--setup` to seed DB
   - **Gemini quota exceeded:** Wait until UTC midnight or add backup API key
   - **Git error:** Verify `repo_path` exists and git is in PATH; run `git status` manually in that folder
   - **Database locked:** Ensure no other process is using `data/income_bot.db`; restart

4. **If stuck, restart entire system**
   ```powershell
   # Kill any running Python processes
   taskkill /f /im python.exe 2>$null
   # Re-run
   python run.py --once
   ```

5. **Verify resolution:**
   - Article published to `live_site/_posts/`
   - GitHub push succeeded
   - Health check shows GREEN

---

## Incident: Gemini API Quota Exceeded

**Symptoms:** Errors mentioning "quota" or "rate limit" in logs.

### Steps

1. **Check current usage**
   - Google AI Studio: https://makersuite.google.com/app/apikey
   - View usage for your key

2. **Short-term fix:**
   - Wait for daily reset (UTC midnight). Bot will resume automatically then.
   - Or temporarily reduce to `.github/workflows/daily.yml` cron to run every other day: `0 8 */2 * *`

3. **Long-term fix:**
   - Option A: Add a second Gemini API key (backup). Edit `config.yaml` with `gemini_backup_api_key` and implement fallback in `ContentGenerator` (future feature).
   - Option B: Reduce daily generation to 1 article every 2 days to stay under limit.
   - Option C: Switch to a different free-tier model (Claude Desktop, Perplexity) — requires code changes.

4. **Monitoring:**
   - Watch `logs/` for "tokens_used" entries
   - Set alert: if tokens in a day exceed 1.8M, warn

---

## Incident: GitHub Actions Workflow Failing

**Symptoms:** Actions tab shows red X on daily workflow.

### Steps

1. **Open the failed workflow run**
   - Click on the red X
   - Review "Jobs" → "Run content_generator" → "Steps" to see which step failed

2. **Common failures:**
   - **"GEMINI_API_KEY not set"**: Add repository secret (Settings → Secrets → Actions)
   - **"Permission denied"**: Check that the GITHUB_TOKEN has write permissions (default has)
   - **"No space left on device"**: GitHub runner issue; retry job
   - **"ModuleNotFoundError"**: Ensure `requirements.txt` includes all deps; workflow may need `pip install -r requirements.txt`

3. **If failure is transient:**
   - Click "Re-run all jobs"

4. **If failure persists:**
   - Clone the repo locally and run `python run.py --once` to reproduce error
   - Fix locally, push changes

5. **Verify fix:**
   - Re-run Actions workflow manually
   - Ensure green checkmark

---

## Incident: Articles Publishing But Not Appearing on Site

**Symptoms:** GitHub Actions shows success, but `YOURUSERNAME.github.io` shows no new content.

### Steps

1. **Confirm GitHub Pages build status**
   - Repository → Settings → Pages
   - Check "Build status": should be "Passed"
   - If "Failed", click "View deployment" to see Jekyll build error

2. **Check site URL**
   - Ensure you're visiting `https://YOURUSERNAME.github.io` (not `http` or `www`)
   - Wait up to 5 minutes after push for build

3. **Verify Jekyll configuration**
   - Ensure `_config.yml` exists in repo root
   - Minimal `_config.yml`:
     ```yaml
     plugins:
       - jekyll-seo-tag
     title: "Your Blog"
     ```
   - Commit and push if missing

4. **Force rebuild**
   ```powershell
   cd live_site
   git commit --allow-empty -m "trigger rebuild" && git push
   ```

5. **Check _posts folder**
   - Verify `_posts/pet-care-supplements/` exists and contains `.md` files
   - If folder missing, check `publisher.py` — category name may be wrong

---

## Incident: Low-Quality Articles Being Published

**Symptoms:** Articles are very short, missing affiliate links, or lack substance.

### Steps

1. **Check logs for validation warnings**
   ```powershell
   Get-Content logs\$(Get-Date -Format yyyy-MM-dd).jsonl | Select-String "validation"
   ```

2. **Review the article content directly**
   - Look at file in `_posts/` folder
   - Is the prompt in `ContentGenerator._build_prompt` too minimal?
   - Does it include word count target and structure?

3. **Tune the prompt**
   - Edit `src/content_generator.py`
   - Increase desired word count: "Write approximately 2500 words"
   - Add mandatory sections: "Include a detailed comparison table with at least 5 columns"
   - Add explicit instruction: "Place affiliate links using the format [AMAZON_LINK_{product_name}] in at least 3 places"

4. **Validate on a test run**
   ```powershell
   python run.py --once
   ```
   Inspect output article in `_posts/` before commit.

5. **If quality remains poor:**
   - Gemini 2.0 Flash may be hitting quality ceilings. Consider switching to a more capable model (Gemini 1.5 Pro, if still free) — update `model='gemini-1.5-pro'` in `content_generator.py`.

---

## Incident: Affiliate Links Not Converting

**Symptoms:** Clicks are happening in analytics but no commission after 24h.

### Steps

1. **Verify tracking IDs are correct**
   - Amazon: URL should contain `?tag=yourtag-20`
   - ShareASale: Check merchant's reporting

2. **Check cookie duration**
   - Amazon: 24-hour cookie (no persistence beyond)
   - ShareASale: varies by merchant (often 30-90 days)
   - Ensure you're not clicking your own links (fraud detection)

3. **Test a conversion yourself**
   - Click an article link → add item to cart → checkout with test account
   - See if commission registers (may take 24-48h)

4. **Validate article has links**
   - Search `_posts/` for `amazon.com` or affiliate domain
   - If links missing, check `ProductFetcher` is returning URLs and `Publisher` is replacing placeholders

5. **If all looks correct but still no revenue:**
   - Traffic may be too low (< 10 clicks/day)
   - Focus on SEO: improve content depth, build backlinks (manual outreach)
   - Consider adding more products per article to increase options

---

## Incident: Database Corruption / Lock

**Symptoms:** Errors about "database is locked" or "cannot open database file".

### Steps

1. **Check for zombie processes**
   - Open Task Manager → Python processes → kill any `run.py` or `pytest` that may have crashed

2. **Ensure file permissions**
   ```powershell
   icacls data\income_bot.db
   ```
   Should show your user has Full Control

3. **If corrupted, restore from backup**
   - DB is not backed up automatically yet. If corrupt, you may lose state.
   - Recreate by running `python run.py --setup` to seed keywords again.
   - Published articles remain in Git; history in `publish_log` may be lost but that's okay.

4. **Prevention:**
   - Always close DB connection (already in finally block)
   - Avoid running multiple instances simultaneously

---

## Emergency: Rollback a Bad Deployment

If a code change broke the bot, revert to last known good state:

```powershell
cd live_site
git log --oneline -10   # find commit before the bad push
git revert <bad_commit_sha>
git push
```

Or use `rollback.ps1`:
```powershell
.\rollback.ps1 -CommitSha <good_sha>
```

Then re-deploy the previous code version from your backup or Git history.

---

## Routine Maintenance

### Daily (Automated)
- GitHub Actions publishes 1 article at 8 AM UTC
- Health check runs after each publish
- Discord alerts on failures

### Weekly (Manual, 10 minutes)
1. Review `reports/` directory for last week
2. Check any ERROR logs in `logs/`
3. Verify GitHub Actions succeeded each day
4. Add 5-10 new seed keywords to `config.yaml` if needed (or let bot cycle)

### Monthly (Manual, 20 minutes)
1. Check affiliate dashboards: Amazon Associates, ShareASale
2. Update `metrics` table manually if needed to reflect actual earnings (optional)
3. Rotate Gemini API key (free, but good hygiene)
4. Review `health_status.json` trends
5. Update niche if desired

---

## Support Escalation

If all else fails and you cannot resolve:
1. **Pause the bot** — disable GitHub Actions workflow temporarily
2. **Gather info:** logs (`income_bot/logs/`), DB (`sqlite3 data/income_bot.db "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 50"`), and health status
3. **Contact:** Ping me (Atlas) in Discord with the above data
4. I'll diagnose and provide fix or hotfix deployment

---

**Keep this runbook handy during the first 30 days of operation.** 🗺️