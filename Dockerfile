FROM python:3.12-slim

WORKDIR /app

COPY requirements-ai.txt requirements-ai.txt
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ai ai
COPY src src
COPY .env.example .env.example

EXPOSE 8000

CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
