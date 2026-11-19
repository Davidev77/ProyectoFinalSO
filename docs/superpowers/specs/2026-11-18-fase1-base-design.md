# Diseño · Fase 1: base de la infraestructura (Tríada)

Fecha: 2026-11-18 · Dueño de la fase: Manuel Betancurt Pérez · Repo: https://github.com/Davidev77/ProyectoFinalSO

## 1. Intención

Proyecto final de Sistemas Operativos (UAO): infraestructura en Docker con Nginx como proxy inverso, 3 backends y monitoreo (Prometheus, Grafana, nginx-prometheus-exporter, cAdvisor). Se divide en tres fases y tres personas:

| Fase | Dueño | Qué entrega |
|---|---|---|
| 1. Base | Manuel | Backends Flask con métricas, Nginx con balanceo y `stub_status`, compose base, CI, CLAUDE.md, contrato, README e informe de su parte |
| 2. Monitoreo | Christian | Prometheus, exporter, cAdvisor, Grafana con provisioning y dashboard «Infraestructura SO» |
| 3. Carga y cierre | Eddie | k6 desde el host, resultados, consolidación del informe y PDF |

La Fase 1 es la base sobre la que trabajan los otros dos. Por eso lo más importante no es solo que funcione, sino que **los acuerdos (nombres, puertos, métricas, etiquetas) queden fijos y escritos** para que Christian y Eddie construyan encima sin preguntar ni romper nada.

Nombre de la app: **Tríada** (identificador técnico `triada`). *Decisión de Claude: tres instancias detrás de un balanceador; corto y fácil de recordar.* La carpeta local es `C:\proyectos\Triada\proyecto-final-so` y el repo `ProyectoFinalSO`.

## 2. Objetivos

1. Backend Python (Flask + `prometheus_client`) con `/`, `/health`, `/metrics`; instancia identificada por `INSTANCE_ID`; middleware que cuenta peticiones y mide su duración.
2. `requirements.txt` con versiones exactas (`==`).
3. Dockerfile según la especificación del usuario (ver §6.3).
4. `nginx.conf`: round robin a 3 backends, cabeceras de proxy, cabecera de respuesta con `$upstream_addr`, segundo `server` en 8081 con `stub_status` no publicado.
5. `docker-compose.yml` base: 3 backends desde el mismo Dockerfile, Nginx, red `so-net`, `restart: unless-stopped`.
6. Pipeline de CI en GitHub Actions que valida cada PR.
7. Documentación que avanza con el código: `CLAUDE.md`, `docs/CONTRATO.md`, README (esqueleto completo + secciones de Fase 1 llenas) y las secciones de Manuel en el informe.
8. **Un poco más que lo básico, sin llegar a robusto** (elegido por Manuel): usuario no-root en el contenedor, log de Nginx con instancia y tiempo, tolerancia a fallos en el upstream, límites de CPU y memoria por backend y una ruta `/lento` para generar latencia observable.

## 3. No objetivos (son de otras fases)

- Prometheus, Grafana, exporter, cAdvisor, volúmenes de datos (Fase 2).
- k6, pruebas de carga, PDF final del informe (Fase 3).
- Presentación en Canva (se hace aparte, fuera de Claude Code).

## 4. Anti-objetivos (fallaría aunque "funcione")

- Código que un ingeniero junior no entienda: abstracciones, decoradores propios, loops ingeniosos, metaprogramación.
- Más archivos de los necesarios.
- Publicar al host los backends o el puerto 8081.
- Más de un proceso de gunicorn (las métricas de `prometheus_client` quedarían partidas).
- Claude haciendo commits, o trabajando sobre `main` o `develop`.
- Cambiar un nombre del contrato sin actualizar `docs/CONTRATO.md` (rompe a Christian o a Eddie).
- Dejar la documentación para el final.

## 5. Restricciones

- Windows 11, Docker Desktop, PowerShell. Comandos de ejemplo en PowerShell (`curl.exe`, no el alias `curl`). El CI corre en Linux.
- Repo vacío en GitHub hoy: no existe ninguna rama.
- Flujo de ramas: `main` ← `develop` ← `fase1-base`. El PR de la fase va a `develop`; `develop` pasa a `main` solo en la entrega final.
- Claude no hace commits: al final de cada paso propone el mensaje y el usuario lo ejecuta.
- La fase termina solo cuando se cumplen todos los criterios de §9, revisados uno por uno con el usuario.

## 6. Diseño decidido

### 6.1 Estructura del repo

```
proyecto-final-so/
├── .github/workflows/ci.yml      CI: calidad + prueba de humo
├── backend/
│   ├── app.py                    Flask: rutas, middleware y métricas
│   ├── requirements.txt          dependencias con versión exacta
│   ├── Dockerfile
│   ├── .dockerignore
│   └── tests/test_app.py         pruebas con el cliente de Flask
├── nginx/nginx.conf              proxy inverso + stub_status
├── docs/
│   ├── CONTRATO.md               acuerdos entre fases (fuente de verdad)
│   ├── img/                      diagramas y capturas
│   └── superpowers/              specs/ y plans/
├── docker-compose.yml
├── .gitignore
├── .gitattributes                fin de línea LF (evita problemas Windows ↔ Linux)
├── CLAUDE.md
└── README.md
```

Reservado para otras fases (lo fija el contrato): `monitoring/prometheus/prometheus.yml`, `monitoring/grafana/provisioning/...`, `monitoring/grafana/dashboards/*.json` (Fase 2) y `k6/carga.js` (Fase 3).

### 6.2 Backend (`backend/app.py`, un solo archivo)

- `INSTANCE_ID` se lee una vez al arrancar: `os.environ.get("INSTANCE_ID", "sin-id")`.
- `GET /` → `200` JSON `{"instancia": "<id>", "mensaje": "Hola desde la instancia <id>", "contenedor": "<hostname>"}`. JSON para que k6 (Fase 3) pueda contar el reparto leyendo `instancia`.
- `GET /health` → `200` JSON `{"estado": "ok", "instancia": "<id>"}`.
- `GET /metrics` → salida de `prometheus_client.generate_latest()` con su `CONTENT_TYPE_LATEST`.
- `GET /lento?ms=<n>` → espera `n` milisegundos y responde `200` JSON `{"instancia": "<id>", "espera_ms": <n>}`. Por defecto 500; se acota entre 0 y 2000 (`request.args.get("ms", default=500, type=int)`, un valor no numérico usa el defecto). Sirve para que la latencia p95 del dashboard (Fase 2) y la prueba de carga (Fase 3) muestren algo distinto de una línea plana. Se mide como cualquier otra ruta.
- Métricas (nombres fijados por las consultas del dashboard de la Fase 2):
  - `http_requests_total` · Counter · etiquetas `instancia`, `metodo`, `ruta`, `codigo`.
  - `http_request_duration_seconds` · Histogram · etiquetas `instancia`, `ruta` · buckets por defecto.
  - Etiqueta en español `instancia` y no `instance`: Prometheus ya agrega `instance` (host:puerto del target) y chocarían.
  - `ruta` es la regla de Flask (`request.url_rule.rule`) o `"otra"` si no existe (un 404 con URL aleatoria no crea series nuevas).
  - `codigo` es el código HTTP como texto (`"200"`, `"500"`); permite el panel de errores 5xx.
- Middleware con `before_request` (guarda la hora en `flask.g`) y `after_request` (incrementa el contador y observa la duración). **No se miden `/metrics` ni `/health`**: Prometheus (cada 5 s) y el healthcheck de Docker inflarían la tasa de solicitudes.
- Se usa el registro por defecto de `prometheus_client`.

### 6.3 Dockerfile

`python:3.12-slim` → `WORKDIR /app` → `COPY requirements.txt .` → `RUN pip install --no-cache-dir -r requirements.txt` → `COPY app.py .` → `RUN useradd --no-create-home --shell /usr/sbin/nologin triada` → `USER triada` → `EXPOSE 5000` → `CMD ["gunicorn", "--workers", "1", "--threads", "4", "--bind", "0.0.0.0:5000", "app:app"]`.

*Decisión de Claude:* `--threads 4` mantiene un solo proceso (métricas correctas) pero permite atender varias peticiones a la vez; con 1 worker síncrono la prueba de carga de la Fase 3 haría cola y el p95 se dispararía. `.dockerignore` excluye `tests/`, `__pycache__/` y similares para que no entren a la imagen. El proceso corre con el usuario sin privilegios `triada`: si alguien explota la app, no es root dentro del contenedor.

### 6.4 Nginx (`nginx/nginx.conf`)

Imagen `nginx:1.27-alpine`, montado en `/etc/nginx/conf.d/default.conf:ro` (solo bloques `upstream` y `server`).

- `upstream backends { zone backends 64k; server backend1:5000 max_fails=3 fail_timeout=10s; ... }` (round robin, el método por defecto). `max_fails`/`fail_timeout`: tras 3 fallos seguidos Nginx deja de enviar tráfico a ese backend durante 10 s y luego lo vuelve a probar.
- `log_format balanceo '$remote_addr "$request" estado=$status instancia=$upstream_addr tiempo=$request_time upstream_tiempo=$upstream_response_time';` usado en `access_log /var/log/nginx/access.log balanceo;` (la imagen oficial lo envía a stdout): `docker compose logs nginx` muestra a qué backend fue cada petición y cuánto tardó. *Decisión de Claude:* `zone` hace que los procesos worker de Nginx compartan el turno del round robin; sin ella cada worker lleva su propia cuenta y 9 peticiones pueden repartirse 4/3/2 en vez de 3/3/3.
- `server` en 80: `proxy_pass http://backends;`, `proxy_set_header Host $host;`, `X-Real-IP $remote_addr`, `X-Forwarded-For $proxy_add_x_forwarded_for`, `add_header X-Upstream $upstream_addr always;`, `proxy_connect_timeout 2s;` y `proxy_next_upstream error timeout http_502 http_503;` (si un backend cae, Nginx reintenta la petición en el siguiente y el cliente no ve el error; lo usa la demo de fallo de la Fase 3).
- `server` en 8081: `location /stub_status { stub_status; }`, `access_log off`. Solo accesible dentro de `so-net` (lo lee `nginx-exporter` en la Fase 2).
- Comentarios cortos en español explicando cada bloque.

### 6.5 `docker-compose.yml`

- `name: triada`.
- Bloque común con ancla YAML (`x-backend: &backend`) que comparte `build: ./backend`, `restart`, `networks` y `healthcheck`; cada servicio `backend1..3` lo reutiliza y solo cambia `INSTANCE_ID`. *Decisión de Claude:* evita repetir tres veces el mismo bloque; es un patrón estándar de Compose y se explica con un comentario de una línea.
- Healthcheck de los backends con Python del propio contenedor (`urllib` contra `/health`), sin instalar curl.
- Límites por backend en el bloque común: `cpus: 0.5` y `mem_limit: 256m`. Dan un techo real a las gráficas de cAdvisor y permiten que la prueba de carga encuentre un cuello de botella concreto.
- `nginx`: `ports: "8080:80"` (único puerto publicado), volumen de `nginx.conf`, `depends_on` con `condition: service_healthy` en los tres backends.
- Red `so-net` (bridge) en todos los servicios. `restart: unless-stopped` en todos.
- Sin volúmenes de datos en esta fase.
- Las fases 2 y 3 agregan sus servicios a **este mismo** `docker-compose.yml` (el enunciado pide un solo archivo), así que la red se referencia simplemente como `so-net`.
- Nombres reservados para la Fase 2 (los fija el contrato): `prometheus:9090`, `nginx-exporter:9113`, `cadvisor:8080`, `grafana:3000`.

### 6.6 CI (`.github/workflows/ci.yml`)

Se dispara en `pull_request` hacia `develop` y `main`, y en `push` a `develop`. Dos jobs:

1. **calidad**: Python 3.12 → instala `requirements.txt` + `pytest` y `ruff` con versión fija → `ruff check backend` → `pytest backend/tests` → hadolint sobre `backend/Dockerfile` (acción oficial con versión fija).
2. **humo** (depende de calidad): `docker compose up -d --build --wait` → 9 peticiones a `http://localhost:8080/` y comprobar que aparecen las 3 instancias → `/health` y `/metrics` responden → `stub_status` responde desde dentro del contenedor de Nginx → `docker compose down`.

Cada paso con nombre en español. Sin publicar imágenes ni desplegar.

### 6.7 Pruebas (`backend/tests/test_app.py`)

Con el cliente de pruebas de Flask, sin Docker: `/` devuelve la instancia; `/health` responde 200; tras una petición a `/`, `/metrics` contiene `http_requests_total` con `instancia`; las peticiones a `/metrics` y `/health` no se cuentan. Pocas pruebas, legibles.

### 6.8 Documentación que avanza con el código

- **Antes de correr el prompt** (preparado en esta conversación y aprobado por Manuel): `CLAUDE.md`, `docs/CONTRATO.md` y el esqueleto completo del README siguiendo el estilo de los ejemplos del usuario (`SISTEMAS OPERATIVOS\CLAUDE.md` y `SISTEMAS OPERATIVOS\README.md`: encabezado centrado con badges, tabla de estado, diagrama mermaid, puesta en marcha numerada, tabla de comandos, autores). Se preparan en `preparacion-fase1\` y el paso 0 los copia al repo; el prompt construye contra ellos y comprueba cada nombre del código contra el contrato.
- **En cada paso del prompt**: se actualiza la sección del README que corresponde y la sección del informe en el documento del paso 0. Las secciones de las fases 2 y 3 quedan con «Pendiente · Fase 2 (Christian)» / «Pendiente · Fase 3 (Eddie)».
- **Informe**: Google Doc «Informe Triada» (https://docs.google.com/document/d/1MPO4G44Ge-d0srosCop8E2RMMqkFC38_iHEAW0BXBCg/edit), ya con portada y secciones de los tres en APA 7 (Times New Roman 12, títulos en negrita y negro, interlineado 1,15). Se escribe con el conector de Google Docs reemplazando el texto gris «Pendiente · Manuel …» de cada sección; no se tocan saltos de página ni el diseño de página (eso lo decide Manuel). El prompt escribe cada sección directamente en ese documento, no en un borrador Markdown. Secciones de Manuel: arquitectura con diagrama, Dockerfile, Nginx como proxy inverso, compose (backends, Nginx, red), y para cada una las decisiones (por qué Flask, por qué round robin, por qué los backends no se exponen al host, por qué 1 worker). Donde va una captura se deja `[CAPTURA: qué mostrar y con qué comando]`.

### 6.9 Roles y skills (los usa el prompt)

| Rol | Hace | Skills |
|---|---|---|
| Principal DevOps / Platform Engineer (agente principal) | Diseña, coordina subagentes, Docker, Nginx, compose | `superpowers:writing-plans`, `superpowers:subagent-driven-development`, `docker-compose-patterns`, `superpowers:verification-before-completion` |
| Senior Python Backend Engineer | `app.py`, middleware, tests | `superpowers:test-driven-development` |
| Senior SRE / Observability Engineer | Revisa métricas contra el contrato y las consultas de la Fase 2 | `superpowers:verification-before-completion` |
| QA Automation Engineer | Verifica balanceo, fallos, puertos cerrados; capturas | `testing-load-balancers`, `playwright-cli` |
| Infrastructure Architect | Revisa diseño y riesgos, aprueba antes del PR | `superpowers:requesting-code-review` |
| Senior CI/CD Engineer | Escribe el CI y revisa cada rama antes del PR | `ci-cd-and-automation`, `github-actions-templates`, `superpowers:finishing-a-development-branch` |
| Documentación (cualquier rol al cerrar su paso) | README e informe | `create-readme`, `humanizer` |

## 7. Enfoques considerados

**Rol del CI/CD Engineer**
- A. Solo revisor con checklist: lo más simple, pero nada obliga a cumplirla en GitHub.
- **B. Pipeline mínimo en GitHub Actions (elegido por Manuel)**: dos archivos cortos; protege la base en los PRs de las fases 2 y 3 y deja evidencia para el informe.
- C. Pipeline con publicación de imágenes y despliegue: no hay dónde desplegar.

**Dónde nacen los acuerdos (CLAUDE.md, contrato, README)**
- **Escritos y aprobados antes de correr el prompt (decisión de Claude)**: el prompt solo construye y no improvisa nombres; los compañeros leen el contrato desde el primer día.
- Generados por el prompt: más corto de preparar, pero los acuerdos quedarían a criterio del agente.

## 8. Paso 0 (lo hace Manuel antes del prompt)

Crear la carpeta, clonar, copiar los archivos preparados, primer commit en `main`, crear `develop` y `fase1-base`, y abrir Claude Code en la carpeta con un prompt corto de arranque. El prompt empieza con el paso 0 ya hecho y trabaja en `C:\proyectos\Triada\proyecto-final-so` (la carpeta `preparacion-fase1` es solo el borrador).

**Permisos del repo:** Manuel no es administrador de `Davidev77/ProyectoFinalSO`. Se implementa todo igual y Manuel le pide al dueño del repo dos cosas: invitar a Christian y Eddie y crear la regla de protección de `develop` y `main` que exige el CI en verde (**sin aprobaciones obligatorias**). Mientras no exista la regla, el CI corre igual pero no bloquea el merge.

**Git:** Claude no ejecuta ninguna operación que escriba en git o GitHub (commit, push, tag, abrir PR). Al cerrar cada paso propone el comando y se detiene hasta que Manuel lo ejecute. *Decisión de Claude: lectura conservadora de «no hagas commits».* Los criterios 9 y 11 son puntos de parada donde Manuel actúa.

## 9. Criterios de terminado de la Fase 1

1. Desde un clon limpio, `docker compose up -d --build` levanta 4 contenedores y los 3 backends quedan `healthy`.
2. `http://localhost:8080/` responde desde el navegador del host.
3. 9 peticiones seguidas se reparten 3 / 3 / 3 entre las instancias (JSON `instancia` y cabecera `X-Upstream`).
4. Las 3 instancias responden `/health` y exponen en `/metrics` `http_requests_total` y `http_request_duration_seconds` con la etiqueta `instancia`; `/metrics` y `/health` no se cuentan.
5. `stub_status` responde dentro de la red (`docker compose exec nginx wget -qO- http://localhost:8081/stub_status`) y **no** responde desde el host; los backends tampoco son accesibles desde el host.
6. Con un backend detenido (`docker compose stop backend2`) Nginx sigue respondiendo con los otros dos, sin errores para el cliente.
6b. Extras: `docker compose exec backend1 whoami` → `triada`; `docker compose logs nginx` muestra `instancia=` y `tiempo=`; `docker stats --no-stream` muestra el límite de 256 MiB en los backends; `/lento?ms=300` tarda unos 300 ms y `/lento?ms=9999` se acota a 2000.
7. `docker compose down` y `up` vuelve a dejar todo funcionando.
8. `requirements.txt` solo con `==`; Dockerfile cumple §6.3; ruff, pytest y hadolint sin errores.
9. CI en verde en el PR `fase1-base` → `develop`.
10. `CLAUDE.md`, `docs/CONTRATO.md`, README (secciones de Fase 1 llenas, el resto marcado como pendiente) y las secciones de Manuel escritas en el documento del informe, con decisiones y marcadores de captura.
11. Revisión del Infrastructure Architect y del CI/CD Engineer sin pendientes; PR con CI en verde fusionado en `develop` (sin aprobación obligatoria); tag `v0.1-base`.

## 10. A criterio del constructor

- Versiones exactas de Flask, gunicorn, prometheus-client, pytest, ruff y hadolint (estables y verificadas al momento).
- Texto exacto de comentarios, mensajes y nombres de pasos del CI.
- Detalle de las pruebas, mientras cubran §6.7.
- Orden fino de los pasos dentro del plan.
