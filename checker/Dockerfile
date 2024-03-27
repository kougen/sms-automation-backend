FROM python:3.10

LABEL org.opencontainers.image.source=https://github.com/kougen/sms-automation-backend

WORKDIR /app

COPY requirements.txt .
COPY dblib.py .

RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

CMD [ "python", "./main.py" ]

