FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DEVICE=cpu HOST=0.0.0.0
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir torch==2.11.0 torchvision==0.26.0 --index-url https://download.pytorch.org/whl/cpu && pip install --no-cache-dir -r requirements.txt
COPY backend ./backend
COPY scripts/serve.py ./scripts/serve.py
RUN useradd --create-home app && chown -R app:app /app
USER app
EXPOSE 8765
CMD ["python", "scripts/serve.py"]
