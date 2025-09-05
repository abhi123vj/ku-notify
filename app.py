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

        # Check if it's a new batch with different publish date
        if old_date != new_date:
            print(
                f"🗑️ New batch detected! Clearing old data (was: {old_date}, now: {new_date})"
            )
            # Clear MongoDB and treat all matching notifications as new
            replace_latest_in_mongo(latest_rows)
            new_matches = [
                n
                for n in latest_rows
                if NOTIFY_YEAR in n["exam_name"]
                and any(
                    keyword.lower() in n["exam_name"].lower()
                    for keyword in NOTIFY_KEYWORDS
                )
            ]
        else:
            # Same date but different notifications - find only NEW ones
            new_matches = []
            for n in latest_rows:
                # Check if this notification is new (not in old_rows)
                is_new = not any(
                    old_n["exam_name"] == n["exam_name"]
                    and old_n["published_date"] == n["published_date"]
                    for old_n in old_rows
                )

                # Check if it matches our criteria AND is new
                if (
                    is_new
                    and NOTIFY_YEAR in n["exam_name"]
                    and any(
                        keyword.lower() in n["exam_name"].lower()
                        for keyword in NOTIFY_KEYWORDS
                    )
                ):
                    new_matches.append(n)

            # Update MongoDB with latest data (includes new + existing)
            replace_latest_in_mongo(latest_rows)

    else:
        # No old data exists, so all matching notifications are "new"
        print("📊 First run - storing initial data")
        replace_latest_in_mongo(latest_rows)
        new_matches = [
            n
            for n in latest_rows
            if NOTIFY_YEAR in n["exam_name"]
            and any(
                keyword.lower() in n["exam_name"].lower() for keyword in NOTIFY_KEYWORDS
            )
        ]

    # Send email only if there are NEW matching notifications
    if new_matches:
        subject = "Kerala University - New Examination Notifications Available"

        # Professional HTML email template
        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px; background-color: #f4f4f4; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #1e3a8a, #3b82f6); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .header h1 {{ margin: 0; font-size: 24px; font-weight: 600; }}
                .header p {{ margin: 10px 0 0 0; opacity: 0.9; }}
                .content {{ padding: 30px; }}
                .notification-count {{ background: #eff6ff; border: 1px solid #dbeafe; border-radius: 6px; padding: 15px; margin-bottom: 25px; }}
                .notification-count strong {{ color: #1e40af; }}
                .notification-item {{ background: #f8fafc; border-left: 4px solid #3b82f6; margin: 15px 0; padding: 20px; border-radius: 0 6px 6px 0; }}
                .notification-title {{ font-weight: 600; color: #1e40af; margin-bottom: 8px; font-size: 16px; }}
                .notification-date {{ color: #64748b; font-size: 14px; margin-bottom: 12px; }}
                .pdf-link {{ display: inline-block; background: #3b82f6; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; font-size: 14px; margin-top: 8px; }}
                .pdf-link:hover {{ background: #2563eb; }}
                .footer {{ background: #f8fafc; padding: 20px; text-align: center; border-radius: 0 0 8px 8px; border-top: 1px solid #e2e8f0; }}
                .footer p {{ margin: 0; color: #64748b; font-size: 14px; }}
                .disclaimer {{ background: #fef3cd; border: 1px solid #fde68a; border-radius: 6px; padding: 15px; margin-top: 20px; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Kerala University</h1>
                    <p>Examination Notification Alert</p>
                </div>
                
                <div class="content">
                    <div class="notification-count">
                        <strong>{len(new_matches)} New Notification{"s" if len(new_matches) > 1 else ""} Available</strong>
                    </div>
                    
                    <p>Dear Student,</p>
                    <p>We're pleased to inform you that new examination notifications matching your criteria have been published on the Kerala University portal.</p>
        """

        # Add each notification
        for m in new_matches:
            body += f"""
                    <div class="notification-item">
                        <div class="notification-title">{m["exam_name"]}</div>
                        <div class="notification-date">📅 Published: {m["published_date"]}</div>
                        <a href="{m["pdf_link"]}" class="pdf-link">📄 View PDF Document</a>
                    </div>
            """

        body += f"""
                    <div class="disclaimer">
                        <strong>📌 Important:</strong> Please verify all details from the official Kerala University website. This is an automated notification system.
                    </div>
                    
                    <p style="margin-top: 25px;">
                        <strong>Next Steps:</strong><br>
                        • Review the notification documents carefully<br>
                        • Note important dates and deadlines<br>
                        • Contact the university for any clarifications
                    </p>
                </div>
                
                <div class="footer">
                    <p>This is an automated notification from KU Notify System</p>
                    <p>Kerala University Official Portal: <a href="https://exams.keralauniversity.ac.in/" style="color: #3b82f6;">exams.keralauniversity.ac.in</a></p>
                </div>
            </div>
        </body>
        </html>
        """

        send_email(subject, body)
        print(
            f"✅ Notification email sent for {len(new_matches)} new matching notification(s)."
        )
    else:
        print("ℹ️ No new matching notifications to send email for.")


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
