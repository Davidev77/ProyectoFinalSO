# Contrato entre fases · Tríada

Fuente de verdad de los nombres que comparten las tres fases. Si algo de aquí cambia, se actualiza este archivo **en el mismo PR** y se avisa al equipo. Si el código y este archivo no coinciden, el error está en el código.

| Fase | Dueño | Rama | Tag al cerrar |
|---|---|---|---|
| 1. Base | Manuel | `fase1-base` | `v0.1-base` |
| 2. Monitoreo | Christian | `fase2-monitoreo` | `v0.2-monitoreo` |
| 3. Carga y cierre | Eddie | `fase3-carga` | `v0.3-cierre` |

## Servicios y puertos

Todos los servicios viven en **un solo** `docker-compose.yml` (proyecto `triada`) y en la red `so-net`.

| Servicio | Imagen | Puerto interno | Publicado al host | Fase |
|---|---|---|---|---|
| `backend1`, `backend2`, `backend3` | build `./backend` | 5000 | **No** | 1 |
| `nginx` | `nginx:1.27-alpine` | 80 · 8081 (`stub_status`) | `8080:80` (solo el 80) | 1 |
| `prometheus` | `prom/prometheus:<versión fija>` | 9090 | `9090:9090` | 2 |
| `nginx-exporter` | `nginx/nginx-prometheus-exporter:<versión fija>` | 9113 | No | 2 |
| `cadvisor` | `gcr.io/cadvisor/cadvisor:<versión fija>` | 8080 | `8082:8080` (opcional, para verlo en el navegador) | 2 |
| `grafana` | `grafana/grafana:<versión fija>` | 3000 | `3000:3000` | 2 |

Reglas: los backends y el 8081 de Nginx nunca se publican al host. Todos los servicios llevan `restart: unless-stopped`.

## Backend

**Variable de entorno:** `INSTANCE_ID` = `"1"`, `"2"` o `"3"` (por defecto `"sin-id"`).

**Rutas:**

| Ruta | Respuesta | Se mide |
|---|---|---|
| `GET /` | `200` `{"instancia": "1", "mensaje": "...", "contenedor": "<hostname>"}` | Sí |
| `GET /health` | `200` `{"estado": "ok", "instancia": "1"}` | No |
| `GET /metrics` | texto Prometheus | No |
| `GET /lento?ms=<n>` | `200` `{"instancia": "1", "espera_ms": n}` · defecto 500 · acotado a 0–2000 | Sí |

**Métricas** (registro por defecto de `prometheus_client`, un solo proceso de gunicorn):

| Métrica | Tipo | Etiquetas |
|---|---|---|
| `http_requests_total` | Counter | `instancia`, `metodo`, `ruta`, `codigo` |
| `http_request_duration_seconds` | Histogram (buckets por defecto) | `instancia`, `ruta` |

- `instancia` (en español) para no chocar con `instance`, que Prometheus agrega solo.
- `ruta` es la regla de Flask (`/`, `/lento`) o `otra` si la URL no existe.
- `codigo` es el código HTTP como texto (`"200"`, `"404"`, `"500"`).

Consultas que la Fase 2 ya usa:

```promql
sum by (instancia) (rate(http_requests_total[1m]))
histogram_quantile(0.95, sum by (le, instancia) (rate(http_request_duration_seconds_bucket[1m])))
sum by (instancia) (rate(http_requests_total{codigo=~"5.."}[1m]))
```

## Nginx

- `upstream backends` con `zone`, round robin, `max_fails=3 fail_timeout=10s` por servidor.
- Cabeceras hacia el backend: `Host`, `X-Real-IP`, `X-Forwarded-For`.
- Cabecera de respuesta: `X-Upstream` = `$upstream_addr` (IP:puerto del backend que respondió).
- Log `balanceo`: `estado=`, `instancia=` (`$upstream_addr`), `tiempo=`, `upstream_tiempo=`. Se ve con `docker compose logs nginx`.
- `stub_status` en `http://nginx:8081/stub_status`, solo dentro de `so-net`. La Fase 2 lo lee con `--nginx.scrape-uri=http://nginx:8081/stub_status`.

## Targets de Prometheus (Fase 2)

| Job | Targets |
|---|---|
| `prometheus` | `localhost:9090` |
| `backends` | `backend1:5000`, `backend2:5000`, `backend3:5000` (directo, **no** a través de Nginx) |
| `nginx` | `nginx-exporter:9113` |
| `cadvisor` | `cadvisor:8080` |

## Archivos por fase

| Fase | Archivos |
|---|---|
| 1 | `backend/`, `nginx/nginx.conf`, `docker-compose.yml` (backends, nginx, red), `.github/workflows/ci.yml` |
| 2 | `monitoring/prometheus/prometheus.yml`, `monitoring/grafana/provisioning/datasources/`, `monitoring/grafana/provisioning/dashboards/`, `monitoring/grafana/dashboards/infraestructura-so.json`, servicios y volúmenes `prometheus_data`, `grafana_data` en el compose |
| 3 | `k6/carga.js` |

## Recursos

Cada backend: `cpus: 0.5`, `mem_limit: 256m`. Si la Fase 3 necesita cambiarlo para un escenario, se documenta aquí.

## CI

Checks obligatorios en PR hacia `develop` y `main`: `calidad` y `humo`. Ningún PR se fusiona con el CI en rojo.
