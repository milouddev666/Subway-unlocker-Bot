FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY pyproject.toml README.md /app/
COPY subway_bot /app/subway_bot
COPY data /app/data

RUN pip install --no-cache-dir .

RUN chown -R app:app /app

USER app

CMD ["python", "-m", "subway_bot"]
