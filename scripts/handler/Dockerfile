FROM python:3.10

LABEL org.opencontainers.image.source=https://github.com/kougen/csikos-sms-automation

WORKDIR /app

COPY requirements.txt .
COPY dblib.py .
COPY lib.py .
COPY test_router.py .
COPY send_router.py .
COPY groups_router.py .
COPY store.py .

RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5501"]

