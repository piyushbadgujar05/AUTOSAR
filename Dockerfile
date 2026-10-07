FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specifications
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Create required runtime directories
RUN mkdir -p data/uploads data/processed data/chroma data/sample_documents

# Generate sample documents during build
RUN python scripts/generate_sample_pdfs.py

# Expose ports: 8000 for FastAPI, 8501 for Streamlit
EXPOSE 8000 8501

ENV PYTHONPATH=/app
ENV USE_FAST_EMBEDDINGS=1

# Default command
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 & streamlit run frontend/streamlit_app.py --server.port 8501 --server.address 0.0.0.0"]
