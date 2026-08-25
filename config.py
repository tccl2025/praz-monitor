"""
Configuration for the full PRAZ bulletin board scraper.

NO LOGIN REQUIRED. Every URL here is a public page — confirmed by direct
testing. This scrapes all four Bulletin Board sections:
    1. Latest Tenders     (currently open)
    2. Former Opportunities (historical archive — the big one)
    3. Award Notices       (who won what)
    4. Annual Procurement Plan (forecasted future tenders, per entity)

SCALE WARNING
-------------
Former Opportunities alone is ~63,790 records across ~3,190 pages
(confirmed live on 24-Aug-2026 — check the "last page" number again
when you run this, it grows over time). At a polite 1.5s delay between
pages, that section alone takes roughly 80 minutes. Budget 2+ hours
for a full run across all sections. This is normal — let it run in
the background, it checkpoints as it goes so you can stop and resume.
"""

import os

BASE = "https://egp.praz.org.zw"

SECTIONS = {
    "latest_tenders": {
        "url_template": BASE + "/index?url=Indexes%2Findex&page={page}&direction=BulletinBoardLive.id",
        "first_page_url": BASE + "/Indexes/index",
        "output_csv": "praz_latest_tenders.csv",
        "state_file": "state_latest_tenders.json",
    },
    "former_opportunities": {
        "url_template": BASE + "/indexes/get-former-opportunities?url=Indexes%2FgetFormerOpportunities&page={page}&direction=BulletinBoardConcluded.id",
        "first_page_url": BASE + "/Indexes/getFormerOpportunities",
        "output_csv": "praz_former_opportunities.csv",
        "state_file": "state_former_opportunities.json",
    },
    "award_notices": {
        # Confirmed 24-Aug-2026: entry point is the "View More" link
        # (viewMoreAward), which has real numbered pagination once loaded.
        "url_template": BASE + "/indexes/view-more-award?url=Indexes%2FviewMoreAward&page={page}&direction=Awards.id+desc",
        "first_page_url": BASE + "/Indexes/viewMoreAward",
        "output_csv": "praz_award_notices.csv",
        "state_file": "state_award_notices.json",
    },
    "annual_procurement_plan": {
        # Confirmed 24-Aug-2026: getApp has standard numbered pagination.
        "url_template": BASE + "/indexes/get-app?url=Indexes%2FgetApp&page={page}",
        "first_page_url": BASE + "/Indexes/getApp",
        "output_csv": "praz_app.csv",
        "state_file": "state_app.json",
    },
}

# --- Politeness settings ---
# This is public data with no rate limit stated, but it's still a
# government server. Be a good citizen — there is no reason to hammer it.
REQUEST_DELAY_SECONDS = 1.5
REQUEST_TIMEOUT_SECONDS = 20
MAX_RETRIES_PER_PAGE = 3
RETRY_BACKOFF_SECONDS = 5

USER_AGENT = "Mozilla/5.0 (compatible; WinguResearchBot/1.0; contact: you@wingu.network)"
