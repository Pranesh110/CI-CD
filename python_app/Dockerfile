
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements first for Docker layer caching
COPY python_app/it-incident-desk-app/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY python_app/it-incident-desk-app/ .

# Python environment settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Application port
EXPOSE 8000

# Start FastAPI application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
