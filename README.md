# 📦 Email-to-Order AI

**Live demo:** https://www.loom.com/share/59e3f13150794924a7bd5daa6d44f5f2

Turns messy customer order emails and PDFs into clean, ERP-ready orders.
Built with the OpenAI API (`openai==0.28`, model `gpt-5-mini`).

Distributors and manufacturers still receive many orders as free-text emails and
PDF attachments. Someone reads each one, works out which product the customer
means, looks up the article number and price, and types it into the ERP. This
project does the reading and matching, and gives a person a one-click approval
step instead.

**Three pieces, one shared brain:**

| File | What it is | Use it for |
|---|---|---|
| `app.py` | Streamlit page: paste an order → see the clean result | Demo on a call |
| `approval_app.py` | Review queue: approve / fix / reject each order | Showing the human-in-the-loop step |
| `main.py` | Always-on API service | Proving it runs in the cloud |

All three import `extractor.py`, so the AI logic exists in exactly one place.

---

## How it works

1. **Read** - the order text goes to the OpenAI API together with the product catalog.
2. **Match** - the model maps what the customer wrote ("M8 bolts") to the article
   code the ERP needs (`ART-90432`).
3. **Price** - prices, line totals and the order total are calculated **in Python**
   from the catalog, never by the AI, so the money is always exact.
4. **Flag** - anything unmatched or ambiguous is marked as an exception for a human.

Two safety features worth knowing about, because clients ask:

- If the model ever invents an article code that isn't in the catalog, the code is
  thrown away and the line is marked unmatched. It cannot make up products.
- `temperature=0` means the same order gives the same result every time.

---

# Files

```
order-ai-openai/
├── extractor.py       # AI brain: calls OpenAI, matches catalog, prices in Python
├── catalog.py         # product list (would come from the ERP in production)
├── app.py             # Streamlit demo
├── approval_app.py    # approval queue + CSV export
├── main.py            # FastAPI service for Render
├── requirements.txt
├── render.yaml        # Render deploy config
├── .streamlit/secrets.toml.example
├── .gitignore
└── samples/           # three example order emails
```
