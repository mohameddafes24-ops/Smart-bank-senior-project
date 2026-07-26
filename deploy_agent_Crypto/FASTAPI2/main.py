from fastapi import FastAPI
from payments import router as payments_router
from webhook import router as webhook_router

app = FastAPI(title="OxaPay Integration")

app.include_router(payments_router)
app.include_router(webhook_router)
