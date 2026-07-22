FROM python:3.12-alpine

WORKDIR /app

# Install dependencies.
ADD requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt \
    && adduser -D -H appuser

# Add actual source code.
ADD astrology.py astroeconomics.py blockchain.py ui.py /app/
ADD tests /app/tests
RUN chown -R appuser:appuser /app

USER appuser
EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=2)"

CMD ["python", "blockchain.py", "--port", "5000"]
