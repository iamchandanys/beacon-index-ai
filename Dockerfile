# Use the official lightweight Python 3.10 image as the base
FROM python:3.10-slim

# Set environment variables to optimize Python behavior:
# - Prevent Python from writing .pyc files to disk
# - Ensure output is sent straight to terminal (useful for Docker logs)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container to /app
WORKDIR /app

# Update package lists, install essential build tools and poppler-utils for PDF processing,
# then clean up apt cache to keep the image size small
RUN apt-get update && apt-get install -y build-essential poppler-utils && rm -rf /var/lib/apt/lists/*

# Copy the main requirements file to the working directory
COPY requirements.txt .

# Copy environment variables file for application configuration
COPY .env .

# Copy all project files into the container's working directory
COPY . .

# Install Python dependencies from requirements.txt without caching to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8080 for the FastAPI application
EXPOSE 8080

# Start the FastAPI application using Uvicorn server, listening on all interfaces at port 8080
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
