# RSS Lead Collector

Automated lead generation system that monitors Reddit and LinkedIn (via Google Alerts) RSS feeds, filters posts using keywords, scores them with Claude AI, and saves qualified leads to Google Sheets.

## Features

- ✅ **Multi-source RSS monitoring**: Reddit subreddits and Google Alerts (LinkedIn)
- ✅ **Smart deduplication**: Checks existing URLs in Google Sheets before processing
- ✅ **Keyword filtering**: Pre-AI filtering using positive/negative keywords to reduce API costs
- ✅ **AI-powered scoring**: Claude Haiku analyzes posts for lead quality and buyer intent
- ✅ **Automated scheduling**: Runs twice daily via GitHub Actions (8:00 & 20:00 UTC)
- ✅ **Rate limiting**: Respects API limits with built-in delays
- ✅ **Error handling**: Graceful failures with detailed logging

## How It Works

```
1. Fetch RSS feeds from Reddit and Google Alerts
2. Check if URL already exists in Google Sheets (skip duplicates)
3. Filter out posts with negative keywords (spam, jobs, etc.)
4. Filter in posts with positive keywords (automation problems, etc.)
5. Score remaining posts with Claude AI
6. Save ALL posts to Google Sheets (regardless of score)
7. Print summary statistics
```

## Setup Instructions

### 1. Create Google Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable **Google Sheets API** and **Google Drive API**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Sheets API" and click "Enable"
   - Search for "Google Drive API" and click "Enable"
4. Create Service Account:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Name: `rss-collector` (or any name)
   - Click "Create and Continue"
   - Skip optional steps, click "Done"
5. Create JSON Key:
   - Click on the service account you just created
   - Go to "Keys" tab
   - Click "Add Key" > "Create new key"
   - Choose "JSON" format
   - Download the JSON file (keep it secure!)

### 2. Create Google Sheet

1. Create a new Google Sheet
2. Copy the Sheet ID from the URL:
   ```
   https://docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit
   ```
3. Share the sheet with your service account email:
   - Click "Share" button
   - Paste the service account email (found in the JSON file: `client_email`)
   - Give "Editor" permissions
   - Uncheck "Notify people"
   - Click "Share"

The script will automatically create these column headers:
```
Date | Source | Title | URL | Content | Author | Score | Problem_Type | Buyer_Intent | Reply | Status
```

### 3. Get Anthropic API Key

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to "API Keys"
4. Create a new API key
5. Copy the key (starts with `sk-ant-...`)

### 4. Configure GitHub Secrets

1. Go to your GitHub repository
2. Navigate to **Settings** > **Secrets and variables** > **Actions**
3. Click **New repository secret** and add these three secrets:

#### `ANTHROPIC_API_KEY`
```
sk-ant-api03-...
```

#### `GOOGLE_SHEETS_ID`
```
1a2b3c4d5e6f7g8h9i0j...
```
(The ID from your Google Sheets URL)

#### `GOOGLE_CREDENTIALS_JSON`
```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "rss-collector@your-project.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "..."
}
```
(Paste the **entire contents** of your downloaded JSON file)

### 5. Add Google Alerts (Optional)

To monitor LinkedIn posts via Google Alerts:

1. Go to [Google Alerts](https://www.google.com/alerts)
2. Create alerts with queries like:
   - `"took over zapier" site:linkedin.com`
   - `"nobody documented" automation site:linkedin.com`
   - `"messy automation" site:linkedin.com`
3. Set delivery to "RSS Feed"
4. Click "Create Alert"
5. Copy the RSS feed URL
6. Edit `reddit_collector.py` and uncomment/replace the placeholder URLs:
   ```python
   # Google Alerts - LinkedIn (Placeholders - Add your own URLs)
   "https://www.google.com/alerts/feeds/YOUR_FEED_ID/YOUR_USER_ID",  # "took over zapier"
   ```

## Running the Collector

### Automatic (GitHub Actions)

The collector runs automatically:
- **8:00 AM UTC** (daily)
- **20:00 PM UTC** (daily)

You can also trigger it manually:
1. Go to **Actions** tab in GitHub
2. Select "RSS Lead Collector" workflow
3. Click "Run workflow"

### Manual (Local Testing)

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_SHEETS_ID="1a2b3c4d..."
export GOOGLE_CREDENTIALS_JSON='{"type":"service_account",...}'

# Run the collector
python reddit_collector.py
```

## Configuration

### RSS Feeds

Edit `reddit_collector.py` to customize feeds:

```python
RSS_FEEDS = [
    # Reddit - New Posts
    "https://www.reddit.com/r/zapier/new/.rss",
    
    # Reddit - Search Queries
    "https://www.reddit.com/r/zapier/search.rss?q=automation&sort=new&restrict_sr=on",
    
    # Google Alerts
    "https://www.google.com/alerts/feeds/XXXX/XXXX",
]
```

### Keyword Filters

**Positive keywords** (must contain at least 1):
```python
POSITIVE_KEYWORDS = [
    "zapier", "automation", "workflow", "manual", "broke", "broken",
    "messy", "documentation", "handoff", "too many", "nobody knows",
    "tribal knowledge", "spreadsheet", "inherited", "took over",
    "process", "integration", "reporting", "undocumented",
    "maintenance", "audit", "cleanup", "lost documentation",
    "who built", "only person", "operations", "crm", "tools", "system"
]
```

**Negative keywords** (skip if contains):
```python
NEGATIVE_KEYWORDS = [
    "hiring", "job offer", "looking for work", "we are hiring",
    "salary", "resume", "portfolio", "giveaway", "promo code",
    "discount", "just launched my", "check out my", "follow me",
    "subscribe to", "crypto", "nft", "invest", "trading",
    "dating", "relationship", "meme", "funny", "joke"
]
```

### AI Scoring

The script uses **Claude 3 Haiku** for cost-effective scoring. Posts are scored 1-10:

- **9-10**: High-value leads (system broke, undocumented automation, handoff problems)
- **7-8**: Medium-value leads (messy workflows, manual work, reporting pain)
- **5-6**: General automation discussion
- **1-4**: Not relevant

**Note**: ALL posts are saved to Google Sheets regardless of score. You can filter manually in Sheets.

### Rate Limiting

```python
RATE_LIMIT_BETWEEN_POSTS = 0.5  # seconds between AI calls
RATE_LIMIT_BETWEEN_FEEDS = 1.0  # seconds between feed fetches
```

## Output

### Google Sheets Columns

| Column | Description |
|--------|-------------|
| **Date** | Timestamp when post was processed |
| **Source** | Reddit subreddit or Google Alerts |
| **Title** | Post title |
| **URL** | Direct link to post |
| **Content** | Post content (truncated to 500 chars) |
| **Author** | Post author username |
| **Score** | AI score (1-10) |
| **Problem_Type** | Category: documentation, messy_systems, manual_work, etc. |
| **Buyer_Intent** | high, medium, or low |
| **Reply** | AI-generated suggested reply (if score ≥ 7) |
| **Status** | Empty by default (for manual tracking) |

### Console Output

```
================================================================================
RSS LEAD COLLECTOR - STARTING
================================================================================

📡 Fetching feed: Reddit: r/zapier
   Found 25 posts
✓ Saved: My Zapier automation broke after update... (Score: 9)
✓ Saved: Looking for help with messy workflows... (Score: 7)

📡 Fetching feed: Reddit: r/automation (search: workflow)
   Found 18 posts
✓ Saved: Inherited undocumented automation system... (Score: 10)

================================================================================
COLLECTION SUMMARY
================================================================================
Total feeds processed:      28
Total posts fetched:        450
Total duplicates skipped:   120
Total failed keyword filter: 280
Total passed to AI:         50
Total saved to Sheets:      50
================================================================================
```

## Troubleshooting

### "Failed to connect to Google Sheets"
- Verify the service account email has Editor access to the sheet
- Check that `GOOGLE_CREDENTIALS_JSON` is valid JSON (no extra quotes/escaping)
- Ensure Google Sheets API and Drive API are enabled

### "ANTHROPIC_API_KEY environment variable not set"
- Verify the secret is named exactly `ANTHROPIC_API_KEY` in GitHub
- Check for typos in the secret value

### "Feed parsing error"
- Some feeds may be temporarily unavailable (script continues with other feeds)
- Verify Reddit RSS URLs are correct (check in browser first)

### No posts being saved
- Check keyword filters aren't too restrictive
- Verify posts aren't duplicates (already in sheet)
- Review console output for filtering statistics

## Cost Estimation

### Claude API (Haiku)
- ~$0.25 per 1M input tokens
- ~$1.25 per 1M output tokens
- Average: ~$0.001 per post scored
- **50 posts/run × 2 runs/day = ~$0.10/day = $3/month**

### Google Sheets API
- Free (up to 60 requests/minute)

## License

MIT License - Feel free to modify and use for your own lead generation needs.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review GitHub Actions logs for error details
3. Open an issue in this repository


git add .
git commit -m "Stricter AI scoring prompt"
git push