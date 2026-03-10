ARG BASE_IMAGE=python:3.11-slim
FROM ${BASE_IMAGE}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY online/infer_service/requirements.txt /workspace/online/infer_service/requirements.txt
RUN pip install --no-cache-dir -r /workspace/online/infer_service/requirements.txt

COPY . .

CMD ["python", "online/infer_service/inference.py"]
