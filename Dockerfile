FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -e ".[dev]"
CMD ["pytest", "tests/", "-v", "--cov=replay_harness", "--cov-report=term-missing", "--cov-fail-under=90"]
