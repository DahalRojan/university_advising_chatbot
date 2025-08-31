# Clean, optimized Dockerfile for University Advising Chatbot
# Designed for Google Cloud Run with fast startup

# Stage 1: Build frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend

# Copy package files
COPY frontend/package*.json ./

# Install ALL dependencies (including dev dependencies needed for build)
RUN npm ci

# Copy frontend source and build
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend with model pre-loading
FROM python:3.11-slim AS backend-deps

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Python requirements
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download ML models (single line to avoid Docker parser issues)
RUN python -c "from sentence_transformers import SentenceTransformer, CrossEncoder; SentenceTransformer('BAAI/bge-large-en-v1.5'); CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2'); print('Models downloaded successfully')" || echo "Models will download at runtime"

# Stage 3: Final production image
FROM python:3.11-slim AS production

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy Python packages from backend-deps stage
COPY --from=backend-deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-deps /usr/local/bin /usr/local/bin

# Copy backend source code
COPY backend/ ./backend/

# Copy built frontend from frontend-build stage
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Copy model cache from backend-deps stage
COPY --from=backend-deps /root/.cache /home/appuser/.cache

# Create necessary directories and set permissions
RUN mkdir -p /app/backend/embeddings /app/backend/data \
    && chown -R appuser:appuser /app /home/appuser

# Switch to non-root user
USER appuser

# Set environment variables
ENV PYTHONPATH=/app/backend
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8080

# Expose port
EXPOSE 8080

# Health check with extended startup time for model loading
HEALTHCHECK --interval=30s --timeout=15s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Simple, reliable startup command
CMD ["python", "-m", "uvicorn", "core.api:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]