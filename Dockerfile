# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for OCR and PDF processing
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create templates directory if not exists
RUN mkdir -p templates static

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Railway uses PORT environment variable
CMD gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120 app:app

# Expose port (Railway will override this)
EXPOSE 8000

# Run the application with gunicorn for production
CMD gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 app:app
