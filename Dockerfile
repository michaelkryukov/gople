FROM python:3.9.18-bullseye
# FROM mcr.microsoft.com/playwright:v1.37.0-jammy

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN python3 -m pip install --no-cache-dir --upgrade pip && \
    python3 -m pip install --no-cache-dir --upgrade -r /app/requirements.txt && \
    python3 -m playwright install --with-deps chromium

COPY ./templates /app/templates
COPY ./gople /app/gople

CMD ["uvicorn", "gople.application:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
