# AstroEconomics

A working astrology + astroeconomics app on top of the classic blockchain demo.

## Run

```bash
pip install -r requirements.txt
python blockchain.py
```

Open **http://127.0.0.1:5000** (or use Cursor **Ports** → port `5000` → Open in Browser).

You should see:

- Today's market pulse (aura, moon, leading sign)
- A birth-date form (no JavaScript required)
- Watchlist, index picture, 7-day forecast
- On-chain chart registry

If the page is blank, hard-refresh and confirm the terminal shows:
`Running on http://127.0.0.1:5000`

A static snapshot is also at `astroeconomics.html` — open that file directly to verify the UI.

## API

```bash
curl http://127.0.0.1:5000/health
curl http://127.0.0.1:5000/astroeconomics/pulse
curl -X POST http://127.0.0.1:5000/astroeconomics/briefing \
  -H "Content-Type: application/json" \
  -d '{"owner":"alice","birth_date":"1990-07-13","register":true}'
```

## Tests

```bash
python -m unittest discover -s tests -v
```

Entertainment/education only. Not financial advice.
