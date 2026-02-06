#!/bin/bash
# Kill any process on port 8000
sudo kill -9 $(sudo lsof -t -i:8000) 2>/dev/null || true

# Create necessary directories
mkdir -p pdfs data vector_store templates static/{css,js,images}

# Copy templates if they exist in app/templates
if [ -d "app/templates" ]; then
    cp -r app/templates/* templates/ 2>/dev/null || true
fi

# Start the application
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level info
