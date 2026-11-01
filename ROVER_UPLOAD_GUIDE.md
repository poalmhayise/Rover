# Hired -> GitHub repository Rover

Target repository: https://github.com/poalmhayise/Rover

## Upload using GitHub Desktop on Windows (recommended)

1. Download this ZIP and extract it to a folder called `Hired-for-Rover`.
2. Sign into GitHub Desktop (https://desktop.github.com) using the GitHub account that owns `poalmhayise/Rover`.
3. In GitHub Desktop: File > Clone repository > URL and enter `https://github.com/poalmhayise/Rover.git`.
4. Open the cloned repository folder using Repository > Show in Explorer.
5. **Only if Rover is empty or intended for Hired:** copy all extracted site files (including `static` and `tests` folders) into that repository folder. Do not put the ZIP file itself there. **If Rover already contains another project, stop rather than overwriting its files.**
6. In GitHub Desktop, review changes. Use commit message `Add Hired worldwide CV builder`, click Commit to main, then Push origin.
7. Confirm that GitHub shows `server.py`, `requirements.txt`, `render.yaml`, and `static/index.html` in the repository.

## Security

The ZIP does **not** include the private `.env` file, real banking details, admin password, uploaded receipts, or customer data. Keep them out of GitHub. Fill the secrets in Render dashboard's Environment after creating the web service. Never publish `.env`.

## Next step: Render

Create a Python web service connected to Rover and use the `render.yaml` deployment settings, including durable disk storage. For real checkout, the bank must first confirm that the receiving account can accept tiny USD bank payments; set `HIRED_USD_BANK_VERIFIED=1` only when confirmed. Until then keep checkout locked.
