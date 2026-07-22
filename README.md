# AstroEconomics

A working astrology + astroeconomics app on top of the classic blockchain demo.

Open `http://localhost:5000` for the full screen:

- Daily cosmic market pulse (moon phase, planetary day, Mercury retrograde, aura score)
- Personal birth-chart briefing with financial horoscope and aligned watchlist
- Sector affinities and index picture for all twelve signs
- Seven-day sky forecast
- On-chain birth-chart registry (charts are mined into blocks automatically)

For entertainment and education only. Not financial advice.

## Quick start

```bash
pip install -r requirements.txt
python blockchain.py
```

Then visit [http://localhost:5000](http://localhost:5000).

With pipenv:

```bash
pip install pipenv
pipenv install
pipenv run python blockchain.py
```

## API

```bash
# Daily sky + market pulse
curl "http://localhost:5000/astroeconomics/pulse"

# Personalized briefing (optional on-chain registration)
curl -X POST http://localhost:5000/astroeconomics/briefing \
  -H "Content-Type: application/json" \
  -d '{"owner":"alice","birth_date":"1990-07-13","register":true}'

# Sun sign + market affinities
curl "http://localhost:5000/astrology/sign?birth_date=1990-07-13"

# Registered charts
curl http://localhost:5000/astrology/charts
```

Classic blockchain routes (`/mine`, `/chain`, `/transactions/new`, `/nodes/*`) still work.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Docker

```bash
docker build -t astroeconomics .
docker run --rm -p 80:5000 astroeconomics
```

Open [http://localhost](http://localhost).

## Project layout

- `astrology.py` — sun signs, moon phase, planetary day, horoscopes
- `astroeconomics.py` — sector maps, aura scores, watchlists, daily pulse
- `blockchain.py` — Flask API + blockchain registry
- `templates/index.html` + `static/` — the web app screen

## Original blockchain tutorial

This repository also contains the source for [Building a Blockchain](https://medium.com/p/117428612f46).
