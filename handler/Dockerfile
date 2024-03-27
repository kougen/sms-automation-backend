FROM python:3.10

LABEL org.opencontainers.image.source=https://github.com/kougen/sms-automation-backend

WORKDIR /app

COPY requirements.txt .
COPY dblib.py .
COPY lib.py .
COPY store.py .
COPY routers/ routers/
COPY main.py .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5501"]

LABEL org.opencontainers.image.source=https://github.com/kougen/sms-automation-backend
