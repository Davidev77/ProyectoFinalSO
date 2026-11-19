FROM python:3.12-slim

WORKDIR /app

# Se copia primero requirements.txt: si el código cambia pero las dependencias no, Docker reutiliza la capa de pip (caché de capas)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Usuario sin privilegios (sin home ni shell): si alguien vulnera el proceso, no es root
RUN useradd --no-create-home --shell /usr/sbin/nologin triada
# DL3066 pide un UID numérico (pensado para Kubernetes); aquí se mantiene el nombre triada
# hadolint ignore=DL3066
USER triada

EXPOSE 5000

# 1 worker con 4 hilos: las métricas viven en memoria del proceso, así que un solo proceso mantiene contadores coherentes.
# El socket de control de gunicorn no se usa y necesita un home que el usuario no tiene
CMD ["gunicorn", "--workers", "1", "--threads", "4", "--no-control-socket", "--bind", "0.0.0.0:5000", "app:app"]
