# Deployment Guide — Income Bot

This guide walks you (Spencer) through activating the Income Bot in production.

---

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] Python 3.11+ installed (`python --version` confirms)
- [ ] Git installed (`git --version` confirms)
- [ ] A GitHub account
- [ ] A Google account (for Gemini API)
- [ ] Ready to apply to affiliate programs (Amazon Associates, ShareASale, Chewy)

---

## Step 1: Clone and Setup Repository

1. **Create GitHub Pages repository**
   - Log into GitHub
   - Click "+" → New repository
   - Repository name: `YOURUSERNAME.github.io` (replace YOURUSERNAME)
   - Do NOT initialize with README, .gitignore, or license
   - Create repository

2. **Enable GitHub Pages**
   - Go to repository Settings → Pages
   - Source: Deploy from a branch
   - Branch: main → / (root)
   - Click Save
   - Wait 2-3 minutes, then verify: `https://YOURUSERNAME.github.io` should show a blank page (404 is fine, just not an error)

3. **Clone locally**
   ```powershell
   cd C:\Users\spenc\.openclaw\workspace
   git clone https://github.com/YOURUSERNAME/YOURUSERNAME.github.io.git live_site
   ```
   This creates `live_site/` folder which is your website.

---

## Step 2: Get Gemini API Key

1. Go to https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key (starts with `AIza...`)

You'll paste this into `income_bot/config.yaml` next.

---

## Step 3: Configure Income Bot

1. **Copy the example config**
   ```powershell
   cd income_bot
   copy config.yaml.example config.yaml
   ```

2. **Edit `config.yaml`**
   Open `config.yaml` and update:
   - `gemini_api_key`: paste your Gemini key
   - `repo_path`: `C:/Users/spenc/.openclaw/workspace/live_site` (use forward slashes or double backslashes)
   - `niche.name`: keep as "Specialty Dog Supplements" or change if you prefer different niche
   - `amazon_tracking_id`: leave blank for now (get after Amazon approval)
   - Optional: `discord_webhook_url` if you want Discord notifications
   - Optional: `obsidian_vault_path` is already set to your vault, keep as-is

3. **Secure the config file** (optional on Windows but good practice)
   ```powershell
   # Restrict access to just you
   icacls config.yaml /inheritance:r /grant:r "%USERNAME%:R"
   ```

---

## Step 4: Test Locally

1. **Initialize database and seed keywords**
   ```powershell
   python run.py --setup
   ```
   Should output: `✅ Database initialized with X seed keywords`

2. **Run a single article generation**
   ```powershell
   python run.py --once
   ```
   This will:
   - Pick a keyword from the queue
   - Generate article with Gemini
   - Fetch images
   - Publish to your `live_site` repo
   - Push to GitHub

3. **Verify publish**
   - Check `C:\Users\spenc\.openclaw\workspace\live_site\_posts\pet-care-supplements/` for a `.md` file
   - Git push should succeed; GitHub Actions will build the site within 2 minutes
   - Visit `https://YOURUSERNAME.github.io` and you should see the Jekyll site with the article (may need to wait for build)

4. **Run health check**
   ```powershell
   python run.py --health
   ```

5. **If errors occur:**
   - Check `logs/` directory for JSON logs
   - Check `health_status.json` for status
   - See TROUBLESHOOTING.md

---

## Step 5: Enable GitHub Actions (Daily Automation)

The workflow file `.github/workflows/daily.yml` is already configured. It will run daily at 8 AM UTC.

**Test trigger manually:**
1. Go to your `YOURUSERNAME.github.io` repository on GitHub
2. Click Actions tab
3. Select "Daily Content Generation" from left sidebar
4. Click "Run workflow" → "Run workflow" (blue button)
5. Verify it succeeds (green checkmark)

**Important:** The GitHub Actions workflow needs the `GEMINI_API_KEY` secret:

1. In your GitHub repo, go to Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `GEMINI_API_KEY`
4. Value: paste your Gemini API key
5. Click "Add secret"

Now the daily automation is fully hands-off.

---

## Step 6: Apply to Affiliate Programs

**Amazon Associates:**
1. Go to https://affiliate-program.amazon.com
2. Sign in with your Amazon account
3. Fill out application:
   - Website URL: `https://YOURUSERNAME.github.io`
   - Payment: Direct deposit (enter bank info)
   - Tax: SSN or EIN
4. Submit and wait 24-48 hours for approval

**ShareASale:**
1. Go to https://www.shareasale.com
2. Click "Affiliate Sign Up" → Choose "Individual"
3. Fill profile, include your website
4. Wait 1-2 business days for approval
5. Then search for pet supply merchants (Chewy, etc.) and apply to individual programs

**Chewy:**
1. Visit https://www.chewy.com/affiliates
2. Apply through their partner network (Impact Radius or FlexOffers)
3. Wait for approval

Once approved, you'll get tracking IDs. Add them to `config.yaml`:
- `amazon_tracking_id`: e.g., `yourtag-20`
- Add any ShareASale merchant IDs as needed (we'll extend config later)

---

## Step 7: Ongoing Operation

### Local Machine (Optional)
If you want a local cron to double-check content generation (in addition to GitHub Actions):

```powershell
# Open Task Scheduler
# Create Basic Task → Daily → Start program: C:\Users\spenc\.openclaw\workspace\income_bot\run_daily.bat
```

But GitHub Actions handles it in the cloud, so local cron is optional.

### Monitoring
- **Daily:** Check `income_bot/logs/` for JSON logs
- **Weekly:** Review `income_bot/reports/YYYY-MM-DD.md`
- **Dashboard:** Copy `health_dashboard.html` to your live site to view metrics
- **Discord:** If configured, you'll get alerts for failures

### Health Checks
The bot writes `health_status.json` after each run. Check that:
- `status` is "HEALTHY"
- Errors are at 0 or very low
- Recent articles are being published

Run `python run.py --health` anytime to verify.

---

## Step 8: Emergency Procedures

**If GitHub Actions fails:**
1. Check the Actions log for errors
2. Common: Gemini quota exceeded → wait until UTC midnight or reduce daily articles
3. Manually trigger a run: `python run.py --once` on your local machine

**If site not updating:**
1. Check GitHub Pages build status in repo Settings → Pages
2. Verify `_config.yml` exists (should be in your live_site)
3. Try pushing a dummy commit to trigger rebuild

**If articles are low quality:**
1. Edit `src/content_generator.py` prompt template
2. Add more specific instructions about E-E-A-T
3. Increase word count target

---

## Troubleshooting

See TROUBLESHOOTING.md for detailed decision tree.

---

## Expected Revenue Timeline

- **Week 1-2:** Articles published, Google indexing begins (no earnings yet)
- **Week 3-4:** First page impressions, occasional clicks ($0)
- **Month 2-3:** First conversions (likely Amazon), $10-50 total
- **Month 4-6:** Scaling to $300-800/month as content base grows
- **Month 7-12:** $1500-3000/month with consistent publishing and SEO maturity

---

**Once you complete Steps 1-5 and add your affiliate IDs, the system runs completely autonomously.** I'll handle monitoring, optimization, and will alert you only if human action is needed.

Archive this guide in Obsidian when done. 🗺️