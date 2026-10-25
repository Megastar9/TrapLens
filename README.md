# TrapLens -- (https://traplens.streamlit.app/)

Think before you click.

TrapLens checks suspicious texts, emails, and screenshots using Google's Gemma 4 model. It explains the warning signs and lets you click highlighted phrases to see why they were flagged.

Built with Python, Streamlit, and the Google GenAI SDK.

## Run it locally

You'll need Python 3.12+ and a [Google AI Studio API key](https://aistudio.google.com/apikey).

```sh
git clone https://github.com/Megastar9/TrapLens.git
cd TrapLens
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows, activate the environment with `.venv\Scripts\Activate.ps1` instead.

Set your API key in the same terminal:

```sh
export GEMINI_API_KEY="your-api-key"
```

For Windows PowerShell, use `$env:GEMINI_API_KEY="your-api-key"`.

Then start the app:

```sh
python -m streamlit run app.py
```

Open http://localhost:8501, paste a message or upload a screenshot, and click **Analyze Message**.

## Deploy on Streamlit

Connect this repo to [Streamlit Community Cloud](https://share.streamlit.io/), select `main` and `app.py`, and add this in **Advanced settings → Secrets**:

```toml
GEMINI_API_KEY = "your-api-key"
```

Keep your key out of GitHub. Visitors to the hosted app use your API quota.

## Tests

```sh
python test_gemma.py
```

Add `--live` to test a real Gemma request with your key.

AI can get things wrong. TrapLens analyzes the message—it doesn't verify senders or websites. Submitted text and images are sent to Google for analysis.
