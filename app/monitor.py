import feedparser
import asyncio
from datetime import datetime
import re
from .dedup import state
from .notifiers.whatsapp import send_whatsapp_alert
from .notifiers.email_notifier import send_email_alert
from .notifiers.sms_notifier import send_sms_alert

RSS_URL = "https://status.aws.amazon.com/rss/all.rss"

# Track current global status for the API
current_status = {}

def classify_status(title: str) -> str:
    title_lower = title.lower()
    if any(word in title_lower for word in ["disruption", "outage", "unavailable"]):
        return "OUTAGE"
    if any(word in title_lower for word in ["degraded", "increased error"]):
        return "DEGRADED"
    if "operating normally" in title_lower:
        return "OPERATIONAL"
    return "UNKNOWN"

def parse_service_region(title: str):
    # Example: "[RESOLVED] Service disruption: Amazon EC2 (N. Virginia)"
    # Regex to find "Service: Region"
    match = re.search(r": (.*) \((.*)\)", title)
    if match:
        return match.group(1), match.group(2)
    return title, "Global"

async def poll_aws_rss():
    global current_status
    print(f"[{datetime.now()}] Polling AWS RSS Feed...")
    
    try:
        feed = feedparser.parse(RSS_URL)
        new_status = {}
        
        for entry in feed.entries:
            service, region = parse_service_region(entry.title)
            status = classify_status(entry.title)
            key = f"{service}_{region}"
            
            new_status[key] = {
                "service": service,
                "region": region,
                "status": status,
                "title": entry.title,
                "description": entry.description,
                "published": entry.published
            }

            if status in ["OUTAGE", "DEGRADED"]:
                if state.should_alert(key):
                    print(f"!!! ALERT DETECTED: {entry.title}")
                    
                    alert_details = {
                        "timestamp": datetime.now().isoformat(),
                        "service": service,
                        "region": region,
                        "status": status,
                        "message": entry.description
                    }
                    
                    # Trigger Notifiers
                    await asyncio.gather(
                        send_whatsapp_alert(service, region, status, entry.description, entry.published),
                        asyncio.to_thread(send_email_alert, service, region, status, entry.description, entry.published),
                        send_sms_alert(service, region, entry.description)
                    )
                    
                    state.mark_alerted(key, alert_details)

        current_status = new_status
        
    except Exception as e:
        print(f"Error during RSS poll: {e}")

async def monitor_loop():
    while True:
        await poll_aws_rss()
        await asyncio.sleep(60) # Poll every 60 seconds
