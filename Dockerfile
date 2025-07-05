FROM python:3.13-slim

WORKDIR /app

# Install Poetry and Git
RUN apt-get update && apt-get install -y git

# Copy files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
