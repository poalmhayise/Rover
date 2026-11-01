# Publish Hired worldwide — setup guide

## What you will receive when Hired is published

Hired will have a real, public HTTPS address such as `https://<the-name-render-assigns>.onrender.com`, reachable by people in any country with internet access. Later, connect a professional domain (subject to purchase and availability). Your computer does **not** need to stay on.

This ZIP is *source code only*. Downloading it is not publishing. Hired has NOT been deployed or indexed yet. You must connect a hosting account and finish the steps below. Since personal documents and payment proofs are saved in SQLite and files, **do not use a host whose storage disappears on redeploy**.

## Recommended path: Render (the Render app can also help with publishing)

1. Connect Render to ChatGPT if that option was offered, or go to https://render.com and create an account. You may also need to connect a GitHub repository containing the **public-source ZIP contents**. Do not upload any `.env` file to GitHub.
2. Create a new Render **Blueprint** from that repository, using the included `render.yaml`. It defines a Python web service and persistent storage. A paid instance + disk is required; confirm Render's current prices before proceeding.
3. When Render requests environment variables, set the values below **privately in Render**, never in your public repository:
   - `HIRED_BANK_ACCOUNT_NAME`: your verified FNB account-holder name.
   - `HIRED_BANK_ACCOUNT_NUMBER`: your verified FNB account number.
   - `HIRED_BANK_SWIFT`: confirm with FNB; the bank publicly lists `FIRNSZMX` for incoming SWIFT payments.
   - `HIRED_BANK_BRANCH`: branch details recommended by FNB for international payments.
   - `HIRED_USD_BANK_VERIFIED`: keep `0` (checkout disabled) until FNB confirms your specific account can receive US$0.60 USD transfers; then set `1`. No SZL amount or FX conversion is used at checkout.
   - `HIRED_ADMIN_PASSWORD`: a long, unique owner password, **not** a bank login password.
   - `HIRED_SUPPORT_EMAIL`: support contact for customers, refunds and data requests.
   - `HIRED_PUBLIC_URL`: the site's eventual HTTPS address. If not known during initial Blueprint creation, leave it empty and update it after deployment in Render's environment-variable settings. Restart / redeploy the app to apply changes.
   - `HIRED_SECRET_KEY`: Render generates this in `render.yaml`. Keep it private. Do not change it casually because active admin sessions would be invalidated.
4. In the Render dashboard, check that the web service is running, HTTPS is active, and the persistent disk is mounted at `/opt/render/project/src/data`.
5. Visit your real public URL on **another device**. Test document generation with a controlled order. Verify that you cannot download a document before bank payment is manually approved.
6. Visit `/admin` to verify your owner login. Do not approve unverified receipts; confirm funds in FNB first.

## Make it appear in search engines

After `HIRED_PUBLIC_URL` is configured, Hired serves:
- `/robots.txt` — tells search engines which routes to crawl.
- `/sitemap.xml` — lists the homepage and useful CV/application-letter guides.
- Search-friendly page titles, description text, canonical URLs, OpenGraph metadata, and structured data.

Go to https://search.google.com/search-console and verify your site/domain. Submit your site's actual `https://YOURDOMAIN/sitemap.xml`. Use URL Inspection to request indexing of the homepage. Google decides if/when to index and rank; this is not instant or guaranteed.

You can also share the public URL on social media or with people who need a CV. **Search discoverability is not automatic sales.** Useful content, referrals, good service and trustworthy payment details still matter.

## Global-access versus global-payments caveat

Everyone can visit Hired after publication, but **FNB bank transfer only is not practical for every international customer.** Your bank may accept inward USD SWIFT payments, but receiving USD into the *specific account* must be confirmed with FNB. Transfer fees and clearing delays frequently exceed a US$0.60 product price. Some customers' banks may not allow small cross-border payments at all. Verify with FNB which inward currencies and transfer instructions your account supports. Do not imply instant downloads when manual payment review is required.

For lower-friction global sales *while keeping the funds in FNB*, ask FNB whether your account qualifies for an **FNB-hosted merchant eCommerce checkout**. This is not integrated into this version and would require separate approval, fees, and implementation. Do not add alternative payment providers without your instruction.

## Security and operation

- Never publish `.env`, admin passwords, customer resumes, or payment receipts.
- Use HTTPS and a strong administrator password; regularly back up your data directory.
- Decide and publish a clear privacy policy, deletion/retention policy, refund procedure and support contact before taking real orders.
- Protect personal CVs; do not upload receipts or personal data into public URLs.
- A receipt upload alone does **not** confirm funds. You still approve each order manually after checking FNB.

## Customer experience after publication

Go to Hired → choose a CV or letter → fill in details → pick a template → see preview → complete FNB payment instructions → upload proof → wait for manual approval → download PDF. Customers can use the site from any connected phone or computer; you manage orders privately.
