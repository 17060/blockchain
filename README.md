# AstroEconomics

A working astrology + astroeconomics app on top of the classic blockchain demo.

## Run

```bash
pip install -r requirements.txt
python blockchain.py
```

Open the app URL printed when the server starts (or the public tunnel URL if one was created).

You should see:

- Today's market pulse (aura, moon, leading sign)
- A birth-date form (no JavaScript required)
- Watchlist, index picture, 7-day forecast
- On-chain chart registry

A static snapshot is also at `astroeconomics.html` — open that file in any browser to view the UI offline.

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

## Original blockchain tutorial

This repository also contains the source for [Building a Blockchain](https://medium.com/p/117428612f46). Book materials: https://github.com/dvf/blockchain-book
