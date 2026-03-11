from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import HTMLResponse
import asyncio
import os
from datetime import datetime
from .monitor import monitor_loop, current_status, poll_aws_rss
from .dedup import state
from .notifiers.whatsapp import send_whatsapp_alert

app = FastAPI(title="AWS Outage Notifier")

@app.on_event("startup")
async def startup_event():
    # Start the monitoring loop in the background
    asyncio.create_task(monitor_loop())

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head><title>AWS Outage Notifier</title></head>
        <body style="font-family: sans-serif; padding: 20px;">
            <h1>AWS Outage Notifier</h1>
            <p>Status: Monitoring Active</p>
            <ul>
                <li><a href="/status">Current Status</a></li>
                <li><a href="/alerts/history">Alert History</a></li>
                <li><a href="/health">Health Check</a></li>
            </ul>
        </body>
    </html>
    """

@app.get("/health")
async def health():
    return {"status": "ok", "monitoring": "active", "timestamp": datetime.now().isoformat()}

@app.get("/status")
async def get_status():
    return current_status

@app.get("/alerts/history")
async def get_history():
    return state.history

@app.post("/test-alert")
async def test_alert(background_tasks: BackgroundTasks):
    background_tasks.add_task(
        send_whatsapp_alert, 
        "TEST-SERVICE", "TEST-REGION", "DEGRADED", 
        "This is a manual test alert from the API.", 
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    return {"message": "Test WhatsApp alert triggered in background"}

@app.post("/silence/{hours}")
async def silence(hours: int):
    state.silence(hours)
    return {"message": f"Alerts silenced for {hours} hours", "until": state.silenced_until.isoformat()}

@app.post("/refresh")
async def refresh():
    await poll_aws_rss()
    return {"message": "RSS feed refreshed", "count": len(current_status)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
