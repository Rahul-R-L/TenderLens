
#!/usr/bin/env python3
"""
TenderLens Personal Tender Alert

Usage:
    python tender_alert.py
    python tender_alert.py --all
    python tender_alert.py --reset
"""

import argparse
import os
import re
import sqlite3
from collections import defaultdict
from datetime import datetime

from auth import resend, APP_NAME

DATABASE = "tenders.db"
HISTORY_DB = "alert_history.db"

EMAIL_TO = [
    os.getenv("TENDER_ALERT_EMAIL", "rahulrl191@gmail.com")
]

RULES = [
    {
        "name": "CC >100",
        "all_words": ["cement", "concrete"],
        "aliases": ["pcc", "rcc", "cc"],
        "exclude": [],
        "min_qty": 100
    },
    {
        "name": "GSB >500",
        "all_words": ["granular", "sub", "base"],
        "aliases": ["gsb"],
        "exclude": [],
        "min_qty": 500
    }
]


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def rule_match(rule, description, qty):
    if qty is None or qty < rule["min_qty"]:
        return False

    text = normalize(description)

    for ex in rule.get("exclude", []):
        if ex in text:
            return False

    if any(alias in text for alias in rule.get("aliases", [])):
        return True

    return all(word in text for word in rule.get("all_words", []))


def init_history():
    conn = sqlite3.connect(HISTORY_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alerts(
            tender_id TEXT,
            rule_name TEXT,
            alerted_at TEXT,
            PRIMARY KEY(tender_id, rule_name)
        )
    """)
    conn.commit()
    return conn


def already_sent(hist_conn, tender_id, rule):
    cur = hist_conn.execute(
        "SELECT 1 FROM alerts WHERE tender_id=? AND rule_name=?",
        (tender_id, rule)
    )
    return cur.fetchone() is not None


def mark_sent(hist_conn, tender_id, rule):
    hist_conn.execute(
        "INSERT OR IGNORE INTO alerts VALUES(?,?,?)",
        (tender_id, rule, datetime.now().isoformat())
    )
    hist_conn.commit()


def fetch_matches():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    sql = """
    SELECT
        t.tender_id,
        t.bid_end_iso,
        b.description,
        b.quantity
    FROM boq_items b
    JOIN tenders t
      ON t.tender_id=b.tender_id
    WHERE datetime(t.bid_end_iso) > datetime('now')
      AND b.quantity >= ?
    ORDER BY t.tender_id
    """

    min_qty = min(r["min_qty"] for r in RULES)

    rows = conn.execute(sql, (min_qty,)).fetchall()
    conn.close()

    grouped = defaultdict(set)

    for row in rows:
        for rule in RULES:
            if rule_match(rule, row["description"], row["quantity"]):
                grouped[row["tender_id"]].add(rule["name"])

    return grouped


def send_email(matches):
    total = len(matches)

    subject = f"TenderLens Alert | {total} New Matches"

    html = f"<h3>{total} new matching tenders found.</h3><hr>"

    counts = defaultdict(int)

    for tid in sorted(matches):
        html += f"<b>{tid}</b><br>"
        for r in sorted(matches[tid]):
            html += f"&#10004; {r}<br>"
            counts[r] += 1
        html += "<br><hr>"

    html += "<h4>Summary</h4>"
    for r, c in counts.items():
        html += f"{r}: {c}<br>"

    resend.Emails.send({
        "from": f"{APP_NAME} <noreply@tenderlens.in>",
        "to": EMAIL_TO,
        "subject": subject,
        "html": html
    })


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    hist = init_history()

    if args.reset:
        hist.execute("DELETE FROM alerts")
        hist.commit()
        print("Alert history cleared.")
        return

    matches = fetch_matches()

    if not args.all:
        filtered = defaultdict(set)
        for tid, rules in matches.items():
            for rule in rules:
                if not already_sent(hist, tid, rule):
                    filtered[tid].add(rule)
        matches = filtered

    if not matches:
        print("No new matching tenders.")
        return

    send_email(matches)

    if not args.all:
        for tid, rules in matches.items():
            for rule in rules:
                mark_sent(hist, tid, rule)

    print(f"Sent alert for {len(matches)} tender(s).")


if __name__ == "__main__":
    main()
