FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/task_master_server.py ./app.py

# Expose port
EXPOSE 8000

# Set environment variables
ENV PORT=8000
ENV LOG_LEVEL=debug

# Run the application with proxy headers enabled
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
