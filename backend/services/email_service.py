import os, smtplib, csv, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fastapi import HTTPException

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.office365.com")
SMTP_PORT   = int(os.getenv("SMTP_PORT", "587"))
EMAIL_USER  = os.getenv("EMAIL_USER")
EMAIL_PASS  = os.getenv("EMAIL_PASS")
EMAIL_TO    = os.getenv("EMAIL_TO", "")  # CSV list
LOG_PATH    = os.getenv(
    "EMAIL_LOG_PATH",
    os.path.join(os.path.dirname(__file__), "..", "email_log.csv")
)

def _log(msg: str):
    """Lightweight timestamped log for email ops."""
    print(f"[{datetime.datetime.now().isoformat()}] [Email] {msg}")

def _recipients() -> list[str]:
    return [e.strip() for e in EMAIL_TO.split(",") if e.strip()]

def send_directors_export_link(sharepoint_url: str, filename_display: str):
    recips = _recipients()
    if not (EMAIL_USER and EMAIL_PASS and recips):
        _log("Missing email configuration or recipients.")
        raise HTTPException(status_code=502, detail="Email configuration invalid or recipients missing.")

    today_display_date = datetime.datetime.now().strftime("%-m.%-d.%y") if os.name != "nt" else datetime.datetime.now().strftime("%#m.%#d.%y")
    subject = f"Bi-Weekly Ticket Report [{today_display_date}]"
    body = f"""Hey Team,

The latest Zendesk ticket report is ready as of {today_display_date}:
{sharepoint_url or '[SharePoint link not available]'}

Please review older tickets prior to the bi-weekly meeting. Leave notations if further follow-up is required.

Thanks,
Olivier
"""

    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"]   = ", ".join(recips)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    ok = False
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as s:
            s.starttls()
            s.login(EMAIL_USER, EMAIL_PASS)
            s.sendmail(EMAIL_USER, recips, msg.as_string())
        ok = True
        _log(f"Email sent successfully to {recips}")
    except Exception as e:
        _log(f"Email send failed: {e}")
        raise HTTPException(status_code=502, detail=f"Email delivery failed: {e}")

    # Always attempt to log the outcome
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                subject,
                "; ".join(recips),
                "Success" if ok else "Failed",
                sharepoint_url or "N/A"
            ])
    except Exception as e:
        _log(f"Failed to write email log: {e}")
