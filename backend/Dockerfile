# --- Stage 1: The Builder ---
# This stage installs dependencies into a virtual environment. It is larger
# but will be discarded, leaving only the necessary artifacts for the final image.
FROM python:3.10-slim as builder

WORKDIR /app

# Update package lists and install build-essential for any C extensions that may be needed.
# Clean up the apt cache afterwards to keep the layer small.
RUN apt-get update && \
    apt-get install -y build-essential && \
    rm -rf /var/lib/apt/lists/*

# Create a virtual environment to isolate dependencies.
RUN python -m venv /opt/venv

# Activate the virtual environment for subsequent commands in this stage.
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install requirements using the CPU-only index for torch.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# --- Stage 2: The Final, Lean Image ---
# This stage creates the final image by copying only what's needed
# from the builder stage, resulting in a much smaller size.
FROM python:3.10-slim

WORKDIR /app

# Copy the clean virtual environment from the builder stage.
COPY --from=builder /opt/venv /opt/venv

# Copy your application source code.
COPY . .

# Copy configuration files if they exist
COPY ./config/ ./config/ 2>/dev/null || true

# Activate the virtual environment for the running container.
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=/app

# Expose the port the app runs on to the outside world.
EXPOSE 8080

# Define the command to run your app when the container launches.
CMD ["python", "run_chatbot.py"]