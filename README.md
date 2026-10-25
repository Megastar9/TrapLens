# ◈ TrapLens

**Think Before You Click.** A Streamlit scam-awareness app powered by Google's real
`gemma-4-26b-a4b-it` through the official `google-genai` SDK. Paste a message, upload a
screenshot, or try an example. Get an explained risk level, exact evidence, and safety steps.
No database, accounts, fake results, or numerical scam probabilities.

## Quick start (macOS / Linux)

Use Python 3.10 or newer. Open Terminal and run:

```sh
cd TrapLens
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

If `.venv` already exists, just activate it and install the requirements.

### Configure your Google API key

1. Open [Google AI Studio](https://aistudio.google.com/apikey), sign in, and create an API key for a Google project with Gemini API access.
2. Set **GEMINI_API_KEY in the same terminal where you will start the app**. On macOS's default zsh, this prompts without displaying your key or putting it in command history:

```sh
read -s 'GEMINI_API_KEY?Paste your Google API key, then press Enter: '
export GEMINI_API_KEY
printf '\n'
```

On Bash, use `read -s -p 'Google API key: ' GEMINI_API_KEY` and then `export GEMINI_API_KEY`.
The environment variable lasts for that terminal session. Opening a new terminal requires setting it again.
Do not put the key in `app.py`, `analyzer.py`, source control, or a screenshot.
The app reads the environment directly; it does **not** automatically load `.env` files.

3. Start the app:

```sh
python -m streamlit run app.py
```

Open **http://localhost:8501** if a browser does not open automatically. Keep the terminal
running; press **Control+C** to stop. After changing the API key, restart the server.

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$key = Read-Host "Google API key" -AsSecureString
$env:GEMINI_API_KEY = [System.Net.NetworkCredential]::new("", $key).Password
python -m streamlit run app.py
```

## Use TrapLens

- Paste up to 20,000 characters and/or upload a PNG, JPEG, or WebP screenshot (8 MB,
  20 megapixels maximum). Crop images to the relevant message for readable text.
- Click **Analyze Message**. Example buttons populate the input; analysis still calls Google.
- Read the risk summary, **Evidence Mode**, recommendations, and assessment limitations.
- Click highlighted phrases in Evidence Mode to reveal explanations. Tab and Enter also work.
  Repeated and overlapping quotes are supported; clicking highlights does not make API calls.
- Screenshot transcriptions are visible for comparison. Download the JSON report if needed.
- Changing the input hides the previous assessment until you analyze again. Clear resets the form.

## Tests

```sh
python test_gemma.py
python test_gemma.py --live
```

The first command runs offline backend and Streamlit interaction tests with isolated test
fixtures. These fixtures are never used by the app to generate results. The second makes a
real Gemma request (may use your quota), or explicitly skips if no key is configured.

## How it works

`analyzer.py` validates input and images, strips image metadata, and sends an inline image
and message to Google with analysis instructions. It requests JSON in the prompt, then
validates the response using Pydantic. No reliance on server-side JSON-schema support.
Malformed JSON, missing fields, ungrounded quotes, empty responses, and API errors produce
safe retry messages, never fabricated fallback assessments. Requests have a 60-second
HTTP timeout. Gemma thinking is disabled using `thinking_level="minimal"` to reduce latency. Invalid or ungrounded model output triggers one corrective retry (up to two API calls,
which may consume additional quota). If both attempts fail validation, no assessment is shown.
API connection and permission errors are not automatically retried.

Each text quote must be an exact substring of the original input. Screenshot quotes must
match Gemma's transcription, which **is not independent OCR verification** and can be wrong.
Model explanations and classifications remain AI-generated and are not guaranteed accurate.
The prompt instructs Gemma to treat message instructions as untrusted and never claim external
verification. No browsing, URL checks, tools, or sender verification are performed.

High and Medium require quoted evidence. Low is not a safety guarantee; Uncertain is used
when context is insufficient. Suspicious URLs are displayed as plain text, not clickable links.

## Privacy and deployment

The server reads the API key from its environment and never renders it in the UI.
TrapLens stores current inputs/results in Streamlit session memory, not a database or files.
Submissions are sent to Google; Google's applicable API terms and data handling policies apply.
Remove sensitive data before submitting. Downloaded reports contain message excerpts.

For this hackathon, run locally. A public deployment needs abuse controls and request limits
because visitors would consume the server's API quota. Configure the environment variable in
your host's secret settings; do not commit it. Do not enable debug logging of API requests.

## Troubleshooting

- **Missing key:** export `GEMINI_API_KEY` before starting Streamlit in the same terminal.
- **Access rejected / model unavailable:** check key restrictions, project access, and model availability in AI Studio. The app never silently switches models.
- **Quota limit:** wait and check your project's API usage/quota.
- **Invalid response or unmatched evidence:** retry with a shorter message or clearer screenshot.
- **Connection failure:** check network access to Google's API and try again.

## Files

- `app.py` — responsive Streamlit interface and session state
- `analyzer.py` — real Gemma integration, validation, safe errors
- `highlighting.py` — escaped interactive source highlights
- `test_gemma.py` — offline tests and optional live API smoke test
- `requirements.txt` — bounded dependency versions
- `.streamlit/config.toml` — dark theme and upload limits
- `.gitignore` — excludes secrets and local environment files

[Google's Gemma API documentation](https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api)
