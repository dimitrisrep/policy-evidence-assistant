FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md requirements.lock ./
COPY src ./src
COPY data ./data
RUN pip install --no-cache-dir -r requirements.lock && pip install --no-cache-dir --no-deps . && useradd --create-home appuser
USER appuser
EXPOSE 8002
CMD ["uvicorn", "policy_evidence.api:app", "--host", "0.0.0.0", "--port", "8002"]
