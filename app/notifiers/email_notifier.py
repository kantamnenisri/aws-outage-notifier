import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

def send_email_alert(service: str, region: str, status: str, description: str, timestamp: str):
    email_to = os.getenv("ALERT_EMAIL_TO")
    email_from = os.getenv("ALERT_EMAIL_FROM")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")

    if not all([email_to, email_from, gmail_password]):
        print("Email Notifier: Missing configuration (TO/FROM/PASSWORD).")
        return

    subject = f"🔴 AWS OUTAGE: {service} in {region}"
    
    html = f"""
    <html>
    <body style="font-family: sans-serif; color: #333;">
        <div style="background-color: #d32f2f; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
            <h1 style="margin: 0;">AWS Outage Alert</h1>
        </div>
        <div style="padding: 20px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 8px 8px;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 8px; font-weight: bold;">Service:</td><td style="padding: 8px;">{service}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Region:</td><td style="padding: 8px;">{region}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Status:</td><td style="padding: 8px;"><span style="color: #d32f2f; font-weight: bold;">{status}</span></td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Time:</td><td style="padding: 8px;">{timestamp} UTC</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Message:</td><td style="padding: 8px;">{description}</td></tr>
            </table>
            <p style="margin-top: 20px;">
                <a href="https://health.aws.amazon.com" style="background-color: #1976d2; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">View Official AWS Dashboard</a>
            </p>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg['From'] = email_from
    msg['To'] = email_to
    msg['Subject'] = subject
    msg.attach(MIMEText(html, 'html'))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(email_from, gmail_password)
            server.send_message(msg)
            print(f"Email alert sent for {service}")
    except Exception as e:
        print(f"Email error: {e}")
