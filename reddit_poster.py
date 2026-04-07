#!/usr/bin/env python3
"""
Reddit Post Scheduler
Reads pending posts from Google Sheets PostQueue tab and publishes them to Reddit
"""

import os
import sys
import json
import time
from datetime import datetime
import praw
import gspread
from google.oauth2.service_account import Credentials

# ============================================================================
# CONFIGURATION
# ============================================================================

SHEET_TAB_NAME = "PostQueue"
SHEET_COLUMNS = ["scheduled_time", "subreddit", "title", "body", "status"]

# Column indices (0-based)
COL_SCHEDULED_TIME = 0
COL_SUBREDDIT = 1
COL_TITLE = 2
COL_BODY = 3
COL_STATUS = 4

# ============================================================================
# GOOGLE SHEETS CLIENT
# ============================================================================

class GoogleSheetsClient:

    def __init__(self, credentials_json: str, sheet_id: str):
        creds_dict = json.loads(credentials_json)
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        self.client = gspread.authorize(credentials)
        spreadsheet = self.client.open_by_key(sheet_id)

        # Get or create PostQueue tab
        try:
            self.sheet = spreadsheet.worksheet(SHEET_TAB_NAME)
            print(f"✓ Connected to tab: {SHEET_TAB_NAME}")
        except gspread.WorksheetNotFound:
            self.sheet = spreadsheet.add_worksheet(title=SHEET_TAB_NAME, rows=1000, cols=5)
            self.sheet.update('A1:E1', [SHEET_COLUMNS])
            print(f"✓ Created tab: {SHEET_TAB_NAME}")

    def get_pending_posts(self):
        """Get all posts that are due and have status 'pending'"""
        all_rows = self.sheet.get_all_values()
        if len(all_rows) <= 1:
            return []

        now = datetime.utcnow()
        pending = []

        for i, row in enumerate(all_rows[1:], start=2):  # start=2 because row 1 is header
            if len(row) < 5:
                continue

            status = row[COL_STATUS].strip().lower()
            if status != "pending":
                continue

            scheduled_str = row[COL_SCHEDULED_TIME].strip()
            try:
                scheduled_time = datetime.strptime(scheduled_str, "%Y-%m-%d %H:%M")
            except ValueError:
                print(f"⚠ Invalid date format in row {i}: {scheduled_str}")
                continue

            if scheduled_time <= now:
                pending.append({
                    "row_index": i,
                    "scheduled_time": scheduled_time,
                    "subreddit": row[COL_SUBREDDIT].strip().lstrip("r/"),
                    "title": row[COL_TITLE].strip(),
                    "body": row[COL_BODY].strip().replace("|", "\n"),
                    "status": status
                })

        return pending

    def update_status(self, row_index: int, status: str):
        """Update the status cell for a given row"""
        self.sheet.update_cell(row_index, COL_STATUS + 1, status)  # gspread is 1-based


# ============================================================================
# REDDIT POSTER
# ============================================================================

class RedditPoster:

    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            username=os.getenv("REDDIT_USERNAME"),
            password=os.getenv("REDDIT_PASSWORD"),
            user_agent=f"relay-poster:v1.0 (by u/{os.getenv('REDDIT_USERNAME')})"
        )
        print(f"✓ Reddit logged in as: {self.reddit.user.me()}")

    def post(self, subreddit: str, title: str, body: str) -> str:
        """Submit a text post and return the URL"""
        sub = self.reddit.subreddit(subreddit)
        submission = sub.submit(title=title, selftext=body)
        return f"https://reddit.com{submission.permalink}"


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("\n" + "="*60)
    print("REDDIT POSTER - STARTING")
    print("="*60 + "\n")

    # Validate env vars
    required = ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USERNAME",
                "REDDIT_PASSWORD", "GOOGLE_SHEETS_ID", "GOOGLE_CREDENTIALS_JSON"]
    for var in required:
        if not os.getenv(var):
            print(f"✗ Missing env var: {var}")
            sys.exit(1)

    sheets = GoogleSheetsClient(os.getenv("GOOGLE_CREDENTIALS_JSON"), os.getenv("GOOGLE_SHEETS_ID"))
    poster = RedditPoster()

    pending = sheets.get_pending_posts()
    print(f"Found {len(pending)} post(s) due for publishing\n")

    for post in pending:
        print(f"→ Posting to r/{post['subreddit']}: {post['title'][:60]}...")
        try:
            url = poster.post(post["subreddit"], post["title"], post["body"])
            sheets.update_status(post["row_index"], "posted")
            print(f"✓ Posted: {url}")
        except Exception as e:
            sheets.update_status(post["row_index"], "failed")
            print(f"✗ Failed: {e}")

        time.sleep(2)  # small delay between posts

    print("\n✓ Done")

if __name__ == "__main__":
    main()