"""
extractor.py — the AI brain. Uses the legacy OpenAI SDK (openai==0.28).

The key is read from Streamlit secrets:

    st.secrets["openai"]["api_key"]

and falls back to the OPENAI_API_KEY environment variable when running outside
Streamlit (e.g. the FastAPI service on Render).

What it does:
  1. Takes raw order text (email body, or text pulled out of a PDF).
  2. Sends it to the model together with the product catalog.
  3. Gets back a structured order: customer, PO number, one line per item with
     the matched article code.
  4. Adds prices and totals IN PYTHON from the catalog - never from the AI -
     so the money is always exact.
"""

import json
import os

import openai

from catalog import catalog_as_text, PRICE_BY_CODE, NAME_BY_CODE, ALL_CODES

MODEL = os.environ.get("MODEL", "gpt-5-mini")


def _load_api_key() -> str:
    """
    Streamlit secrets first, environment variable second.

    In .streamlit/secrets.toml (local) or the Streamlit Cloud Secrets box:

        [openai]
        api_key = "sk-..."
    """
    try:
        import streamlit as st

        return st.secrets["openai"]["api_key"]
    except Exception:
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            raise RuntimeError(
                "No API key found. Either add it to Streamlit secrets as "
                '[openai] api_key = "sk-...", or set the OPENAI_API_KEY '
                "environment variable."
            )
        return key


SYSTEM_PROMPT = """You are an order-entry assistant for an industrial \
distributor. You read incoming customer order emails, which are messy and \
informal, and turn them into a clean structured order for the ERP system.

You get the company's product catalog. Match every item the customer asks for \
to the correct article code, using the product names and aliases. Customers \
rarely use the exact catalog wording, so use judgement.

Rules:
- Only use article codes that exist in the catalog. NEVER invent a code.
- If you cannot confidently match an item, still include the line, set
  "matched" to false, set "code" to null, and explain in "note".
- If matched but something is ambiguous (unclear size, unclear unit), set
  "matched" true and put the doubt in "note".
- Quantity must be a whole number.
- Reply with a JSON object only. No markdown, no backticks, no explanation."""

USER_TEMPLATE = """PRODUCT CATALOG (code | name | unit | price | aliases):
{catalog}

CUSTOMER ORDER (raw text):
\"\"\"
{order_text}
\"\"\"

Return JSON with exactly this shape:
{{
  "customer": "company name if stated, else null",
  "po_number": "PO number if stated, else null",
  "requested_delivery": "date or delivery note if stated, else null",
  "lines": [
    {{
      "raw_text": "what the customer wrote for this item",
      "matched": true,
      "code": "article code from the catalog, or null",
      "product_name": "catalog name, or null",
      "quantity": 1,
      "note": "short note if unclear, else empty string"
    }}
  ],
  "overall_note": "anything a human should double-check, else empty string"
}}"""


def _call_model(messages):
    """
    Call the model with openai==0.28 syntax.

    Tries JSON mode first. Some models reject the response_format parameter,
    so if that call fails we retry without it - the prompt already asks for
    JSON only, and _parse_json() strips code fences just in case.
    """
    openai.api_key = _load_api_key()

    try:
        return openai.ChatCompletion.create(
            model=MODEL,
            messages=messages,
            response_format={"type": "json_object"},
        )
    except Exception:
        return openai.ChatCompletion.create(
            model=MODEL,
            messages=messages,
        )


def _parse_json(raw: str) -> dict:
    """Parse the model's reply, tolerating ```json fences."""
    raw = (raw or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        start, end = raw.find("{"), raw.rfind("}")
        if start != -1 and end != -1:
            raw = raw[start:end + 1]
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("Model did not return valid JSON: %s\n\nGot:\n%s" % (exc, raw))


def extract_order(order_text):
    """Run one order through the model and return a structured dict."""
    if not order_text or not order_text.strip():
        raise ValueError("Empty order text.")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": USER_TEMPLATE.format(
                catalog=catalog_as_text(),
                order_text=order_text.strip(),
            ),
        },
    ]

    response = _call_model(messages)
    raw = response["choices"][0]["message"]["content"]

    data = _parse_json(raw)
    data.setdefault("lines", [])
    _validate_and_price(data)
    return data


def _validate_and_price(order):
    """
    Guard rails + money math, done in Python.

    - Any article code the model invented (not in our catalog) is thrown away
      and the line is marked unmatched.
    - Unit price, line total and order total come from the catalog.
    """
    total = 0.0
    for line in order["lines"]:
        code = line.get("code")

        if code and code not in ALL_CODES:
            line["note"] = (line.get("note") or "") + \
                " [code '%s' not in catalog - cleared]" % code
            line["code"] = None
            line["matched"] = False
            code = None

        if code:
            line["product_name"] = NAME_BY_CODE[code]

        qty = line.get("quantity")
        if not isinstance(qty, int):
            try:
                qty = int(float(qty))
            except (TypeError, ValueError):
                qty = 0
            line["quantity"] = qty

        unit_price = PRICE_BY_CODE.get(code)
        if unit_price is not None:
            line["unit_price"] = unit_price
            line["line_total"] = round(unit_price * qty, 2)
            total += line["line_total"]
        else:
            line["unit_price"] = None
            line["line_total"] = None

    order["order_total"] = round(total, 2)


def needs_human_review(order):
    """True if anything is unmatched or flagged - the 'exception' case."""
    if order.get("overall_note"):
        return True
    return any(
        (not line.get("matched")) or line.get("note")
        for line in order.get("lines", [])
    )
