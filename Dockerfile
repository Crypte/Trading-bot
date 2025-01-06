FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE 1  # Pas de fichiers .pyc
ENV PYTHONUNBUFFERED 1  # Sortie immédiatement affichée (pas de buffering)

RUN apt-get update && apt-get install -y \
    gcc \
    libssl-dev \
    libffi-dev \
    && apt-get clean


COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

WORKDIR /app
COPY bot.py /app/bot.py

CMD ["python", "main.py"]