# Troubleshooting Guide — Income Bot

Follow this decision tree when something goes wrong.

---

## Start: Is the bot running?

### No articles being published?

1. **Is GitHub Pages set up?**
   - Go to repository Settings → Pages
   - Verify source is set to main branch / (root)
   - If not, configure and wait 2 minutes

2. **Did GitHub Actions trigger?**
   - Go to repository → Actions tab
   - Check if "Daily Content Generation" workflow ran today
   - If not, check cron schedule (8 AM UTC daily)
   - You can trigger manually: Actions → Run workflow

3. **Are there pending keywords?**
   - Check `data/keywords.json` or database
   - Run `python run.py --once` manually to see if it outputs "No pending keywords"
   - If empty, that's expected (all done). Add more seed keywords to config or let it recycle after a week

---

## GitHub Actions Failed

Open the failed workflow run → Check logs.

### Error: `GEMINI_API_KEY` not set
- Add repository secret: Settings → Secrets → Actions → `GEMINI_API_KEY`

### Error: `Repository not found` or permission denied
- The GITHUB_TOKEN in Actions already has permissions; no issue
- If using custom SSH, check deploy keys

### Error: `No space left on device` (runner disk full)
- This is GitHub's runner; unlikely. Retry the workflow.

### Error: `Quota exceeded` for Gemini
- Gemini free tier: 2M tokens/day. You may have exceeded.
- Wait until UTC midnight reset, OR
- Reduce daily article count (modify workflow cron to run less often)
- OR add backup API key (future enhancement)

---

## Local Run (`python run.py --once`) Fails

### Error: `Gemini API key not provided`
- Check `config.yaml` has `gemini_api_key` set correctly
- Or set environment variable `GEMINI_API_KEY`

### Error: `repo_path does not exist`
- Create the folder: `mkdir C:\path\to\live_site`
- Or clone your GitHub Pages repo there

### Error: Git command failed
- Ensure `git` is in PATH
- Verify you have write permissions to the repo
- Try running `git status` manually in the repo path

### Error: No module named 'google.generativeai'
- Install dependencies: `pip install -r requirements.txt`

---

## Articles Publishing but Site Not Updating

1. **Check GitHub Pages build status**
   - Settings → Pages → Build status
   - If failed, view build log

2. **Verify Jekyll processing**
   - Your repo must have `_config.yml` (Jekyll config)
   - Generate it: create simple `_config.yml` with:
     ```yaml
     plugins:
       - jekyll-seo-tag
     title: "Your Blog"
     ```
   - Commit and push

3. **Force rebuild**
   - Push an empty commit: `git commit --allow-empty -m "trigger" && git push`
   - Or enable "Re-run jobs" in Actions

---

## Articles Are Low Quality

**Symptom:** Thin content, missing affiliate links, poor formatting.

1. **Check prompt template in `src/content_generator.py`**
   - Increase word count target
   - Add more explicit E-E-A-T instructions
   - Require specific sections (Testing Methodology, FAQ)

2. **Validate article before publishing** (already enabled)
   - Look for warnings in logs: "Article validation issues"
   - If placeholders missing, may be Gemini not following instructions

3. **Improve prompt:**
   - Add: "Write at least 2000 words"
   - Add: "Include 5 frequently asked questions"
   - Add: "Use first-person narrative: 'I tested these products...'"

---

## Gemini Quota Exhausted

**Symptom:** Articles stop generating, errors about quota.

1. **Wait for reset** (UTC midnight)
2. **Add backup API key** (modify config to have `gemini_backup_api_key` and fallback logic)
3. **Reduce frequency:**
   - Change GitHub Actions cron from daily to every other day: `0 8 */2 * *`
   - Or reduce number of articles per run (currently 1)

---

## Affiliate Links Not Working

1. **Placeholders not replaced?**
   - Ensure `amazon_tracking_id` is set in config
   - Publisher replaces placeholders like `[AMAZON_LINK_PROD_NAME]` with actual URLs
   - Check logs for "missing affiliate links" warning

2. **Links show but no commission?**
   - Verify your tracking ID is correct in the URL
   - Wait until affiliate program approves the product
   - Some programs require cookies; ensure links are direct

---

## No Traffic After 2 Months

1. **Check Google Search Console**
   - Verify site is indexed
   - Look for "Coverage" issues
   - Submit sitemap

2. **Improve SEO:**
   - Add meta descriptions (modify content prompt to include them)
   - Add schema markup (FAQ, Product)
   - Build internal links between articles

3. **Promote manually:**
   - Share articles on Reddit (relevant subreddits)
   - Post in Facebook groups for dog owners
   - Answer related Quora questions with links

---

## Health Check Reports RED

Run `python run.py --health` and check:

- **GitHub Pages:** RED → repo not accessible or no posts
- **Affiliate Links:** RED → articles missing links → check product_fetcher URLs
- **Recent Activity:** RED → no recent commits → check if bot is running

---

## Emergency Rollback

If a bad commit broke the site:

```powershell
cd live_site
git log --oneline  # find previous good commit SHA
git revert <bad_commit_sha>
git push
```

Or use the provided `rollback.ps1` script:
```powershell
.\rollback.ps1 -CommitSha <good_sha>
```

---

## Log Locations

- **Structured logs:** `income_bot/logs/YYYY-MM-DD.jsonl` (one line per JSON event)
- **Health status:** `income_bot/health_status.json` (generated after each run)
- **Daily reports:** `income_bot/reports/YYYY-MM-DD.md`
- **Database:** `income_bot/data/income_bot.db` (SQLite state)
- **Git logs:** `cd live_site && git log`

---

## Need More Help?

1. Check logs first — they have structured data
2. Look for ERROR or CRITICAL entries
3. Verify config values
4. Run integration test: `pytest tests/` (requires pytest)
5. Review DEPLOYMENT.md setup steps

If truly stuck, ping me and I'll diagnose. 🗺️