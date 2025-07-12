FROM python:3.11-slim

# Create a non-root user
RUN adduser --disabled-password --gecos '' celeryuser

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /tochly

COPY . .
COPY requirements.txt .

RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

USER celeryuser

CMD ["celery", "-A", "tochly", "worker", "--loglevel=info"]
