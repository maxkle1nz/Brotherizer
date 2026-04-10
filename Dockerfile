FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    BROTHERIZER_HOST=0.0.0.0 \
    BROTHERIZER_PORT=5555

WORKDIR /app

COPY . /app

RUN python -m pip install --upgrade pip && \
    python -m pip install -e .

EXPOSE 5555

CMD ["brotherizer-api"]
