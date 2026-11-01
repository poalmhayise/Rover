# Hired — Global CV & application-letter website (FNB-only payment)

A real working web app with four creative templates, live previews, payment-reference generation, FNB bank-transfer checkout, secure receipt uploads, manual owner payment confirmation, an admin dashboard, and PDF downloads after approval.

**Worldwide launch:** see `DEPLOY_PUBLIC.md` and `render.yaml` for a production-ready hosting plan and search-engine discovery setup. The public preview is live at https://hired-documents-preview.onrender.com. Real-money checkout stays blocked until persistent storage, owner banking details, and support configuration are confirmed. Render requires a paid web service with a persistent disk for safe order processing.

## Important: how payment works

Money goes **directly from the customer's bank to your FNB bank account**, not through this application. Hired never handles funds or bank passwords. The customer is instructed to transfer US$0.60 USD and uploads proof. **The owner must verify actual receipt through FNB before approving an order.** Hired does not have live FNB banking API access and cannot verify payments automatically.

The fixed worldwide price is **US$0.60 USD per document**, with no SZL conversion at checkout. Bank charges are extra and can exceed US$0.60, and some banks won't process such small international transfers. Before enabling checkout, **confirm the particular FNB account can accept USD inbound transfers**. This is a manual SWIFT/bank checkout, not an instant global merchant payment gateway.

## Windows quick start

1. Install **Python 3.11+** (check **Add Python to PATH** during installation).
2. Unzip the project and open Command Prompt inside the `Hired` folder.
3. Run:
   ```cmd
   python -m pip install -r requirements.txt
   ```
   The shareable public-source ZIP intentionally excludes `.env` so your bank details are not accidentally posted to GitHub. Run `copy .env.example .env` and enter your bank settings **privately**. The owner's working copy retains the previously supplied details.
4. Edit `.env` using Notepad. The FNB account number is already included in your **private `.env` only**, not the public example. Set `HIRED_BANK_ACCOUNT_NAME` to the exact name shown by FNB. Set `HIRED_USD_BANK_VERIFIED=1` only when FNB confirms this account is able to receive a USD-denominated transfer; otherwise keep it at `0`. Set `HIRED_SECRET_KEY` to a fresh secret and `HIRED_ADMIN_PASSWORD` to a long unique password. You can generate a secret with:
   ```cmd
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```
5. Start the site:
   ```cmd
   python server.py
   ```
6. Visit `http://127.0.0.1:8080` to use Hired. Owner dashboard: `http://127.0.0.1:8080/admin`.

**Account-holder details already provided are configured privately in the working copy.** Checkout remains disabled until you confirm with FNB that this specific account can receive USD transfers and set `HIRED_USD_BANK_VERIFIED=1`. The price is fixed at US$0.60 and does not require an SZL amount. Confirm branch/correspondent details with FNB. Never paste your online banking password into the site.

## How the buyer journey works

1. Choose **CV / Resume** or **Application letter**, fill the form, and select one of four designs.
2. Place an order. Hired generates a random private access token plus a unique `HIRED-XXXXXXXXXXXX` payment reference.
3. Send the shown amount by direct FNB bank transfer, including the unique reference. Upload bank proof (PNG/JPG/PDF, up to 3 MB).
4. The owner logs in at `/admin`, compares the payment to real FNB account transactions, and clicks **Approve**.
5. The customer refreshes their order or opens their saved private order link and downloads their finished PDF.

If an applicant closes the browser, they should save the *private status link* supplied in the order view. That link acts like a secret download key. Do not share it publicly. Do not approve an order only because a payment screenshot appears plausible.

## Publishing for phone and desktop

This is a working **source project**, not a publicly hosted URL. To put Hired on the Internet you need hosting with persistent disk storage and HTTPS. A custom domain is recommended, but a public host-provided domain can work too. See `DEPLOY_PUBLIC.md`. This app uses `sqlite3` and keeps customer records and proof uploads in `HIRED_DATA_DIR`, which must be on a durable, backed-up volume. Do not host this on an ephemeral free-tier filesystem or orders may disappear on restart. A VPS with a persistent volume and an HTTPS reverse proxy is the simplest reliable deployment.

For production:
- Set `HIRED_HOST=127.0.0.1` behind an HTTPS reverse proxy, or use `0.0.0.0` only if a properly configured HTTPS reverse proxy/network firewall protects the Python server.
- Set `HIRED_HTTPS_ONLY=1` once HTTPS is active to require `Secure` admin cookies and HSTS.
- Set strong `HIRED_ADMIN_PASSWORD` and `HIRED_SECRET_KEY`.
- Mount `HIRED_DATA_DIR` to persistent private disk, back it up, and restrict access to receipt files.
- Set a support email if you want to receive customer queries.
- Add your own privacy policy and support/contact information; customers are submitting personally identifiable career details.
- For real sales, check local tax, consumer protection and data privacy obligations with a qualified adviser.

### Deploy with Docker (suitable for a VPS)

```bash
docker build -t hired .
docker run -d --name hired --restart unless-stopped \
  --env-file .env -e HIRED_HOST=0.0.0.0 -e HIRED_DATA_DIR=/app/data \
  -p 127.0.0.1:8080:8080 -v hired-data:/app/data hired
```

Then route an HTTPS hostname to `127.0.0.1:8080` with Caddy, Nginx, or your host's managed HTTPS proxy. Never expose this app using plain HTTP for real customer payments.

## Security and scope

- A customer's document download is withheld until owner approval, not merely upload of a receipt.
- Only order owners with private tokens can access orders/downloads.
- Bank account details are intentionally shown to buyers during checkout; your **private bank login credentials** are never requested.
- Each order is stored in private SQLite. Admin can delete records when no longer needed.
- No Binance or PayPal payment options exist in this build.
- Generated PDFs are automatically laid out from customer-provided text. This is not a generative-AI writing service; users control their wording.
- There is no automated bank API verification, automated transactional email, multiuser account system, or public hosting included in the zip.

## Customise

Edit `/static/index.html`, `/static/style.css`, `/static/app.js`, and `pdf_documents.py`. All four designs render to ReportLab PDFs. Update verified bank details through `.env`, then restart the process. The per-document USD price is fixed at US$0.60.

## Tests

```bash
python -m pytest tests -q
```
