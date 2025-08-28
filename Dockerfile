# Use official Python image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Update package lists, install build-essential and poppler-utils, then clean up apt cache to reduce image size
RUN apt-get update && apt-get install -y build-essential poppler-utils && rm -rf /var/lib/apt/lists/*

# Copy requirements file to /app folder
COPY requirements.txt .

# Copy .env file to /app folder
COPY .env .

# Copy project files to /app folder
COPY . .

# Install project dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the API port
EXPOSE 8080

# Start the FastAPI application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
