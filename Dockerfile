FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory (will be mounted as volume in production)
RUN mkdir -p /data && chmod 777 /data

# Set environment variable for data directory
ENV DATA_DIR=/data

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "start.py"]
