"""
approval_app.py — the APPROVAL SCREEN (human-in-the-loop step).

Orders arrive in a queue, a person glances at each one, fixes anything wrong,
and clicks Approve. Approved orders become an ERP import file.

Run:
    streamlit run approval_app.py

Tip for live demos: pick "Pre-loaded samples" in the sidebar — it runs the whole
flow with NO API calls, so a bad connection can never break your demo.
"""

import copy
import csv
import glob
import io

import streamlit as st

from catalog import CATALOG, PRICE_BY_CODE, NAME_BY_CODE

CODE_OPTIONS = [""] + [p["code"] for p in CATALOG]

st.set_page_config(page_title="Order Approval Queue", page_icon="✅", layout="wide")

SAMPLE_QUEUE = [
    {
        "customer": "Schmidt Handel",
        "po_number": "88123",
        "requested_delivery": "Hamburg warehouse",
        "source_email": "From: einkauf@schmidt-handel.de\n\nHello,\n\nPlease deliver:\n"
        "- 10 boxes M8 bolts\n- 5 boxes M10 bolts\n- 20 rolls brown packing tape\n\n"
        "PO 88123. Deliver to our Hamburg warehouse.\n\nBest regards,\nKlaus Schmidt",
        "lines": [
            {"raw_text": "10 boxes M8 bolts", "code": "ART-90432", "quantity": 10, "note": ""},
            {"raw_text": "5 boxes M10 bolts", "code": "ART-90433", "quantity": 5, "note": ""},
            {"raw_text": "20 rolls brown packing tape", "code": "ART-55012", "quantity": 20, "note": ""},
        ],
    },
    {
        "customer": "Nordic Supply",
        "po_number": None,
        "requested_delivery": None,
        "source_email": "From: orders@nordic-supply.com\n\nHi,\n\nPlease send:\n"
        "- 4 boxes of M12 bolts\n- 8 rolls of stretch wrap\n"
        "- 5 bags of cable ties (not sure which size, whatever is standard)\n\nThanks",
        "lines": [
            {"raw_text": "4 boxes of M12 bolts", "code": "", "quantity": 4,
             "note": "M12 not in catalog — needs a human decision"},
            {"raw_text": "8 rolls of stretch wrap", "code": "ART-55020", "quantity": 8, "note": ""},
            {"raw_text": "5 bags of cable ties (size unclear)", "code": "ART-77100",
             "quantity": 5, "note": "Guessed 200mm — confirm with customer"},
        ],
    },
]


def recalc(lines):
    """Prices and totals from the catalog — never from the AI."""
    total = 0.0
    for ln in lines:
        price = PRICE_BY_CODE.get(ln.get("code"))
        qty = ln.get("quantity") or 0
        if price is not None:
            ln["unit_price"] = price
            ln["line_total"] = round(price * qty, 2)
            total += ln["line_total"]
        else:
            ln["unit_price"] = None
            ln["line_total"] = None
    return round(total, 2)


if "queue" not in st.session_state:
    st.session_state.queue = []
if "approved" not in st.session_state:
    st.session_state.approved = []

st.title("✅ Order Approval Queue")
st.caption(
    "The AI reads each incoming order; a person approves it in seconds instead "
    "of retyping it for minutes."
)

with st.sidebar:
    st.header("Load incoming orders")
    mode = st.radio("Source", ["Pre-loaded samples", "Live AI extraction"])

    if st.button("⬇ Load into queue", use_container_width=True):
        if mode == "Pre-loaded samples":
            st.session_state.queue = copy.deepcopy(SAMPLE_QUEUE)
        else:
            from extractor import extract_order

            loaded = []
            for path in sorted(glob.glob("samples/*.txt")):
                with open(path, encoding="utf-8") as fh:
                    text = fh.read()
                try:
                    o = extract_order(text)
                    o["source_email"] = text
                    loaded.append(o)
                except Exception as exc:  # noqa: BLE001
                    st.error(f"{path}: {exc}")
            st.session_state.queue = loaded
        st.success(f"{len(st.session_state.queue)} order(s) loaded.")

    st.divider()
    st.metric("Pending", len(st.session_state.queue))
    st.metric("Approved", len(st.session_state.approved))

if not st.session_state.queue:
    st.info("⬅ Click **Load into queue** to bring in orders to review.")
else:
    order = st.session_state.queue[0]
    st.subheader(f"Reviewing: {order.get('customer') or 'Unknown customer'}")
    st.caption(
        f"{len(st.session_state.queue)} waiting · PO: {order.get('po_number') or '—'} "
        f"· Delivery: {order.get('requested_delivery') or '—'}"
    )

    a, b = st.columns([1, 1.3])

    with a:
        st.markdown("**Original email**")
        st.text_area(
            "original", value=order.get("source_email", ""), height=320,
            label_visibility="collapsed", disabled=True,
        )

    with b:
        st.markdown("**Clean order — fix anything wrong, then approve**")
        edited = st.data_editor(
            [
                {
                    "Customer wrote": l.get("raw_text", ""),
                    "Article code": l.get("code") or "",
                    "Qty": l.get("quantity") or 0,
                    "Flag": l.get("note", ""),
                }
                for l in order["lines"]
            ],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Article code": st.column_config.SelectboxColumn(options=CODE_OPTIONS),
                "Qty": st.column_config.NumberColumn(min_value=0, step=1),
                "Flag": st.column_config.TextColumn(disabled=True),
            },
            key="editor",
        )

        new_lines = [
            {
                "raw_text": row["Customer wrote"],
                "code": row["Article code"] or "",
                "product_name": NAME_BY_CODE.get(row["Article code"], ""),
                "quantity": int(row["Qty"] or 0),
                "note": row["Flag"],
            }
            for row in edited
        ]
        total = recalc(new_lines)

        unmatched = [l for l in new_lines if not l["code"]]
        if unmatched:
            st.warning(
                f"⚠️ {len(unmatched)} line(s) have no article code. Pick one from "
                "the dropdown — the order can't post to the ERP until they're set."
            )
        st.metric("Order total", f"EUR {total:.2f}")

        c1, c2 = st.columns(2)
        if c1.button("✅ Approve & send to ERP", type="primary",
                     use_container_width=True, disabled=bool(unmatched)):
            order["lines"] = new_lines
            order["order_total"] = total
            st.session_state.approved.append(order)
            st.session_state.queue.pop(0)
            st.rerun()
        if c2.button("🗑 Reject", use_container_width=True):
            st.session_state.queue.pop(0)
            st.rerun()

if st.session_state.approved:
    st.divider()
    st.subheader("📤 Approved — ready for the ERP")
    st.caption("In production these post automatically (file drop or API call).")

    flat = [
        {
            "customer": o.get("customer") or "",
            "po_number": o.get("po_number") or "",
            "article_code": l["code"],
            "quantity": l["quantity"],
            "unit_price": l.get("unit_price"),
            "line_total": l.get("line_total"),
        }
        for o in st.session_state.approved
        for l in o["lines"]
    ]
    st.dataframe(flat, use_container_width=True, hide_index=True)

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(flat[0].keys()))
    writer.writeheader()
    writer.writerows(flat)
    st.download_button(
        "⬇ Download ERP import file (CSV)",
        data=buf.getvalue(),
        file_name="approved_orders.csv",
        mime="text/csv",
    )
