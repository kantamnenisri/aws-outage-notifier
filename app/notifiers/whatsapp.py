import httpx
import os
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

async def send_whatsapp_alert(service: str, region: str, status: str, description: str, timestamp: str):
    phone = os.getenv("CALLMEBOT_PHONE")
    apikey = os.getenv("CALLMEBOT_APIKEY")
    
    if not phone or not apikey:
        print("WhatsApp Notifier: CALLMEBOT_PHONE or CALLMEBOT_APIKEY missing.")
        return

    message = (
        f"🔴 AWS OUTAGE ALERT\n"
        f"Service: {service}\n"
        f"Region: {region}\n"
        f"Status: {status}\n"
        f"Message: {description}\n"
        f"Time: {timestamp} UTC\n"
        f"Details: https://health.aws.amazon.com"
    )
    
    encoded_msg = urllib.parse.quote(message)
    url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={encoded_msg}&apikey={apikey}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=10)
            if response.status_code == 200:
                print(f"WhatsApp alert sent for {service}")
            else:
                print(f"WhatsApp alert failed: {response.text}")
        except Exception as e:
            print(f"WhatsApp error: {e}")
