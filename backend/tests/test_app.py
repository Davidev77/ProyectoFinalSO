from prometheus_client import REGISTRY

from app import INSTANCE_ID, app

cliente = app.test_client()


def valor(metrica, etiquetas):
    # Lee el valor actual de una métrica; 0 si todavía no existe
    return REGISTRY.get_sample_value(metrica, etiquetas) or 0


def test_inicio_devuelve_la_instancia():
    respuesta = cliente.get("/")
    assert respuesta.status_code == 200
    datos = respuesta.get_json()
    assert datos["instancia"] == INSTANCE_ID
    assert datos["mensaje"] == f"Hola desde la instancia {INSTANCE_ID}"
    assert datos["contenedor"]


def test_inicio_devuelve_html_al_navegador():
    cabeceras = {"Accept": "text/html,application/xhtml+xml,*/*;q=0.8"}
    respuesta = cliente.get("/", headers=cabeceras)
    assert respuesta.status_code == 200
    assert respuesta.mimetype == "text/html"
    assert f"Instancia {INSTANCE_ID}" in respuesta.get_data(as_text=True)


def test_inicio_devuelve_json_a_curl_y_a_k6():
    # curl envía */*; k6 no envía Accept
    respuesta = cliente.get("/", headers={"Accept": "*/*"})
    assert respuesta.mimetype == "application/json"
    assert respuesta.get_json()["instancia"] == INSTANCE_ID


def test_health_responde_ok():
    respuesta = cliente.get("/health")
    assert respuesta.status_code == 200
    assert respuesta.get_json() == {"estado": "ok", "instancia": INSTANCE_ID}


def test_cada_peticion_suma_en_el_contador_y_en_la_duracion():
    etiquetas = {
        "instancia": INSTANCE_ID,
        "metodo": "GET",
        "ruta": "/",
        "codigo": "200",
    }
    antes = valor("http_requests_total", etiquetas)
    antes_duracion = valor(
        "http_request_duration_seconds_count", {"instancia": INSTANCE_ID, "ruta": "/"}
    )
    cliente.get("/")
    assert valor("http_requests_total", etiquetas) == antes + 1
    assert (
        valor(
            "http_request_duration_seconds_count",
            {"instancia": INSTANCE_ID, "ruta": "/"},
        )
        == antes_duracion + 1
    )


def test_metrics_y_health_no_se_cuentan():
    cliente.get("/metrics")
    cliente.get("/health")
    for ruta in ["/metrics", "/health"]:
        assert (
            valor(
                "http_requests_total",
                {
                    "instancia": INSTANCE_ID,
                    "metodo": "GET",
                    "ruta": ruta,
                    "codigo": "200",
                },
            )
            == 0
        )


def test_ruta_desconocida_se_cuenta_como_otra():
    respuesta = cliente.get("/no-existe")
    assert respuesta.status_code == 404
    assert (
        valor(
            "http_requests_total",
            {
                "instancia": INSTANCE_ID,
                "metodo": "GET",
                "ruta": "otra",
                "codigo": "404",
            },
        )
        >= 1
    )


def test_metrics_expone_el_formato_de_prometheus():
    texto = cliente.get("/metrics").get_data(as_text=True)
    assert "http_requests_total" in texto
    assert "http_request_duration_seconds_bucket" in texto


def test_lento_espera_lo_pedido():
    respuesta = cliente.get("/lento?ms=50")
    assert respuesta.status_code == 200
    assert respuesta.get_json() == {"instancia": INSTANCE_ID, "espera_ms": 50}


def test_lento_acota_valores_fuera_de_rango():
    assert cliente.get("/lento?ms=-5").get_json()["espera_ms"] == 0
    assert cliente.get("/lento?ms=abc").get_json()["espera_ms"] == 500
    assert cliente.get("/lento?ms=9999").get_json()["espera_ms"] == 2000
