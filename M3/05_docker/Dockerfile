FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY 03_debounce ./03_debounce
COPY 04_actuator_fires ./04_actuator_fires
COPY 06_end_to_end_latency ./06_end_to_end_latency
CMD ["python", "04_actuator_fires/actuator_simulator.py", "--status", "OPEN"]
