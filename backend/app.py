import os
import socket
import time

from flask import Flask, Response, g, jsonify, render_template, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

app = Flask(__name__)

# Identificador de esta instancia (lo define docker compose)
INSTANCE_ID = os.environ.get("INSTANCE_ID", "sin-id")

# Momento en que arrancó esta instancia (para mostrar cuánto lleva encendida)
INICIO = time.time()

# Un color por instancia: así, al recargar la página, se nota el cambio de backend
COLORES = {"1": "#2563eb", "2": "#059669", "3": "#d97706"}

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


# Utils
def total_atendidas():
    # Suma todas las series de http_requests_total de esta instancia
    total = 0
    for familia in PETICIONES.collect():
        for muestra in familia.samples:
            if muestra.name == "http_requests_total":
                total += muestra.value
    return int(total)


def formatear_duracion(segundos):
    minutos, segundos = divmod(int(segundos), 60)
    horas, minutos = divmod(minutos, 60)
    return f"{horas} h {minutos} min {segundos} s"


# Middlewares
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
    PETICIONES.labels(
        INSTANCE_ID, request.method, ruta, str(respuesta.status_code)
    ).inc()
    DURACION.labels(INSTANCE_ID, ruta).observe(time.perf_counter() - g.inicio)
    return respuesta


@app.route("/")
def inicio():
    datos = {
        "instancia": INSTANCE_ID,
        "mensaje": f"Hola desde la instancia {INSTANCE_ID}",
        "contenedor": socket.gethostname(),
    }

    # Un navegador pide HTML; curl, k6 y el CI no, y siguen recibiendo el JSON del contrato.
    formato = request.accept_mimetypes.best_match(["application/json", "text/html"])
    if formato == "text/html":
        return render_template(
            "inicio.html",
            **datos,
            color=COLORES.get(INSTANCE_ID, "#6b7280"),
            colores=COLORES,
            inicio=int(INICIO),
            activa=formatear_duracion(time.time() - INICIO),
            # El contador suma al terminar la petición (after_request): esta aún no está, por eso el + 1
            atendidas=total_atendidas() + 1,
            # Nginx no reenvía el puerto en Host: se arma el enlace con el mismo host del navegador
            host=request.host.split(":")[0],
        )

    return jsonify(datos)


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
