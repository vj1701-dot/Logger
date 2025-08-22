# Multi-stage build for Next.js dashboard
FROM node:18-alpine as dashboard-builder

WORKDIR /app

# Copy dashboard
COPY dashboard/package.json dashboard/package-lock.json* ./
RUN npm ci

COPY dashboard/ .
RUN npm run build

# Build stage for Mini App
FROM node:18-alpine as miniapp-builder

WORKDIR /app

# Copy mini app
COPY miniapp/package.json miniapp/package-lock.json* ./
RUN npm ci

COPY miniapp/ .
RUN npm run build

# Final stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY src/ ./src/
COPY main.py .

# Copy built dashboard
COPY --from=dashboard-builder /app/.next ./dashboard/.next
COPY --from=dashboard-builder /app/public ./dashboard/public
COPY --from=dashboard-builder /app/package.json ./dashboard/

# Copy built mini app
COPY --from=miniapp-builder /app/dist ./miniapp/dist

# Create directories for static files
RUN mkdir -p /app/static

# Set environment variables
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

# Start the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]