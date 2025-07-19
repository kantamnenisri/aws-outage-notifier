# AWS Outage Alert Notifier

A fresh infrastructure monitoring service that tracks AWS service health via public RSS feeds and provides multi-channel notifications across WhatsApp, Email, and SMS.

**Live Demo:** [https://aws-outage-notifier.onrender.com](https://aws-outage-notifier.onrender.com)

**Last Updated:** February 15, 2026

## Features
- **RSS Monitoring**: Polls `status.aws.amazon.com/rss/all.rss` every 60 seconds.
- **Incident Classification**: Automatically identifies DEGRADED and OUTAGE states.
- **Multi-Channel Alerts**:
  - **WhatsApp**: Via CallMeBot API.
  - **Email**: Via Gmail SMTP (HTML-formatted).
  - **SMS**: Via Textbelt API.
- **Smart Deduplication**: Prevents alert fatigue with a 60-minute deduplication window per service/region.
- **Global Silence**: API endpoint to mute all alerts for a specified duration.
- **Docker Ready**: Fully containerized for easy deployment.

## Setup

### Environment Variables
Create a `.env` file based on `.env.example`:
```env
CALLMEBOT_PHONE=+13058143780
CALLMEBOT_APIKEY=5042020
ALERT_EMAIL_TO=recipient@example.com
ALERT_EMAIL_FROM=sender@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
SMS_PHONE=+919XXXXXXXXX
ENABLE_SMS=true
```

### Local Execution
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```

### API Usage
- `GET /health`: System status check.
- `GET /status`: Current AWS service health table.
- `GET /alerts/history`: View last 50 alerts sent.
- `POST /test-alert`: Trigger manual test to all configured channels.
- `POST /silence/{hours}`: Mute notifications for X hours.

## 💡 Inspiration
This project is a reference implementation exploring concepts related to 
multi-cloud reliability engineering. The author holds USPTO patent 
applications in this domain (US 19/325,718 and US 19/344,864).

## Health Check
- Added /ping endpoint for automated health monitoring.
