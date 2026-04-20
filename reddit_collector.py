#!/usr/bin/env python3
import os
import sys
import json
import time
import re
import random
from datetime import datetime
from typing import List, Dict, Set, Optional
import feedparser
import requests
import gspread
from google.oauth2.service_account import Credentials
from anthropic import Anthropic
from bs4 import BeautifulSoup

RSS_FEEDS = [
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
    "https://www.google.com/alerts/feeds/10605284653761947770/17547666453224584072",
    "https://www.google.com/alerts/feeds/10605284653761947770/11799962196978559227",
    "https://www.google.com/alerts/feeds/10605284653761947770/11205966101093525896",
    "https://www.google.com/alerts/feeds/10605284653761947770/2957016071162074905",
    "https://www.google.com/alerts/feeds/10605284653761947770/3088012883186134098",
    "https://www.google.com/alerts/feeds/10605284653761947770/8706557038309823380",
    "https://www.google.com/alerts/feeds/10605284653761947770/16545658599802679305",
    "https://www.google.com/alerts/feeds/10605284653761947770/6875575467182349121",
    "https://www.google.com/alerts/feeds/10605284653761947770/10698494035640013000",
    "https://www.google.com/alerts/feeds/10605284653761947770/5283008468998240233",
    "https://www.google.com/alerts/feeds/10605284653761947770/2944949419624491757",
    "https://www.google.com/alerts/feeds/10605284653761947770/10638649173406501531",
    "https://www.google.com/alerts/feeds/10605284653761947770/637427977252961531",
    "https://www.google.com/alerts/feeds/10605284653761947770/9947997926182776142",
    "https://www.google.com/alerts/feeds/10605284653761947770/16104753547817923697",
    "https://www.google.com/alerts/feeds/10605284653761947770/4834273587035497087",
    "https://www.google.com/alerts/feeds/10605284653761947770/9947997926182774748",
    "https://www.google.com/alerts/feeds/10605284653761947770/13365351787220754925",
    "https://www.google.com/alerts/feeds/10605284653761947770/1239498199882998243",
    "https://www.google.com/alerts/feeds/10605284653761947770/8699520351222471960",
]

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

RATE_LIMIT_BETWEEN_POSTS = 0.5
RATE_LIMIT_BETWEEN_FEEDS = 1.0
MAX_CONTENT_FOR_SHEETS = 500
MAX_CONTENT_FOR_AI = 600
SHEET_COLUMNS = ["Date", "Source", "Title", "URL", "Content", "Author", "Score", "Problem_Type", "Buyer_Intent", "Reply", "Status"]
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


def clean_html(text):
    if not text:
        return ""
    soup = BeautifulSoup(text, 'html.parser')
    text = soup.get_text()
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def truncate_text(text, max_length):
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def contains_positive_keyword(text):
    text_lower = text.lower()
    return any(k.lower() in text_lower for k in POSITIVE_KEYWORDS)


def contains_negative_keyword(text):
    text_lower = text.lower()
    return any(k.lower() in text_lower for k in NEGATIVE_KEYWORDS)


def extract_source_name(feed_url):
    if "reddit.com" in feed_url:
        match = re.search(r'/r/([^/]+)/', feed_url)
        if match:
            subreddit = match.group(1)
            if "search.rss" in feed_url:
                q = re.search(r'q=([^&]+)', feed_url)
                if q:
                    return f"Reddit: r/{subreddit} (search: {q.group(1)})"
            return f"Reddit: r/{subreddit}"
    elif "google.com/alerts" in feed_url:
        return "Google Alerts (LinkedIn)"
    return feed_url


class GoogleSheetsClient:

    def __init__(self, credentials_json, sheet_id):
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

    def get_existing_urls(self):
        try:
            all_values = self.sheet.get_all_values()
            if len(all_values) <= 1:
                return set()
            urls = set()
            for row in all_values[1:]:
                if len(row) > 3 and row[3]:
                    urls.add(row[3])
            print(f"✓ Loaded {len(urls)} existing URLs from sheet")
            return urls
        except Exception as e:
            print(f"⚠ Warning: Could not load existing URLs: {e}")
            return set()

    def ensure_headers(self):
        try:
            first_row = self.sheet.row_values(1)
            if not first_row or first_row != SHEET_COLUMNS:
                self.sheet.update('A1:K1', [SHEET_COLUMNS])
                print("✓ Sheet headers initialized")
        except Exception as e:
            print(f"⚠ Warning: Could not set headers: {e}")

    def append_row(self, row_data):
        try:
            self.sheet.append_row(row_data)
        except Exception as e:
            print(f"⚠ Warning: Failed to append row: {e}")
            raise


class AIScorer:

    def __init__(self, api_key):
        self.client = Anthropic(api_key=api_key)
        print("✓ Claude AI client initialized")

    def score_post(self, title, content, source):
        try:
            prompt = AI_PROMPT_TEMPLATE.format(
                title=title,
                content=truncate_text(content, MAX_CONTENT_FOR_AI),
                source=source
            )
            message = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}]
            )
            response_text = message.content[0].text.strip()
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)
            result = json.loads(response_text)
            required_fields = ["score", "problem_type", "buyer_intent", "reason"]
            if not all(f in result for f in required_fields):
                return None
            return result
        except Exception as e:
            print(f"⚠ Warning: AI scoring failed: {e}")
            return None


class RSSCollector:

    def __init__(self):
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.google_sheets_id = os.getenv('GOOGLE_SHEETS_ID')
        self.google_credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON')

        if not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        if not self.google_sheets_id:
            raise ValueError("GOOGLE_SHEETS_ID not set")
        if not self.google_credentials_json:
            raise ValueError("GOOGLE_CREDENTIALS_JSON not set")

        self.sheets_client = GoogleSheetsClient(self.google_credentials_json, self.google_sheets_id)
        self.sheets_client.ensure_headers()
        self.ai_scorer = AIScorer(self.anthropic_api_key)
        self.existing_urls = self.sheets_client.get_existing_urls()
        self.stats = {
            'feeds_processed': 0,
            'posts_fetched': 0,
            'duplicates_skipped': 0,
            'failed_keyword_filter': 0,
            'passed_to_ai': 0,
            'saved_to_sheets': 0
        }

    def fetch_feed(self, feed_url):
        try:
            headers = {
                "User-Agent": random.choice(USER_AGENTS),
                "Accept": "application/rss+xml, application/xml, text/xml, */*",
            }
            if "reddit.com" in feed_url:
                response = requests.get(feed_url, headers=headers, timeout=15)
                if response.status_code != 200:
                    print(f"⚠ Warning: HTTP {response.status_code} for {feed_url}")
                    return []
                feed = feedparser.parse(response.text)
            else:
                feed = feedparser.parse(feed_url, request_headers=headers)

            if feed.bozo and not feed.entries:
                print(f"⚠ Warning: Feed error for {feed_url}: {feed.bozo_exception}")
                return []

            posts = []
            for entry in feed.entries:
                post = {
                    'title': entry.get('title', ''),
                    'url': entry.get('link', ''),
                    'content': entry.get('summary', '') or entry.get('content', [{}])[0].get('value', ''),
                    'author': entry.get('author', ''),
                    'source': extract_source_name(feed_url)
                }
                posts.append(post)
            return posts

        except Exception as e:
            print(f"⚠ Warning: Failed to fetch feed {feed_url}: {e}")
            return []

    def process_post(self, post):
        if post['url'] in self.existing_urls:
            self.stats['duplicates_skipped'] += 1
            return False

        clean_content = clean_html(post['content'])
        combined_text = f"{post['title']} {clean_content}"

        if contains_negative_keyword(combined_text):
            self.stats['failed_keyword_filter'] += 1
            return False

        if not contains_positive_keyword(combined_text):
            self.stats['failed_keyword_filter'] += 1
            return False

        time.sleep(RATE_LIMIT_BETWEEN_POSTS)
        self.stats['passed_to_ai'] += 1

        ai_result = self.ai_scorer.score_post(post['title'], clean_content, post['source'])
        if not ai_result:
            ai_result = {'score': '', 'problem_type': '', 'buyer_intent': '', 'reason': ''}

        row = [
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            post['source'],
            post['title'],
            post['url'],
            truncate_text(clean_content, MAX_CONTENT_FOR_SHEETS),
            post['author'],
            str(ai_result.get('score', '')),
            ai_result.get('problem_type', ''),
            ai_result.get('buyer_intent', ''),
            '',
            ''
        ]

        try:
            self.sheets_client.append_row(row)
            self.existing_urls.add(post['url'])
            self.stats['saved_to_sheets'] += 1
            print(f"✓ Saved: {post['title'][:60]}... (Score: {ai_result.get('score', 'N/A')})")
            return True
        except Exception as e:
            print(f"⚠ Warning: Failed to save post: {e}")
            return False

    def run(self):
        print("\n" + "="*80)
        print("RSS LEAD COLLECTOR - STARTING")
        print("="*80 + "\n")

        for feed_url in RSS_FEEDS:
            print(f"\n📡 Fetching feed: {extract_source_name(feed_url)}")
            posts = self.fetch_feed(feed_url)
            self.stats['feeds_processed'] += 1
            self.stats['posts_fetched'] += len(posts)
            print(f"   Found {len(posts)} posts")

            for post in posts:
                self.process_post(post)

            time.sleep(RATE_LIMIT_BETWEEN_FEEDS)

        self.print_summary()

    def print_summary(self):
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


def main():
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
