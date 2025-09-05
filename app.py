import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pymongo import MongoClient
import resend
import os

from dotenv import load_dotenv

load_dotenv()
# ---------------- CONFIG ---------------- #
BASE_URL = os.getenv("BASE_URL", "https://exams.keralauniversity.ac.in/Login/check1")
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "KuNotify"
COLLECTION_NAME = "KuNotifications"
NOTIFY_KEYWORDS = os.getenv(
    "NOTIFY_KEYWORDS", "btech,b.tech,bachelor of technology"
).split(",")
NOTIFY_YEAR = os.getenv("NOTIFY_YEAR", "2018")

# Resend setup (store API key as env var)
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO = os.getenv("EMAIL_TO")

resend.api_key = RESEND_API_KEY
# ---------------------------------------- #


def fetch_latest_published(url):
    """Fetch the latest published batch of notifications from KU website."""
    print(f"🔎 Fetching from {url}")
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    heading = soup.find("tr", class_="tableHeading")
    if not heading:
        return []

    published_date = heading.get_text(strip=True).replace("Published on ", "")

    rows = []
    for tr in heading.find_next_siblings("tr"):
        if "tableHeading" in tr.get("class", []):
            break
        if "displayList" not in tr.get("class", []):
            continue

        cols = tr.find_all("td")
        if len(cols) < 2:
            continue

        exam_name = cols[1].get_text(" ", strip=True)

        link_tag = cols[2].find("a") if len(cols) >= 3 else None
        pdf_link = urljoin(BASE_URL, link_tag["href"]) if link_tag else ""

        rows.append(
            {
                "published_date": published_date,
                "exam_name": exam_name,
                "pdf_link": pdf_link,
            }
        )

    return rows


def get_stored_latest():
    """Return the currently stored latest batch from MongoDB."""
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    return list(collection.find())


def replace_latest_in_mongo(notifications):
    """Replace MongoDB collection with the latest batch only."""
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    collection.delete_many({})
    if notifications:
        collection.insert_many(notifications)
        print(f"✅ Stored {len(notifications)} latest notifications.")
    else:
        print("⚠️ No notifications to insert.")


def send_email(subject, body):
    """Send email via Resend API."""
    try:
        resend.Emails.send(
            {"from": EMAIL_FROM, "to": EMAIL_TO, "subject": subject, "html": body}
        )
        print("📧 Email notification sent successfully!")
    except Exception as e:
        print(f"❌ Email send failed: {e}")


def check_for_new_and_notify(latest_rows):
    """Compare with DB, update, and send alert if new batch or new rows detected."""
    old_rows = get_stored_latest()

    if old_rows:
        old_date = old_rows[0]["published_date"]
        new_date = latest_rows[0]["published_date"]

        old_names = {r["exam_name"] for r in old_rows}
        new_names = {r["exam_name"] for r in latest_rows}

        # Check both date and names
        if old_date == new_date and old_names == new_names:
            print("ℹ️ No new notifications (already stored).")
            return

    # New batch OR new rows detected → update MongoDB
    replace_latest_in_mongo(latest_rows)

    # Filter matching notifications
    matches = [
        n
        for n in latest_rows
        if NOTIFY_YEAR in n["exam_name"]
        and any(
            keyword.lower() in n["exam_name"].lower() for keyword in NOTIFY_KEYWORDS
        )
    ]

    if matches:
        subject = "🚨 New B.Tech 2018 Scheme Notification!"
        body = "<h3>Latest Notifications:</h3><ul>"
        for m in matches:
            body += f"<li>{m['published_date']} - {m['exam_name']}<br><a href='{m['pdf_link']}'>PDF Link</a></li>"
        body += "</ul>"

        send_email(subject, body)
    else:
        print("ℹ️ No B.Tech 2018 Scheme notifications in latest batch.")


if __name__ == "__main__":
    url = BASE_URL
    latest_rows = fetch_latest_published(url)

    if latest_rows:
        check_for_new_and_notify(latest_rows)

        # # Optional backup to CSV
        # df = pd.DataFrame(latest_rows)
        # df.to_csv("latest_published_notifications.csv", index=False)
    else:
        print("⚠️ No notifications found")
