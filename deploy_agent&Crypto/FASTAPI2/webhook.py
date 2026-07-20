from fastapi import APIRouter, Request, Header, HTTPException
import hmac
import hashlib
import json
import time
import httpx

router = APIRouter()

OXAPAY_API_KEY = "-"
MAX_TIME_DRIFT = 300  # seconds

UPDATE_URL = "https://fefddf1fae27.ngrok-free.app/api/usdt/update"
AUTH_TOKEN = "-"


def verify_hmac(body: bytes, received_hmac: str) -> bool:
    calculated = hmac.new(
        OXAPAY_API_KEY.encode(),
        body,
        hashlib.sha512
    ).hexdigest()

    return hmac.compare_digest(calculated, received_hmac)


@router.post("/webhook/oxapay")
async def oxapay_webhook(
    request: Request,
    hmac_header: str = Header(None, alias="Hmac"),
    x_timestamp: str = Header(None),
):
    if not hmac_header:
        raise HTTPException(status_code=400, detail="Missing HMAC header")

    if x_timestamp:
        if abs(time.time() - int(x_timestamp)) > MAX_TIME_DRIFT:
            raise HTTPException(status_code=400, detail="Expired webhook")

    raw_body = await request.body()

    if not verify_hmac(raw_body, hmac_header):
        raise HTTPException(status_code=401, detail="Invalid HMAC signature")

    payload = json.loads(raw_body)

    if payload["status"] == "Paid":
        order_id = payload["order_id"]
        track_id = payload["track_id"]

        print(f"✅ Payment confirmed: {order_id} | Track: {track_id}")

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {AUTH_TOKEN}",
        }

        params = {
            "status": "paid",
            "order_id": int(order_id),
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.put(  # ← changed here
                    UPDATE_URL,
                    headers=headers,
                    params=params,
                )
                response.raise_for_status()

        except httpx.HTTPError as e:
            # Important: webhook should still return 200 to avoid retries
            print("❌ Failed to update order:", str(e))

    return {"status": "ok"}
