"""
main.py — the production-style service (runs on Render).

Always on, no buttons. In a real deployment a background job feeds it order
emails; here it exposes a simple API so you can prove the same brain runs in
the cloud.

    GET  /         -> hello page
    GET  /health   -> health check
    POST /extract  -> { "order_text": "..." } -> structured order

Run locally:
    uvicorn main:app --reload
"""

import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from extractor import extract_order, needs_human_review

app = FastAPI(title="Email-to-Order Extractor", version="1.0")


class OrderIn(BaseModel):
    order_text: str


@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html><body style="font-family:sans-serif;max-width:640px;margin:40px auto">
      <h2>Email-to-Order Extractor - live</h2>
      <p>This service turns messy customer order emails into clean,
      ERP-ready structured orders.</p>
      <p>POST to <code>/extract</code> with:</p>
      <pre>{ "order_text": "5 boxes of M8 bolts and 10 rolls of brown tape" }</pre>
    </body></html>
    """


@app.get("/health")
def health():
    return {"status": "ok", "model": os.environ.get("MODEL", "gpt-5-mini")}


@app.post("/extract")
def extract(payload: OrderIn):
    try:
        order = extract_order(payload.order_text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {exc}")
    order["needs_human_review"] = needs_human_review(order)
    return order
