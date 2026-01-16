#!/bin/bash
# Startup script for Railway deployment

# Railway provides PORT, default to 8000 if not set
export PORT=${PORT:-8000}

echo "Starting app on port $PORT"

# Start gunicorn
exec gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 app:app
