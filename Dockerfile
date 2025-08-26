# Multi-stage Dockerfile for University Advising Chatbot
# Supports both cloud build and production deployment

# Stage 1: Build frontend
FROM node:18-alpine AS frontend-build
WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./
RUN npm ci

# Copy frontend source and build
COPY frontend/ ./
RUN npm run build

# Stage 2: Setup Python backend
FROM python:3.11-slim AS backend-setup

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy backend requirements
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Pre-download HuggingFace models to avoid runtime download issues
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en')" || echo "Model download failed, will handle at runtime"

# Stage 3: Production image
FROM python:3.11-slim AS production

# Install system dependencies for runtime
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy Python dependencies from backend-setup stage
COPY --from=backend-setup /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-setup /usr/local/bin /usr/local/bin

# Copy backend source code
COPY backend/ ./backend/

# Copy built frontend from frontend-build stage
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Copy configuration files 
COPY backend/config/ ./backend/config/

# Create necessary directories and set permissions
RUN mkdir -p /app/backend/vector_db /app/backend/embeddings /app/backend/data && \
    mkdir -p /home/appuser/.cache && \
    chown -R appuser:appuser /app /home/appuser/.cache

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Set environment variables
ENV PYTHONPATH=/app/backend
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV OAUTH_CLIENT_ID=""
ENV OAUTH_CLIENT_SECRET=""
ENV OAUTH_TENANT_ID=""
ENV SESSION_SECRET="fallback-secret-key"
ENV GROQ_API_KEY=""
ENV GROQ_API_URL="https://api.groq.com/openai/v1/chat/completions"
ENV GROQ_MODEL="llama3-70b-8192"

# Start the application with dynamic port binding
CMD ["sh", "-c", "cd backend && python run_chatbot.py"]