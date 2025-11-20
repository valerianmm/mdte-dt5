FROM python:3.11-slim

WORKDIR /app

COPY fetch_recent_data.py /app/

RUN pip install psycopg2-binary

CMD ["python", "fetch_recent_data.py"]
