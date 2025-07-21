FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1

# Start the FastAPI app (which mounts Flask and the bot)
CMD ["uvicorn", "combined_main:app", "--host", "0.0.0.0", "--port", "8080"]