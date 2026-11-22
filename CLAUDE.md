# Tríada

Infraestructura en Docker: Nginx como proxy inverso reparte con round robin entre 3 backends Flask que exponen métricas para Prometheus; Prometheus, Grafana, nginx-exporter y cAdvisor monitorean todo. Proyecto final de Sistemas Operativos · UAO · 2026. Repo: `Davidev77/ProyectoFinalSO`.

**Estado:** Fase 1 (base, Manuel) y Fase 2 (monitoreo, Christian) terminadas y fusionadas en `develop` (tags `v0.1-base` y `v0.2-monitoreo`). Fase 3 (pruebas de carga y cierre, Eddie) en curso en la rama `fase3-carga`.

## Comandos (PowerShell, en la raíz)

- `docker compose up -d --build --wait`: levanta todo y espera a que los backends estén `healthy`
- `docker compose ps` · `docker compose logs nginx --tail 20` · `docker compose down`
- `1..9 | ForEach-Object { (curl.exe -s http://localhost:8080/ | ConvertFrom-Json).instancia }`: ver el reparto (cada instancia 3 veces en 9 peticiones)
- `cd backend; python -m pytest tests -v`: pruebas (con `.venv` activo)
- `cd backend; ruff check .`: estilo y errores (con `.venv` activo)
- `Get-Content backend/Dockerfile | docker run --rm -i hadolint/hadolint:v2.15.1`: revisar el Dockerfile
- En PowerShell usa `curl.exe`, no `curl` (es un alias de otro comando).

## Stack

Python 3.12 · Flask · prometheus_client · gunicorn (1 worker, 4 hilos) · Nginx 1.27-alpine · Docker Compose · GitHub Actions. Versiones exactas (`==`). No agregar dependencias sin acordarlo.

## Estructura

```
backend/        app.py (rutas, middleware, métricas) · templates/inicio.html · requirements.txt · Dockerfile · tests/
nginx/          nginx.conf (upstream, proxy, log de balanceo, stub_status en 8081)
monitoring/     Fase 2: prometheus/ y grafana/ (provisioning y dashboards)
k6/             Fase 3: carga.js · resultados/ (ignorada por Git)
docs/           CONTRATO.md · img/
.github/        workflows/ci.yml
docker-compose.yml · README.md · CLAUDE.md
```

## Contrato

La fuente de verdad es `docs/CONTRATO.md`: servicios, puertos, red `so-net`, rutas, métricas (`http_requests_total`, `http_request_duration_seconds`) y etiquetas (`instancia`, `metodo`, `ruta`, `codigo`). Otras personas construyen sobre esos nombres: no los cambies sin actualizar el contrato en el mismo PR y avisar.

## Ramas y git

- `main` ← `develop` ← `faseN-*`. Los PR van a `develop`; `develop` pasa a `main` solo en la entrega final. Nunca trabajar directo en `main` ni `develop`.
- **Claude no hace commit, push, tag ni abre PR.** Al terminar un paso muestra los comandos exactos y se detiene hasta que Manuel confirme.
- Mensajes de commit en español con prefijo: `feat(backend):`, `build(backend):`, `feat(infra):`, `ci:`, `docs:`, `fix:`.
- El CI (`calidad` y `humo`) debe quedar en verde antes de fusionar.

## Reglas del código

- Simple y legible para un ingeniero junior: sin abstracciones propias, sin decoradores propios, sin loops ingeniosos. Si hay dos formas, la más obvia.
- Comentarios breves en español, solo donde aporten. Identificadores en español; los nombres de métricas siguen la convención de Prometheus en inglés.
- No crear archivos que no estén en la estructura sin acordarlo.
- De la app solo se publica `8080:80` de Nginx. Del monitoreo se publican Prometheus (`9090`), Grafana (`3000`) y cAdvisor (`8082`). Backends (`5000`) y `stub_status` (`8081`) nunca.
- gunicorn siempre con `--workers 1`: con varios procesos las métricas de `prometheus_client` se parten y salen mal.
- `/metrics` y `/health` no se cuentan en las métricas.

## Documentación

- **Informe:** Google Doc «Informe Triada» → https://docs.google.com/document/d/1MPO4G44Ge-d0srosCop8E2RMMqkFC38_iHEAW0BXBCg/edit. Cada sección tiene un texto gris «Pendiente · <dueño> …»: se reemplaza solo el de la sección propia, en Times New Roman 12 negro, con sangría de primera línea como el resto. Usar la skill `anthropic-skills:google-workspace` antes de editarlo. No tocar saltos de página, márgenes ni diseño de página: eso lo decide Manuel. Las capturas pendientes se marcan `[CAPTURA: qué mostrar · comando]`.
- **README:** se actualiza la sección correspondiente al terminar cada cambio, no al final.
- Escritura sin muletillas de IA (skill `humanizer` antes de dar por cerrado un texto).

## Cosas a tener en cuenta

- `.gitattributes` fuerza LF; si un archivo aparece con CRLF (`git ls-files --eol`), el CI en Linux puede fallar.
- cAdvisor en Docker Desktop para Windows a veces no muestra los nombres de los contenedores.
- Nginx usa `zone` en el upstream para que el round robin sea parejo entre sus procesos (3/3/3 en 9 peticiones).
- Nginx vuelve a resolver `backend1..3` cada 10 s (`resolver 127.0.0.11` + `resolve`): un backend recreado con otra IP recupera su tráfico sin reiniciar Nginx.
- `stub_status` desde dentro del contenedor de Nginx: usar `127.0.0.1:8081`, no `localhost` (Alpine lo resuelve a IPv6 y Nginx escucha en IPv4). Desde otro contenedor: `nginx:8081`.
- La ruta `/lento?ms=` existe para generar latencia observable en Grafana y en k6; está acotada a 2000 ms.
- El primer arranque de Grafana (volumen vacío) tarda ~90 s: por eso su healthcheck tiene `start_period: 120s`.
- `GET /` devuelve HTML si el cliente lo pide (`Accept: text/html`, un navegador) y JSON en los demás casos (curl, k6, CI).
- `/metrics` no sale por Nginx (responde 404): Prometheus lo lee directo en cada backend. Para verlo a mano: `docker compose exec nginx wget -qO- http://backend1:5000/metrics`.
