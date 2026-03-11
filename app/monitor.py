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

def parse_service_region(entry):
    title = entry.title
    # Example: "[RESOLVED] Service disruption: Amazon EC2 (N. Virginia)"
    # Regex to find "Service: Region"
    match = re.search(r": (.*) \((.*)\)", title)
    if match:
        return match.group(1), match.group(2)
    
    # Try extracting from GUID (common for multiple services)
    # guid: https://status.aws.amazon.com/#multipleservices-me-south-1_1772556000
    guid = getattr(entry, 'guid', '')
    if '#' in guid:
        fragment = guid.split('#')[-1]
        if '-' in fragment:
            # multipleservices-me-south-1_1772556000 -> me-south-1
            # Split by _ first to get the part before timestamp
            part_before_ts = fragment.split('_')[0]
            # Find the first hyphen which is after 'multipleservices' or service name
            if '-' in part_before_ts:
                region = '-'.join(part_before_ts.split('-')[1:])
                if region:
                    service = title.split(':')[0] if ':' in title else "Multiple Services"
                    return service, region.upper()

    return title, "Global"

async def poll_aws_rss():
    global current_status
    print(f"[{datetime.now()}] Polling AWS RSS Feed...")
    
    try:
        feed = feedparser.parse(RSS_URL)
        new_status = {}
        
        for entry in feed.entries:
            service, region = parse_service_region(entry)
            status = classify_status(entry.title)
            key = f"{service}_{region}_{entry.title}" # More unique key
            
            new_status[key] = {
                "service": service,
                "region": region,
                "status": status,
                "title": entry.title,
                "description": entry.description,
                "published": entry.published,
                "guid": getattr(entry, 'guid', '')
            }

            if status in ["OUTAGE", "DEGRADED"]:
                if state.should_alert(key):
                    print(f"!!! ALERT DETECTED: {entry.title}")
                    
                    alert_details = {
                        "timestamp": datetime.now().isoformat(),
                        "service": service,
                        "region": region,
                        "status": status,
                        "message": entry.description,
                        "published": entry.published
                    }
                    
                    # Trigger Notifiers
                    # Ensure they are awaited or scheduled
                    asyncio.create_task(send_whatsapp_alert(service, region, status, entry.description, entry.published))
                    # send_email_alert is sync, use to_thread
                    asyncio.create_task(asyncio.to_thread(send_email_alert, service, region, status, entry.description, entry.published))
                    asyncio.create_task(send_sms_alert(service, region, entry.description))
                    
                    state.mark_alerted(key, alert_details)

        current_status = new_status
        
    except Exception as e:
        print(f"Error during RSS poll: {e}")

async def monitor_loop():
    while True:
        await poll_aws_rss()
        await asyncio.sleep(60) # Poll every 60 seconds
