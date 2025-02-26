# 1. Use an official Python base image
FROM python:3.10-slim

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*
    
# 2. Set a working directory inside the container
WORKDIR /app

# 3. Copy only requirements first, to leverage Docker's layer caching
COPY requirements.txt .

# 4. Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the entire project
COPY . .

# 6. Expose port 8000 (FastAPI default)
EXPOSE 8000

# 7. Run the server
# If you want to use gunicorn/uvicorn in production, you might do:
CMD ["uvicorn", "service.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
