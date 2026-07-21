FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=8788
ENV CACHE_DIR=/data/cache
ENV CACHE_TTL_SEC=10800
EXPOSE 8788
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}
