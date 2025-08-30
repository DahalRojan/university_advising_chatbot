# Optimized Multi-stage Dockerfile for University Advising Chatbot
# Designed for Google Cloud Run with fast startup and small size

# Stage 1: Build frontend
FROM node:18-alpine AS frontend-build
WORKDIR /app/frontend

# Copy package files first (better caching)
COPY frontend/package*.json ./
RUN npm ci --only=production

# Copy source and build
COPY frontend/ ./
RUN npm run build

# Stage 2: Python dependencies
FROM python:3.11-slim AS python-deps
WORKDIR /app

# Install system dependencies (minimal for faster builds)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python requirements
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir --user -r requirements.txt

# Pre-download critical ML models to avoid cold start delays
RUN python -c "
import os
try:
    from sentence_transformers import SentenceTransformer
    print('Downloading BGE-large model for faster startup...')
    # Download the large model you're actually using
    SentenceTransformer('BAAI/bge-large-en-v1.5')
    print('BGE-large model download completed')
    # Also download the cross-encoder for reranking
    try:
        from sentence_transformers import CrossEncoder
        CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        print('Cross-encoder model download completed')
    except Exception as ce:
        print(f'Cross-encoder download failed: {ce}')
except Exception as e:
    print(f'Model pre-download failed: {e}')
    print('Models will be downloaded at runtime (slower cold starts)')
" 2>/dev/null || echo "Pre-download skipped"

# Stage 3: Final production image
FROM python:3.11-slim AS production

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Install minimal runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get purge -y --auto-remove

# Copy Python packages from deps stage
COPY --from=python-deps /root/.local /home/appuser/.local

# Copy backend source code
COPY backend/ ./backend/

# Copy built frontend
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Create necessary directories and set permissions
RUN mkdir -p /app/backend/embeddings /app/backend/data \
    && chown -R appuser:appuser /app /home/appuser

# Switch to non-root user
USER appuser

# Set environment variables for production
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app/backend
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV PYTHONDONTWRITEBYTECODE=1

# Expose port
EXPOSE 8080

# Add health check for Cloud Run
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Create startup script for model warmup + server start
RUN echo '#!/bin/bash\n\
echo "🚀 Starting University Advising Chatbot..."\n\
cd /app/backend\n\
python startup_warmup.py\n\
if [ $? -eq 0 ]; then\n\
  echo "✅ Warmup successful, starting server..."\n\
else\n\
  echo "⚠️ Warmup had issues, starting server anyway..."\n\
fi\n\
exec python -m uvicorn core.api:app --host 0.0.0.0 --port 8080 --workers 1\n\
' > /app/start.sh && chmod +x /app/start.sh

# Optimize startup command with warmup
CMD ["/app/start.sh"]