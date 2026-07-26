from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
import json

router = APIRouter()

OXAPAY_API_KEY = "-"
OXAPAY_URL = "https://api.oxapay.com/v1/payment/invoice"


class PaymentRequest(BaseModel):
    amount: float
    order_id: int


class PaymentResponse(BaseModel):
    payment_url: str
    track_id: int


@router.post("/create-payment", response_model=PaymentResponse)
def create_payment(payload: PaymentRequest):
    headers = {
        "merchant_api_key": OXAPAY_API_KEY,
        "Content-Type": "application/json",
    }

    data = {
        "amount": str(payload.amount),
        "currency": "USD",
        "lifetime": 30,
        "fee_paid_by_payer": 1,
        "under_paid_coverage": 2.5,
        "to_currency": "USDT",
        "auto_withdrawal": False,
        "mixed_payment": True,
        "callback_url": "https://brendon-genotypical-addyson.ngrok-free.dev/webhook/oxapay",
        "return_url": "https://example.com/success",
        "order_id": str(payload.order_id),
        "description": f"Order #{payload.order_id}",
        "sandbox": False
    }

    response = requests.post(
        OXAPAY_URL,
        headers=headers,
        data=json.dumps(data)
    )
    result = response.json()

    if response.status_code != 200 or "data" not in result:
        raise HTTPException(status_code=400, detail=result)

    return {
        "payment_url": result["data"]["payment_url"],
        "track_id": result["data"]["track_id"],
    }
