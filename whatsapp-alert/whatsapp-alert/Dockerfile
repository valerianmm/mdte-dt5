# Use lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Flask script
COPY whatsapp_alert_service.py .

# Expose port 5000
EXPOSE 5000

# Run the app
CMD ["python", "whatsapp_alert_service.py"]

