FROM python:3.12-alpine

WORKDIR /app

# Install dependencies.
ADD requirements.txt /app
RUN cd /app && \
    pip install -r requirements.txt

# Add actual source code.
ADD astrology.py astroeconomics.py blockchain.py /app/
ADD templates /app/templates
ADD static /app/static
ADD tests /app/tests

EXPOSE 5000

CMD ["python", "blockchain.py", "--port", "5000"]
