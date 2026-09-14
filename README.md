# 📦 Email-to-Order AI

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

1. **Read** — the order text goes to the OpenAI API together with the product catalog.
2. **Match** — the model maps what the customer wrote ("M8 bolts") to the article
   code the ERP needs (`ART-90432`).
3. **Price** — prices, line totals and the order total are calculated **in Python**
   from the catalog, never by the AI, so the money is always exact.
4. **Flag** — anything unmatched or ambiguous is marked as an exception for a human.

Two safety features worth knowing about, because clients ask:

- If the model ever invents an article code that isn't in the catalog, the code is
  thrown away and the line is marked unmatched. It cannot make up products.
- `temperature=0` means the same order gives the same result every time.

---

# Step-by-step: running this for the first time

## Step 1 — Install Python

Check whether you already have it. Open Terminal (Mac) or Command Prompt (Windows):

```bash
python --version
```

If you see 3.10 or higher, you're set. If not, install from
<https://www.python.org/downloads/>.
**On Windows, tick "Add Python to PATH" during install.**

On Mac/Linux you may need to type `python3` instead of `python` everywhere below.

## Step 2 — Get an OpenAI API key

1. Go to <https://platform.openai.com/api-keys>
2. **Create new secret key**, copy it (starts with `sk-`). You only see it once.
3. Go to Settings → Billing and add a small amount of credit.
4. **Set a usage limit of $5** while you're learning. Nothing here should cost
   more than a few cents, but the limit means no surprises.

## Step 3 — Put the project on your computer

Unzip this folder somewhere easy, then open a terminal **inside** the folder:

```bash
cd path/to/order-ai-openai
```

(Tip: on Windows you can type `cd ` then drag the folder onto the terminal window.)

## Step 4 — Install the libraries

```bash
pip install -r requirements.txt
```

Takes a minute or two. If `pip` isn't found, try `python -m pip install -r requirements.txt`.

## Step 5 — Put your API key in Streamlit secrets

Inside the project folder there is a `.streamlit` folder. Create a file in it
called `secrets.toml` (copy `secrets.toml.example`) containing:

```toml
[openai]
api_key = "sk-your-key-here"
```

That's it — the apps read `st.secrets["openai"]["api_key"]` automatically.

`secrets.toml` is listed in `.gitignore`, so it will never be uploaded to GitHub.

> Only needed for the FastAPI service (Step 8) and Render, which can't read
> Streamlit secrets: set an environment variable instead —
> `export OPENAI_API_KEY=sk-...` (Mac/Linux) or `set OPENAI_API_KEY=sk-...` (Windows).
> The code falls back to it automatically.

## Step 6 — Run the demo

```bash
streamlit run app.py
```

A browser tab opens. A sample order is already filled in — click **Extract order**.
In a couple of seconds you'll see the clean order with article codes and totals.

Try the files in `samples/`:
- `order_easy.txt` — straightforward
- `order_messy.txt` — informal, lowercase, vague. **This is the impressive one.**
- `order_with_exception.txt` — contains a product that doesn't exist in the catalog,
  so you can see it flag the problem instead of guessing

## Step 7 — Run the approval screen

Stop the app with `Ctrl+C`, then:

```bash
streamlit run approval_app.py
```

In the sidebar choose **Pre-loaded samples** → **Load into queue**. Review an order,
change something in the table, click **Approve**, then download the CSV at the bottom.
That CSV is the file that would go into the ERP.

Note the second order has a line the AI couldn't match — the Approve button stays
disabled until you fix it. That safety behaviour is a strong selling point.

## Step 8 — Run the cloud service locally

```bash
uvicorn main:app --reload
```

Open <http://localhost:8000>. That's the always-on version — same brain, no buttons.

---

# Putting it on GitHub

You need this public so agencies and clients can see your code.

## Step 1 — Create an account and repo
1. Sign up at <https://github.com>
2. Click **+** (top right) → **New repository**
3. Name it `email-to-order-ai`, set it **Public**, don't add any files. **Create repository.**

## Step 2 — Upload

Easiest way, no commands:
- On the empty repo page click **uploading an existing file**
- Drag in every file **except** `.env` if you made one
- Click **Commit changes**

Or with git, if you have it installed:
```bash
git init
git add .
git commit -m "Email-to-order AI demo"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/email-to-order-ai.git
git push -u origin main
```

## ⚠️ Never commit your API key
`.gitignore` already excludes `.env`. Before pushing, double-check no file contains
your `sk-...` key. If a key is ever exposed, delete it in the OpenAI dashboard and
make a new one.

---

# Deploying (free)

## Streamlit Community Cloud — for the shareable demo link

1. Go to <https://share.streamlit.io> and sign in with GitHub.
2. **New app** → pick your repo → main file: `app.py`.
3. **Advanced settings → Secrets**, paste exactly this (same format as your local file):
   ```toml
   [openai]
   api_key = "sk-your-key-here"
   ```
4. **Deploy.** You get a public link like `https://yourname-email-to-order.streamlit.app`

Put that link in your LinkedIn messages and Upwork profile. Deploy `approval_app.py`
as a second app the same way.

## Render — for the always-on service

1. Go to <https://render.com>, sign in with GitHub.
2. **New +** → **Blueprint** → pick your repo. Render reads `render.yaml` itself.
3. When prompted, paste `OPENAI_API_KEY` as a secret value.
4. **Apply.** You get a URL like `https://order-extractor.onrender.com`

The free plan sleeps when idle, so the first request after a pause takes ~30 seconds.
Fine for a demo.

---

# Where everything lives

- **GitHub** stores your code.
- **Streamlit Cloud / Render** run your code — their machines, not the client's.
- **The API key** sits in your hosting environment, tied to **your** OpenAI account.
  The client never sees it. You pay OpenAI; you bill the client. That's why you own
  the API, not them.
- In a real deployment the client's **inbox** and **ERP** plug into the two ends.
  This demo stops at producing the clean order, so you can show results without
  touching anyone's live systems.

---

# Cost

With `gpt-5-mini` an order costs roughly **€0.005–0.02** to process, so a client
doing 1,000 orders a month costs you about €5–20 in API. That's why you bundle the
API cost into a flat monthly fee.

Prices and model names change — check <https://platform.openai.com/docs/pricing>.
To switch models, set the `MODEL` environment variable; no code change needed.

---

# Troubleshooting

**`module 'openai' has no attribute 'ChatCompletion'`**
→ You have the new SDK installed. This project uses the legacy one:
`pip install openai==0.28`

**`ModuleNotFoundError: No module named 'openai'`**
→ `pip install -r requirements.txt` didn't run in this folder. Re-run it.

**`AuthenticationError` / `api_key must be set`**
→ Your key isn't set in this terminal. Redo Step 5 (it resets when you close the terminal).

**`RateLimitError` or "insufficient quota"**
→ No credit on the OpenAI account. Add a few dollars in Billing.

**`model not found` / `does not exist`**
→ `gpt-5-mini` isn't enabled on your account. Check the models list in your OpenAI
dashboard and set another one: `set MODEL=gpt-4o-mini` (no code change needed).

**`Unrecognized request argument: response_format`**
→ Handled automatically — the code retries without it. Nothing to fix.

**Streamlit opens but nothing happens on click**
→ Look at the terminal; the real error prints there.

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
