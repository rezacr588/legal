FROM python:3.11-slim

WORKDIR /app

# Copy backend files (legal-dashboard mounted as volume in docker-compose.yml)
COPY backend /app/backend

# Install dependencies
RUN pip install --no-cache-dir \
    flask \
    flask-cors \
    flask-sqlalchemy \
    polars \
    pyarrow \
    groq \
    cerebras_cloud_sdk \
    tiktoken \
    huggingface_hub \
    psycopg2-binary \
    cryptography

# Expose port
EXPOSE 5000

# Set working directory to backend
WORKDIR /app/backend

# Run the application
CMD ["python", "app.py"]
