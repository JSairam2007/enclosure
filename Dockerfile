# M3 Docker: build and run from a cold boot.
#   docker build -t edgeai .
#   docker run --rm --restart unless-stopped -v "%cd%/models:/app/models" -v "%cd%/clips:/app/clips" edgeai
# Linux with hardware: add --device /dev/ttyUSB0 and --device /dev/video0.
# opencv-python needs libGL even when headless, hence libgl1.
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "M3/decide_act.py", "--model", "models/best_int8.onnx", "--sources", "clips/demo.mp4", "--headless", "--loop"]
