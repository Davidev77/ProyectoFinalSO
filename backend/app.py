import os
import socket
import time

from flask import Flask, Response, g, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

app = Flask(__name__)

# Identificador de esta instancia (lo define docker compose)
INSTANCE_ID = os.environ.get("INSTANCE_ID", "sin-id")

PETICIONES = Counter(
    "http_requests_total",
    "Total de peticiones HTTP",
    ["instancia", "metodo", "ruta", "codigo"],
)
DURACION = Histogram(
    "http_request_duration_seconds",
    "Duración de las peticiones HTTP en segundos",
    ["instancia", "ruta"],
)


@app.before_request
def marcar_inicio():
    g.inicio = time.perf_counter()


@app.after_request
def registrar_metricas(respuesta):
    # Prometheus y el healthcheck no se cuentan
    if request.path in ("/metrics", "/health"):
        return respuesta
    # Una ruta inexistente se agrupa como "otra" para no crear una serie por URL
    ruta = request.url_rule.rule if request.url_rule else "otra"
    PETICIONES.labels(INSTANCE_ID, request.method, ruta, str(respuesta.status_code)).inc()
    DURACION.labels(INSTANCE_ID, ruta).observe(time.perf_counter() - g.inicio)
    return respuesta


@app.route("/")
def inicio():
    return jsonify(
        instancia=INSTANCE_ID,
        mensaje=f"Hola desde la instancia {INSTANCE_ID}",
        contenedor=socket.gethostname(),
    )


@app.route("/health")
def health():
    return jsonify(estado="ok", instancia=INSTANCE_ID)


@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.route("/lento")
def lento():
    # Si ms no es un entero, Flask usa el defecto (500); luego se acota a 0-2000
    ms = request.args.get("ms", default=500, type=int)
    ms = max(0, min(ms, 2000))
    time.sleep(ms / 1000)
    return jsonify(instancia=INSTANCE_ID, espera_ms=ms)
