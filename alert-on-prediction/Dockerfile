FROM python:3.11-slim

WORKDIR /app

# Install runtime deps for inference + MQTT + Postgres
# Pin to training-time versions to avoid pickle/sklearn/xgboost compatibility warnings.
RUN pip install --no-cache-dir \
    psycopg2-binary \
    paho-mqtt \
    numpy \
    scikit-learn==1.6.1 \
    xgboost==3.1.2 \
    joblib

# Default command; Python code will be bind-mounted at runtime
CMD ["python", "alert_on_prediction.py"]
