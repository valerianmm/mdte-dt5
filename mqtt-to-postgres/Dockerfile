FROM python:3.11
WORKDIR /app

COPY mqtt_postgres_ingestor.py /app/

RUN pip install paho-mqtt psycopg2 

CMD ["python", "mqtt_postgres_ingestor.py"]
