# Ho-Thu-V-c-i-ti-n
# Thu Vũ AI — Autumn Fragrance Studio

## Run locally
1. Python 3.10+ recommended.
2. `pip install -r requirements.txt`
3. Create a Gemini key at https://aistudio.google.com/apikey
4. Set `GOOGLE_API_KEY` as an environment variable or enter it in the app sidebar.
5. Run `streamlit run app.py`

## Streamlit Community Cloud Secrets
```toml
GOOGLE_API_KEY = "your-gemini-api-key"
GOOGLE_MODEL = "gemini-2.5-flash"
```

The app supports typed requests, audio recording analyzed by Gemini, browser-native speech output, autumn-themed styling,
manual formula editing, AI formula application to sliders, solvent balancing, and CSV export.
Do not publish the API key.

