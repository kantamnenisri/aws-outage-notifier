import http.server
import socketserver
import json
import os
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import threading
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

PORT = 8000
RSS_URL = "https://status.aws.amazon.com/rss/all.rss"

# State Management
class GlobalState:
    def __init__(self):
        self.last_alerted = {}
        self.history = []
        self.silenced_until = datetime.min
        self.current_status = {}

state = GlobalState()

# --- Notifiers (Standard Lib) ---

def send_whatsapp(service, region, status, description, timestamp):
    phone = os.environ.get("CALLMEBOT_PHONE")
    apikey = os.environ.get("CALLMEBOT_APIKEY")
    if not (phone and apikey): return
    msg = f"🔴 AWS ALERT\nSvc: {service}\nReg: {region}\nStat: {status}\nMsg: {description[:50]}...\nTime: {timestamp}"
    url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&apikey={apikey}&text={urllib.parse.quote(msg)}"
    try: urllib.request.urlopen(url, timeout=10)
    except Exception as e: print(f"WhatsApp Error: {e}")

def send_email(service, region, status, description, timestamp):
    to_email = os.environ.get("ALERT_EMAIL_TO")
    from_email = os.environ.get("ALERT_EMAIL_FROM")
    password = os.environ.get("GMAIL_APP_PASSWORD")
    if not all([to_email, from_email, password]): return
    
    msg = MIMEMultipart()
    msg['Subject'] = f"🔴 AWS OUTAGE: {service} ({region})"
    body = f"Status: {status}\nTime: {timestamp}\n\nDescription: {description}"
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(from_email, password)
            server.send_message(msg)
    except Exception as e: print(f"Email Error: {e}")

def send_sms(service, region, description):
    phone = os.environ.get("SMS_PHONE")
    if os.environ.get("ENABLE_SMS", "false").lower() != "true" or not phone: return
    msg = f"AWS OUTAGE: {service} {region} - {description[:50]}"
    data = json.dumps({"phone": phone, "message": msg, "key": "textbelt"}).encode()
    req = urllib.request.Request("https://textbelt.com/text", data=data, headers={'Content-Type': 'application/json'})
    try: urllib.request.urlopen(req, timeout=10)
    except Exception as e: print(f"SMS Error: {e}")

# --- Monitor Logic ---

def poll_rss():
    print(f"[{datetime.now()}] Polling AWS RSS...")
    try:
        with urllib.request.urlopen(RSS_URL, timeout=15) as response:
            root = ET.fromstring(response.read())
            for item in root.findall('.//item'):
                title = item.find('title').text
                desc = item.find('description').text
                pub_date = item.find('pubDate').text
                
                # Classify
                status = "OPERATIONAL"
                if any(x in title.lower() for x in ["disruption", "outage", "unavailable"]): status = "OUTAGE"
                elif any(x in title.lower() for x in ["degraded", "increased error"]): status = "DEGRADED"
                
                if status != "OPERATIONAL":
                    key = title[:50] # Simplified key
                    now = datetime.now()
                    if now > state.silenced_until and (key not in state.last_alerted or (now - state.last_alerted[key]) > timedelta(minutes=60)):
                        print(f"!!! TRIGGERING ALERTS FOR: {title}")
                        state.last_alerted[key] = now
                        state.history.insert(0, {"time": now.isoformat(), "title": title})
                        # Fire and forget threads for notifications
                        threading.Thread(target=send_whatsapp, args=("AWS", "Region", status, desc, pub_date)).start()
                        threading.Thread(target=send_email, args=("AWS", "Region", status, desc, pub_date)).start()
                        threading.Thread(target=send_sms, args=("AWS", "Region", desc)).start()
    except Exception as e: print(f"Poll Error: {e}")

def monitor_thread():
    while True:
        poll_rss()
        time.sleep(60)

# --- Web Server ---

class AlertAPIHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200); self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "monitoring": "active"}).encode())
        elif self.path == '/alerts/history':
            self.send_response(200); self.end_headers()
            self.wfile.write(json.dumps(state.history[:50]).encode())
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == '/test-alert':
            print("Manual test alert triggered")
            threading.Thread(target=send_whatsapp, args=("TEST", "LOCAL", "DEGRADED", "Test alert", "NOW")).start()
            self.send_response(200); self.end_headers()
            self.wfile.write(json.dumps({"message": "Test triggered"}).encode())
        else:
            self.send_error(404)

if __name__ == "__main__":
    # Start monitor in background
    threading.Thread(target=monitor_thread, daemon=True).start()
    
    port = int(os.environ.get("PORT", 8000))
    with socketserver.TCPServer(("0.0.0.0", port), AlertAPIHandler) as httpd:
        print(f"Server at port {port}")
        httpd.serve_forever()
