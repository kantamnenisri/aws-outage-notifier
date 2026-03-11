import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def send_sms_alert(service: str, region: str, description: str):
    enable_sms = os.getenv("ENABLE_SMS", "false").lower() == "true"
    phone = os.getenv("SMS_PHONE")
    
    if not enable_sms or not phone:
        print("SMS Notifier: Disabled or SMS_PHONE missing.")
        return

    # Keep it short for SMS
    short_msg = description[:60] + "..." if len(description) > 60 else description
    message = f"AWS OUTAGE: {service} {region} - {short_msg}"

    payload = {
        "phone": phone,
        "message": message,
        "key": "textbelt" # Free tier key
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post("https://textbelt.com/text", json=payload, timeout=10)
            result = response.json()
            if result.get("success"):
                print(f"SMS alert sent for {service}")
            else:
                print(f"SMS alert failed: {result.get('error')}")
        except Exception as e:
            print(f"SMS error: {e}")
