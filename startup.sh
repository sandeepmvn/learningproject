#!/bin/bash
# Startup script for Azure App Service

# Install dependencies if needed
pip install --no-cache-dir -r requirements.txt

# Create data directory for SQLite database
mkdir -p /home/data

# Start the application
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
