FROM python:3.10-slim

WORKDIR /app

# Cài dependencies 
RUN pip install --no-cache-dir fastapi==0.95.2 uvicorn[standard]==0.22.0 gunicorn==20.1.0
RUN pip install --no-cache-dir python-multipart redis httpx

# Copy code
COPY app/app.py .

EXPOSE 5000

CMD ["gunicorn", "app:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:80"]
