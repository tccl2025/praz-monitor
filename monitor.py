"""
PRAZ real-time tender monitor.

Checks the Latest Tenders bulletin board for anything new matching your
target categories or target entities, and emails you immediately when it
finds a match. Designed to run on a schedule (every 1-2 hours) via GitHub
Actions — see .github/workflows/monitor.yml — so it works even when your
computer is off.

CREDENTIALS: read from environment variables, never hardcoded. When run
via GitHub Actions, these come from encrypted GitHub Secrets (set once in
GitHub's website, never visible in code or logs).

    ALERT_EMAIL_FROM       - the Gmail address sending alerts
    ALERT_EMAIL_APP_PASSWORD - a Gmail "app password" (not your real password —
                                Gmail generates a separate one for this purpose)
    ALERT_EMAIL_TO         - where alerts should be sent (can be same as FROM)
"""
import os
import csv
import json
import smtplib
from email.mime.text import MIMEText
from pathlib import Path

from bs4 import BeautifulSoup
import requests

import config

SEEN_IDS_FILE = "seen_tender_ids.json"

# --- What counts as a match worth alerting you about ---
TARGET_KEYWORDS = [
    "network", "wifi", "wi-fi", "fibre", "fiber", "lan ", "switch", "router",
    "access point", "starlink", "server", "storage", "data center", "datacenter",
    "firewall", "antivirus", "cctv", "security", "surveillance", "software",
    "licence", "license", "sap", "cloud", "sd wan", "sd-wan", "voip", "pabx", "ict",
]

TARGET_ENTITIES = [
    "GRAIN MARKETING BOARD", "ZIMBABWE REVENUE AUTHOURITY", "AFC HOLDINGS",
    "ZESA HOLDINGS", "PEOPLES OWN SAVINGS BANK", "DEPOSIT PROTECTION CORPORATION",
    "TOBACCO INDUSTRY MARKETING BOARD", "EMPOWERBANK",
    "MUNICIPALITY OF MARONDERA", "HWEDZA RURAL DISTRICT COUNCIL",
    "MUREWA RURAL DISTRICT COUNCIL", "GOROMONZI RURAL DISTRICT COUNCIL",
]


def load_seen_ids():
    path = Path(SEEN_IDS_FILE)
    if path.exists():
        with open(path) as f:
            return set(json.load(f))
    return set()


def save_seen_ids(ids):
    with open(SEEN_IDS_FILE, "w") as f:
        json.dump(list(ids), f)


def fetch_latest_tenders_page1():
    resp = requests.get(config.SECTIONS["latest_tenders"]["first_page_url"],
                         headers={"User-Agent": config.USER_AGENT}, timeout=20)
    resp.raise_for_status()
    return resp.text


def parse_tenders(html):
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table")
    if not table:
        return []
    rows = table.find_all("tr")
    headers = [th.get_text(strip=True) for th in rows[0].find_all(["th", "td"])]
    records = []
    for row in rows[1:]:
        cells = row.find_all("td")
        values = [c.get_text(strip=True) for c in cells]
        if len(values) == len(headers):
            records.append(dict(zip(headers, values)))
    return records


def is_match(tender):
    title = tender.get("Notice Title", "").lower()
    entity = tender.get("Procuring Entity", "").upper()
    keyword_match = any(k in title for k in TARGET_KEYWORDS)
    entity_match = any(e in entity for e in TARGET_ENTITIES)
    return keyword_match or entity_match


def send_alert_email(new_matches):
    from_addr = os.environ["ALERT_EMAIL_FROM"]
    app_password = os.environ["ALERT_EMAIL_APP_PASSWORD"]
    to_addr = os.environ.get("ALERT_EMAIL_TO", from_addr)

    lines = [f"{len(new_matches)} new matching tender(s) found on PRAZ:\n"]
    for t in new_matches:
        lines.append(
            f"- {t.get('Notice Title', '(no title)')}\n"
            f"  Entity: {t.get('Procuring Entity', '?')}\n"
            f"  Closing: {t.get('Bid Closing Date', t.get('Closing Date', '?'))}\n"
            f"  Tender Id: {t.get('Tender Id', '?')}\n"
        )
    body = "\n".join(lines)

    msg = MIMEText(body)
    msg["Subject"] = f"PRAZ Alert: {len(new_matches)} new tender(s) match your targets"
    msg["From"] = from_addr
    msg["To"] = to_addr

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(from_addr, app_password)
        server.sendmail(from_addr, [to_addr], msg.as_string())

    print(f"Alert email sent to {to_addr}")


def main():
    seen_ids = load_seen_ids()
    print(f"Currently tracking {len(seen_ids)} previously-seen tender IDs")

    html = fetch_latest_tenders_page1()
    tenders = parse_tenders(html)
    print(f"Fetched {len(tenders)} tenders from page 1 of Latest Tenders")

    new_matches = []
    all_ids_this_run = set()

    for t in tenders:
        tid = t.get("Tender Id")
        if not tid:
            continue
        all_ids_this_run.add(tid)
        if tid in seen_ids:
            continue  # already seen this one before
        if is_match(t):
            new_matches.append(t)

    if new_matches:
        print(f"Found {len(new_matches)} NEW matching tenders — sending alert")
        send_alert_email(new_matches)
    else:
        print("No new matching tenders this run")

    # Remember everything we saw this run, so we don't re-alert on it next time
    save_seen_ids(seen_ids | all_ids_this_run)


if __name__ == "__main__":
    main()
