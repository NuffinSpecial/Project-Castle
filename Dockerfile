FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# Use a persistent volume (host-specific) by setting CASTLE_DATA_DIR.
# Render blueprint mounts a disk at /var/data and sets CASTLE_DATA_DIR=/var/data.
ENV CASTLE_DATA_DIR=/var/data

EXPOSE 10000

CMD ["gunicorn", "web_app:app", "--bind", "0.0.0.0:10000", "--workers", "2", "--threads", "4", "--timeout", "120"]

