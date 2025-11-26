FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY telegram_alert_service.py .

CMD ["python", "telegram_alert_service.py"]
