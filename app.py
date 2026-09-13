"""
app.py — the DEMO you show on a call.

Paste an order email, click a button, watch it become a clean ERP-ready order.

Run:
    streamlit run app.py
"""

import io

import streamlit as st

from extractor import extract_order, needs_human_review
from catalog import CATALOG

st.set_page_config(page_title="Email-to-Order AI", page_icon="📦", layout="wide")

st.title("📦 Email-to-Order Extractor")
st.caption(
    "Customer orders arrive as messy emails and PDFs. This reads them, matches "
    "each item to your article numbers, and produces a clean order for the ERP - "
    "no manual typing."
)

SAMPLE = """From: purchasing@meyer-bau.de
Subject: Bestellung / order

Hi,

Please send us the following to our Dortmund site:

- 5 boxes of M8 bolts
- a couple of boxes of the M10 ones as well (let's say 3)
- 10 rolls of the brown packing tape
- 2 bags of the long black cable ties (300mm)
- 4 pairs of safety gloves, size L

Need it by next Friday if possible. Our PO is 4501-2231.

Thanks,
Stefan Meyer
Meyer Bau GmbH
"""

left, right = st.columns(2)

with left:
    st.subheader("1. Incoming order")

    uploaded = st.file_uploader("Upload a PDF order (optional)", type=["pdf"])
    prefill = ""
    if uploaded is not None:
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(uploaded.read()))
            prefill = "\n".join((p.extract_text() or "") for p in reader.pages)
            st.success("PDF text pulled out — check it below, then extract.")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Could not read that PDF: {exc}")

    order_text = st.text_area(
        "Order email / text", value=prefill or SAMPLE, height=380
    )
    run = st.button("▶ Extract order", type="primary", use_container_width=True)

with right:
    st.subheader("2. Clean order for the ERP")

    if run:
        try:
            with st.spinner("Reading the order…"):
                order = extract_order(order_text)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Something went wrong: {exc}")
        else:
            cols = st.columns(3)
            cols[0].metric("Customer", order.get("customer") or "—")
            cols[1].metric("PO number", order.get("po_number") or "—")
            cols[2].metric("Order total", f"EUR {order.get('order_total', 0):.2f}")

            if order.get("requested_delivery"):
                st.write(f"**Delivery:** {order['requested_delivery']}")

            st.dataframe(
                [
                    {
                        "Customer wrote": l.get("raw_text", ""),
                        "Article code": l.get("code") or "❓ no match",
                        "Product": l.get("product_name") or "—",
                        "Qty": l.get("quantity"),
                        "Unit price": f"EUR {l['unit_price']:.2f}" if l.get("unit_price") else "—",
                        "Line total": f"EUR {l['line_total']:.2f}" if l.get("line_total") else "—",
                        "Note": l.get("note", ""),
                    }
                    for l in order.get("lines", [])
                ],
                use_container_width=True,
                hide_index=True,
            )

            if needs_human_review(order):
                st.warning(
                    "⚠️ Something here needs a human glance (see the Note column). "
                    "In production only these exceptions go to a person — clean "
                    "orders flow straight through."
                )
                if order.get("overall_note"):
                    st.info(order["overall_note"])
            else:
                st.success("✅ Fully matched — this would post to the ERP automatically.")

            with st.expander("Raw structured data (what the ERP receives)"):
                st.json(order)
    else:
        st.info("Click **Extract order** to see the result here.")

with st.sidebar:
    st.header("Product catalog")
    st.caption("In production this syncs from the client's ERP.")
    st.dataframe(
        [{"Code": p["code"], "Name": p["name"], "EUR": p["price"]} for p in CATALOG],
        hide_index=True,
        use_container_width=True,
    )
