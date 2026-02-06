FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir fastapi uvicorn requests pydantic pyyaml

ENV ZENODO_ENV=sandbox
ENV MATVERSE_PAPERS_REPO=git@github.com:matverse-acoa/papers.git
ENV MATVERSE_PAPERS_PATH=2026
ENV MATVERSE_PUBLISH=1

CMD ["uvicorn", "matverse_runtime.main:app", "--host", "0.0.0.0", "--port", "8000"]
