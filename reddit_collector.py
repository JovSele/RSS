#!/usr/bin/env python3
"""
RSS Lead Collector for Reddit and Google Alerts
Monitors RSS feeds, filters by keywords, scores with Claude AI, and saves to Google Sheets
"""

import os
import sys
import json
import time
import re
from datetime import datetime
from typing import List, Dict, Set, Optional
import feedparser
import gspread
from google.oauth2.service_account import Credentials
from anthropic import Anthropic
from bs4 import BeautifulSoup

# ============================================================================
# CONFIGURATION
# ============================================================================

# RSS Feeds to monitor
RSS_FEEDS = [
     # Reddit - New Posts
    "https://www.reddit.com/r/zapier/new.rss",
    "https://www.reddit.com/r/nocode/new.rss",
    "https://www.reddit.com/r/automation/new.rss",
    "https://www.reddit.com/r/smallbusiness/new.rss",
    "https://www.reddit.com/r/Entrepreneur/new.rss",
    "https://www.reddit.com/r/startups/new.rss",
    "https://www.reddit.com/r/revops/new.rss",
    "https://www.reddit.com/r/operations/new.rss",
    "https://www.reddit.com/r/agency/new.rss",
    "https://www.reddit.com/r/shopify/new.rss",
    "https://www.reddit.com/r/hubspot/new.rss",
    "https://www.reddit.com/r/salesforce/new.rss",
    "https://www.reddit.com/r/ecommerce/new.rss",
    "https://www.reddit.com/r/SaaS/new.rss",
    
    # Reddit - Search Queries (sort=new)
    "https://www.reddit.com/r/zapier/search.rss?q=zapier&sort=new&restrict_sr=on",
    "https://www.reddit.com/r/zapier/search.rss?q=automation&sort=new&restrict_sr=on",
    "https://www.reddit.com/r/zapier/search.rss?q=workflow&sort=new&restrict_sr=on",
    "https://www.reddit.com/r/zapier/search.rss?q=problem&sort=new&restrict_sr=on",
    "https://www.reddit.com/r/zapier/search.rss?q=error&sort=new&restrict_sr=on",
    "https://www.reddit.com/r/zapier/search.rss?q=expensive&sort=new&restrict_sr=on",
    "https://www.reddit.com/r/nocode/search.rss?q=automation&sort=new&restrict_sr=on",
    "https://www.reddit.com/r/nocode/search.rss?q=workflow&sort=new&restrict_sr=on",
    "https://www.reddit.com/r/automation/search.rss?q=workflow&sort=new&restrict_sr=on",
    "https://www.reddit.com/r/automation/search.rss?q=integration&sort=new&restrict_sr=on",
    "https://www.reddit.com/r/smallbusiness/search.rss?q=automation&sort=new&restrict_sr=on",
    "https://www.reddit.com/r/smallbusiness/search.rss?q=tools&sort=new&restrict_sr=on",
    "https://www.reddit.com/r/revops/search.rss?q=automation&sort=new&restrict_sr=on",
    "https://www.reddit.com/r/agency/search.rss?q=zapier&sort=new&restrict_sr=on",
    
    # Google Alerts - LinkedIn (Placeholders - Add your own URLs)
    "https://www.google.com/alerts/feeds/10605284653761947770/17547666453224584072",  # took over zapier
    "https://www.google.com/alerts/feeds/10605284653761947770/11799962196978559227",  # inherited automation
    "https://www.google.com/alerts/feeds/10605284653761947770/11205966101093525896",  # zapier audit
    "https://www.google.com/alerts/feeds/10605284653761947770/2957016071162074905",   # zapier broke
    "https://www.google.com/alerts/feeds/10605284653761947770/3088012883186134098",   # too many zaps
    "https://www.google.com/alerts/feeds/10605284653761947770/8706557038309823380",   # messy zaps
    "https://www.google.com/alerts/feeds/10605284653761947770/16545658599802679305",  # zapier maintenance
    "https://www.google.com/alerts/feeds/10605284653761947770/6875575467182349121",   # workflow handoff
    "https://www.google.com/alerts/feeds/10605284653761947770/10698494035640013000",  # automation handoff
    "https://www.google.com/alerts/feeds/10605284653761947770/5283008468998240233",   # undocumented workflows
    "https://www.google.com/alerts/feeds/10605284653761947770/2944949419624491757",   # nobody documented
    "https://www.google.com/alerts/feeds/10605284653761947770/10638649173406501531",  # tribal knowledge
    "https://www.google.com/alerts/feeds/10605284653761947770/637427977252961531",    # lost documentation
    "https://www.google.com/alerts/feeds/10605284653761947770/9947997926182776142",   # who built this
    "https://www.google.com/alerts/feeds/10605284653761947770/16104753547817923697",  # nobody knows how
    "https://www.google.com/alerts/feeds/10605284653761947770/4834273587035497087",   # only person who
    "https://www.google.com/alerts/feeds/10605284653761947770/9947997926182774748",   # took over automation
    "https://www.google.com/alerts/feeds/10605284653761947770/13365351787220754925",  # workflow documentation
    "https://www.google.com/alerts/feeds/10605284653761947770/1239498199882998243",   # too many tools
    "https://www.google.com/alerts/feeds/10605284653761947770/8699520351222471960",   # spreadsheet tracking
]

# Positive keywords (must contain at least 1)
POSITIVE_KEYWORDS = [
    "automate zapier", "automation audit", "automation broke",
    "automation handoff", "automation maintenance", "automation stopped",
    "clean up zapier", "copy paste", "document workflows",
    "documentation missing", "doing this manually", "excel tracking",
    "inherited automation", "inherited this", "inherited zaps",
    "knowledge transfer", "left the company", "lost documentation",
    "maintaining zapier", "manual client onboarding", "manual crm",
    "manual process", "messy zaps", "need zapier help",
    "nobody documented", "nobody knows how", "one who knows",
    "only one who", "only person who", "operations are messy",
    "operations chaos", "person who knows", "person who understands",
    "process documentation", "repetitive task", "reverse engineering",
    "spreadsheet tracking", "systems are messy", "too many automations",
    "too many spreadsheets", "too many tools", "too many zaps",
    "took over automation", "took over zapier", "tracking in excel",
    "tribal knowledge", "undocumented workflows", "who built this",
    "workflow documentation", "workflow handoff", "workflow is messy",
    "zap breaking", "zap failed", "zap stopped working",
    "zapier audit", "zapier broke", "zapier cleanup", "zapier help",
    "zapier maintenance", "zapier setup", "zapier tasks limit"
]

# Negative keywords (skip if contains)
NEGATIVE_KEYWORDS = [
    "amazon", "apply for", "apply now", "book a call", "book a demo",
    "bootcamp", "captcha", "case study", "comment below", "construction",
    "course", "cv", "data entry work", "dm me", "download", "ebook",
    "ecommerce", "followers", "free audit", "free trial", "guide",
    "healthcare", "hiring", "home job", "check out our", "schedule a",
    "imo app", "interested candidates", "job", "job opening", "jobs",
    "link below", "link in comments", "location", "logistics",
    "manufacturing", "newsletter", "now hiring", "our platform",
    "our solution", "pan india", "podcast", "real estate", "recruiter",
    "repost", "resume", "send cv", "shopify", "sign up",
    "signal messenger", "supply chain", "template", "training",
    "typing work", "urgent role", "we are hiring", "we build",
    "we help", "we offer", "webinar", "whatsapp number",
    "whitepaper", "work from home"
]


# AI Scoring Prompt Template
AI_PROMPT_TEMPLATE = """You are a lead scoring assistant for Relay Reports (relayreports.app) — a tool that analyzes Zapier exports and generates automation documentation.

Analyze this post:

TITLE: {title}
CONTENT: {content}
SOURCE: {source}

Return ONLY raw JSON, no markdown, no backticks:
{{
  "score": <1-5>,
  "problem_type": "<documentation | messy_systems | manual_work | broken_automation | cost_problem | handoff | irrelevant>",
  "buyer_intent": "<high | medium | low>",
  "reason": "<1 sentence referencing something SPECIFIC from this post>"
}}

SCORING:

5 — Person has Zapier/automation chaos, inherited workflows, needs documentation or handoff, asking for help. ALL must be true:
- Asking for help, not sharing a solution
- Specific pain: inherited zaps, nobody knows how it works, handoff nightmare, lost documentation
- Content longer than 2 sentences

4 — Person describes manual processes, messy operations, too many tools, broken automation, workflow problems

3 — General automation discussion, adjacent conversation about operations

2 — Vendor promoting services, thought leadership, success stories, "I built X"

1 — MANDATORY for: hiring, job, resume, CV, recruiter, spam, promo ("check out my", "dm me", "free audit", "we offer", "sign up"), humor, empty posts

Ideal customer: Zapier power users, operations managers, no-code consultants, automation agencies.
"""


# Rate limiting
RATE_LIMIT_BETWEEN_POSTS = 0.5  # seconds
RATE_LIMIT_BETWEEN_FEEDS = 1.0  # seconds

# Content truncation
MAX_CONTENT_FOR_SHEETS = 500  # characters
MAX_CONTENT_FOR_AI = 600  # characters

# Google Sheets columns
SHEET_COLUMNS = ["Date", "Source", "Title", "URL", "Content", "Author", "Score", "Problem_Type", "Buyer_Intent", "Reply", "Status"]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def clean_html(text: str) -> str:
    """Remove HTML tags and clean up text"""
    if not text:
        return ""
    soup = BeautifulSoup(text, 'html.parser')
    text = soup.get_text()
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def truncate_text(text: str, max_length: int) -> str:
    """Truncate text to max_length characters"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def contains_positive_keyword(text: str) -> bool:
    """Check if text contains at least one positive keyword"""
    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in POSITIVE_KEYWORDS)

def contains_negative_keyword(text: str) -> bool:
    """Check if text contains any negative keyword"""
    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in NEGATIVE_KEYWORDS)

def extract_source_name(feed_url: str) -> str:
    """Extract a readable source name from feed URL"""
    if "reddit.com" in feed_url:
        # Extract subreddit name
        match = re.search(r'/r/([^/]+)/', feed_url)
        if match:
            subreddit = match.group(1)
            if "search.rss" in feed_url:
                # Extract search query
                query_match = re.search(r'q=([^&]+)', feed_url)
                if query_match:
                    query = query_match.group(1)
                    return f"Reddit: r/{subreddit} (search: {query})"
            return f"Reddit: r/{subreddit}"
    elif "google.com/alerts" in feed_url:
        return "Google Alerts (LinkedIn)"
    return feed_url

# ============================================================================
# GOOGLE SHEETS INTEGRATION
# ============================================================================

class GoogleSheetsClient:
    """Handle Google Sheets operations"""
    
    def __init__(self, credentials_json: str, sheet_id: str):
        """Initialize Google Sheets client"""
        try:
            creds_dict = json.loads(credentials_json)
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            self.client = gspread.authorize(credentials)
            self.sheet = self.client.open_by_key(sheet_id).sheet1
            print(f"✓ Connected to Google Sheets: {sheet_id}")
        except Exception as e:
            print(f"✗ CRITICAL: Failed to connect to Google Sheets: {e}")
            raise
    
    def get_existing_urls(self) -> Set[str]:
        """Get all existing URLs from the sheet to avoid duplicates"""
        try:
            # Get all values from URL column (column D, index 3)
            all_values = self.sheet.get_all_values()
            if len(all_values) <= 1:  # Only header or empty
                return set()
            
            # Extract URLs (skip header row)
            urls = set()
            for row in all_values[1:]:
                if len(row) > 3 and row[3]:  # URL is in column index 3
                    urls.add(row[3])
            
            print(f"✓ Loaded {len(urls)} existing URLs from sheet")
            return urls
        except Exception as e:
            print(f"⚠ Warning: Could not load existing URLs: {e}")
            return set()
    
    def ensure_headers(self):
        """Ensure the sheet has proper headers"""
        try:
            first_row = self.sheet.row_values(1)
            if not first_row or first_row != SHEET_COLUMNS:
                self.sheet.update('A1:K1', [SHEET_COLUMNS])
                print("✓ Sheet headers initialized")
        except Exception as e:
            print(f"⚠ Warning: Could not set headers: {e}")
    
    def append_row(self, row_data: List[str]):
        """Append a row to the sheet"""
        try:
            self.sheet.append_row(row_data)
        except Exception as e:
            print(f"⚠ Warning: Failed to append row: {e}")
            raise

# ============================================================================
# AI SCORING
# ============================================================================

class AIScorer:
    """Handle Claude AI scoring"""
    
    def __init__(self, api_key: str):
        """Initialize Anthropic client"""
        self.client = Anthropic(api_key=api_key)
        print("✓ Claude AI client initialized")
    
    def score_post(self, title: str, content: str, source: str) -> Optional[Dict]:
        """Score a post using Claude AI"""
        try:
            # Prepare prompt
            prompt = AI_PROMPT_TEMPLATE.format(
                title=title,
                content=truncate_text(content, MAX_CONTENT_FOR_AI),
                source=source
            )
            
            # Call Claude API
            message = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=150,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parse response
            response_text = message.content[0].text.strip()
            
            # Try to extract JSON from response
            # Sometimes Claude wraps JSON in markdown code blocks
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)
            
            result = json.loads(response_text)
            
            # Validate required fields
            required_fields = ["score", "problem_type", "buyer_intent", "reason"]
            if not all(field in result for field in required_fields):
                print(f"⚠ Warning: AI response missing required fields")
                return None
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"⚠ Warning: Failed to parse AI JSON response: {e}")
            return None
        except Exception as e:
            print(f"⚠ Warning: AI scoring failed: {e}")
            return None

# ============================================================================
# MAIN COLLECTOR
# ============================================================================

class RSSCollector:
    """Main RSS collector orchestrator"""
    
    def __init__(self):
        """Initialize the collector"""
        # Load environment variables
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.google_sheets_id = os.getenv('GOOGLE_SHEETS_ID')
        self.google_credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
        
        # Validate environment variables
        if not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        if not self.google_sheets_id:
            raise ValueError("GOOGLE_SHEETS_ID environment variable not set")
        if not self.google_credentials_json:
            raise ValueError("GOOGLE_CREDENTIALS_JSON environment variable not set")
        
        # Initialize clients
        self.sheets_client = GoogleSheetsClient(self.google_credentials_json, self.google_sheets_id)
        self.sheets_client.ensure_headers()
        self.ai_scorer = AIScorer(self.anthropic_api_key)
        
        # Load existing URLs for deduplication
        self.existing_urls = self.sheets_client.get_existing_urls()
        
        # Statistics
        self.stats = {
            'feeds_processed': 0,
            'posts_fetched': 0,
            'duplicates_skipped': 0,
            'failed_keyword_filter': 0,
            'passed_to_ai': 0,
            'saved_to_sheets': 0
        }
    
    def fetch_feed(self, feed_url: str) -> List[Dict]:
         """Fetch and parse an RSS feed"""
         try:
             import random
             user_agents = [
                 "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                 "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                 "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
             ]
             headers = {
                 "User-Agent": random.choice(user_agents),
                 "Accept": "application/rss+xml, application/xml, text/xml, */*",
             }
             feed = feedparser.parse(feed_url, request_headers=headers)
        
             if feed.bozo:
                 print(f"⚠ Warning: Feed parsing error for {feed_url}: {feed.bozo_exception}")
                 return []
            
            posts = []
            for entry in feed.entries:
                post = {
                    'title': entry.get('title', ''),
                    'url': entry.get('link', ''),
                    'content': entry.get('summary', '') or entry.get('content', [{}])[0].get('value', ''),
                    'author': entry.get('author', ''),
                    'published': entry.get('published', ''),
                    'source': extract_source_name(feed_url)
                }
                posts.append(post)
            
            return posts
            
        except Exception as e:
            print(f"⚠ Warning: Failed to fetch feed {feed_url}: {e}")
            return []
    
    def process_post(self, post: Dict) -> bool:
        """Process a single post through the pipeline"""
        # Check for duplicate URL
        if post['url'] in self.existing_urls:
            self.stats['duplicates_skipped'] += 1
            return False
        
        # Clean HTML from content
        clean_content = clean_html(post['content'])
        combined_text = f"{post['title']} {clean_content}"
        
        # Apply negative keyword filter
        if contains_negative_keyword(combined_text):
            self.stats['failed_keyword_filter'] += 1
            return False
        
        # Apply positive keyword filter
        if not contains_positive_keyword(combined_text):
            self.stats['failed_keyword_filter'] += 1
            return False
        
        # Rate limit before AI call
        time.sleep(RATE_LIMIT_BETWEEN_POSTS)
        
        # Score with AI
        self.stats['passed_to_ai'] += 1
        ai_result = self.ai_scorer.score_post(
            post['title'],
            clean_content,
            post['source']
        )
        
        if not ai_result:
            # AI scoring failed, but we still save the post with empty AI fields
            ai_result = {
                'score': '',
                'problem_type': '',
                'buyer_intent': '',
                'reason': '',
                'suggested_reply': ''
            }
        
        # Clean the suggested reply
        ai_result.get('suggested_reply', ''),  # Reply
        
        # Prepare row for Google Sheets
        row = [
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # Date
            post['source'],  # Source
            post['title'],  # Title
            post['url'],  # URL
            truncate_text(clean_content, MAX_CONTENT_FOR_SHEETS),  # Content
            post['author'],  # Author
            str(ai_result.get('score', '')),  # Score
            ai_result.get('problem_type', ''),  # Problem_Type
            ai_result.get('buyer_intent', ''),  # Buyer_Intent
            ai_result.get('suggested_reply', ''),  # Reply
            ''  # Status (empty by default)
        ]
        
        # Save to Google Sheets
        try:
            self.sheets_client.append_row(row)
            self.existing_urls.add(post['url'])  # Add to dedup set
            self.stats['saved_to_sheets'] += 1
            print(f"✓ Saved: {post['title'][:60]}... (Score: {ai_result.get('score', 'N/A')})")
            return True
        except Exception as e:
            print(f"⚠ Warning: Failed to save post: {e}")
            return False
    
    def run(self):
        """Run the collector"""
        print("\n" + "="*80)
        print("RSS LEAD COLLECTOR - STARTING")
        print("="*80 + "\n")
        
        for feed_url in RSS_FEEDS:
            # Skip commented-out feeds
            if feed_url.strip().startswith('#'):
                continue
            
            print(f"\n📡 Fetching feed: {extract_source_name(feed_url)}")
            
            posts = self.fetch_feed(feed_url)
            self.stats['feeds_processed'] += 1
            self.stats['posts_fetched'] += len(posts)
            
            print(f"   Found {len(posts)} posts")
            
            for post in posts:
                self.process_post(post)
            
            # Rate limit between feeds
            time.sleep(RATE_LIMIT_BETWEEN_FEEDS)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print collection summary statistics"""
        print("\n" + "="*80)
        print("COLLECTION SUMMARY")
        print("="*80)
        print(f"Total feeds processed:      {self.stats['feeds_processed']}")
        print(f"Total posts fetched:        {self.stats['posts_fetched']}")
        print(f"Total duplicates skipped:   {self.stats['duplicates_skipped']}")
        print(f"Total failed keyword filter: {self.stats['failed_keyword_filter']}")
        print(f"Total passed to AI:         {self.stats['passed_to_ai']}")
        print(f"Total saved to Sheets:      {self.stats['saved_to_sheets']}")
        print("="*80 + "\n")

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point"""
    try:
        collector = RSSCollector()
        collector.run()
        print("✓ Collection completed successfully")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
