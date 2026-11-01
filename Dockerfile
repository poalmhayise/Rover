FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /app/data && useradd -r -u 10001 hired && chown -R hired:hired /app/data
USER hired
ENV HIRED_HOST=0.0.0.0 HIRED_PORT=8080 HIRED_DATA_DIR=/app/data PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["python", "server.py"]
