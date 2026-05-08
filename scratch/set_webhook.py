import asyncio
import os
from dotenv import load_dotenv
import httpx

load_dotenv()

VEXA_API_KEY = os.getenv("VEXA_API_KEY")
VEXA_API_BASE = os.getenv("VEXA_API_BASE", "https://api.cloud.vexa.ai")

async def set_webhook(url: str):
    webhook_endpoint = f"{VEXA_API_BASE}/user/webhook"
    headers = {
        "X-API-Key": VEXA_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "webhook_url": f"{url}/webhook/vexa"
    }
    
    print(f"Setting Vexa webhook to: {payload['webhook_url']}...")
    
    async with httpx.AsyncClient() as client:
        resp = await client.put(webhook_endpoint, headers=headers, json=payload)
        if resp.status_code == 200:
            print("✅ Webhook updated successfully in Vexa.ai!")
            print(resp.json())
        else:
            print(f"❌ Failed to update webhook: {resp.status_code}")
            print(resp.text)

if __name__ == "__main__":
    import sys
    # Priority: 1. Argument, 2. APP_BASE_URL env var
    target_url = sys.argv[1] if len(sys.argv) > 1 else os.getenv("APP_BASE_URL")
    
    if not target_url:
        print("❌ Error: No URL provided.")
        print("Usage: python set_webhook.py <url>  OR set APP_BASE_URL env var.")
        sys.exit(1)
        
    asyncio.run(set_webhook(target_url.rstrip("/")))
