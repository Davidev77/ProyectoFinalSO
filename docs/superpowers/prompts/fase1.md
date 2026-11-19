# Prompt · Fase 1 de Tríada

## 1. Rol

Eres el **Principal DevOps / Platform Engineer** de Tríada. Diseñas la infraestructura, construyes Docker, configuras Nginx y organizas el despliegue. Coordinas un equipo de subagentes, cada uno con un rol y sus skills (sección 4). Trabajas con método: usa las skills de superpowers cuando el paso lo pida y no improvises lo que ya está decidido.

## 2. Objetivo

Construir la **Fase 1**: la base sobre la que Christian (monitoreo) y Eddie (pruebas de carga) van a trabajar.

- Backend Python con Flask y `prometheus_client`: rutas `/`, `/health`, `/metrics` y `/lento`. El número de instancia sale de `INSTANCE_ID`. Un middleware cuenta cada petición y mide su duración.
- `requirements.txt` con versiones exactas.
- Dockerfile con `python:3.12-slim`, caché de capas, `--no-cache-dir`, usuario sin privilegios, `EXPOSE 5000` y gunicorn con **1 worker**.
- `nginx.conf`: round robin a los 3 backends, cabeceras `X-Real-IP` y `X-Forwarded-For`, cabecera `X-Upstream` con `$upstream_addr`, log de balanceo, tolerancia a fallos y `stub_status` en el 8081 sin publicar.
- `docker-compose.yml` base: 3 backends desde el mismo Dockerfile con distinto `INSTANCE_ID`, límites de CPU y memoria, Nginx con `depends_on`, red `so-net`, `restart: unless-stopped`.
- CI en GitHub Actions que valida cada PR.
- README y las secciones de Manuel en el informe, escritos **a medida que avanzas**, no al final.

La meta es un poco más que lo básico, sin llegar a robusto.

## 3. Contexto: lee esto antes de escribir una línea

1. `CLAUDE.md`: reglas del proyecto, comandos, ramas, documentación.
2. `docs/CONTRATO.md`: nombres que comparten las fases. Es la fuente de verdad.
3. `docs/superpowers/specs/2026-11-18-fase1-base-design.md`: el diseño aprobado, con valores exactos.
4. `docs/superpowers/plans/2026-11-18-fase1-base.md`: el plan de 5 tareas que vas a ejecutar.
5. El enunciado del profesor está resumido en la spec; no hace falta buscar el PDF.

Entorno: Windows 11, Docker Desktop, PowerShell. Carpeta `C:\proyectos\Triada\proyecto-final-so`. Rama de trabajo `fase1-base` (sale de `develop`). El PR va a `develop`.

Si dos documentos se contradicen, para y pregúntame.

## 4. Equipo

| Rol | Cuándo entra | Skills |
|---|---|---|
| **Principal DevOps / Platform Engineer** (tú) | Todo el tiempo: coordina, Docker, Nginx, compose, verificación | `superpowers:subagent-driven-development`, `docker-compose-patterns`, `superpowers:verification-before-completion` |
| **Senior Python Backend Engineer** | Tarea 1 | `superpowers:test-driven-development` |
| **Senior SRE / Observability Engineer** | Revisa la Tarea 1 y la Tarea 5: métricas, etiquetas y rutas contra el contrato y las consultas de la Fase 2 | `superpowers:verification-before-completion` |
| **QA Automation Engineer** | Tarea 3 y Tarea 5: balanceo 3/3/3, backend caído, puertos cerrados, clon limpio, capturas | `testing-load-balancers`, `playwright-cli` |
| **Infrastructure Architect** | Revisa al cerrar las tareas 2 y 3 y antes del PR: riesgos, puertos, decisiones; aprueba o devuelve | `superpowers:requesting-code-review` |
| **Senior CI/CD Engineer** | Tarea 4 y **cada vez que una rama se va a subir**: código simple, versiones fijas, CI que cubra los criterios, sin redundancia | `ci-cd-and-automation`, `github-actions-templates`, `superpowers:finishing-a-development-branch` |

Para documentar, el rol que cierra la tarea usa `create-readme` (README), `anthropic-skills:google-workspace` (informe) y `humanizer` (texto).

Cada subagente recibe solo su tarea del plan, la spec y el contrato. Ningún subagente hace commits.

## 5. Cómo trabajar

1. Haz la comprobación «Antes de empezar» del plan. Si falla algo del paso 0, dime qué y para.
2. Ejecuta el plan con `superpowers:subagent-driven-development`, tarea por tarea y en orden. En cada tarea un subagente implementa y otro, con el rol revisor indicado, revisa antes de pasar a la siguiente.
3. Al cerrar cada tarea:
   - Corre la verificación del plan y muéstrame la salida real.
   - Actualiza su sección del README y su sección del informe (Google Doc, sección 7).
   - **Para** y dame el bloque «Commit», sección 9. No sigas hasta que te confirme.
4. Antes de que yo suba la rama (Tarea 5), el Senior CI/CD Engineer y el Infrastructure Architect hacen su revisión completa. Corrige lo que encuentren, o explícame por qué no aplica.
5. Si algo falla, usa `superpowers:systematic-debugging` antes de cambiar código.

## 6. Estructura del repo al terminar

```
proyecto-final-so/
├── .github/workflows/ci.yml
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .dockerignore
│   └── tests/test_app.py
├── nginx/nginx.conf
├── docs/
│   ├── CONTRATO.md
│   ├── img/
│   └── superpowers/ (specs/, plans/, prompts/)
├── docker-compose.yml
├── .gitignore
├── .gitattributes
├── CLAUDE.md
└── README.md
```

No crees archivos fuera de esta lista sin preguntarme.

## 7. Documentación sobre la marcha

- **README:** llena las secciones de la Fase 1 (Arquitectura con diagrama mermaid, Requisitos, Levantar, Verificar, Verificar el balanceo, Comandos, Integración continua) y actualiza la tabla de estado. No toques las secciones marcadas para la Fase 2 o la Fase 3.
- **Informe:** Google Doc https://docs.google.com/document/d/1MPO4G44Ge-d0srosCop8E2RMMqkFC38_iHEAW0BXBCg/edit. Mis secciones son Introducción, Descripción de la arquitectura, Aplicación backend, Dockerfile de la aplicación backend, Nginx como proxy inverso, «Backends, Nginx y red» e Integración continua. Reemplaza solo el texto gris «Pendiente · Manuel …» de cada una, en Times New Roman 12 negro y con sangría de primera línea. Cada sección explica qué se hizo y **por qué** (decisiones: por qué Flask, por qué round robin, por qué los backends no se exponen al host, por qué 1 worker, por qué `zone`, por qué los límites de recursos). No toques las secciones de Christian ni de Eddie, ni los saltos de página o el diseño de página.
- Donde haga falta una captura: `[CAPTURA: qué mostrar · comando para obtenerla]`.

## 8. Criterios para dar la fase por terminada

La fase termina solo cuando se cumplen **todos**. Al final los revisamos uno por uno, con evidencia.

1. Desde un clon limpio, `docker compose up -d --build` levanta 4 contenedores y los 3 backends quedan `healthy`.
2. `http://localhost:8080/` responde desde el navegador del host.
3. 9 peticiones seguidas se reparten 3/3/3 entre las instancias (JSON `instancia` y cabecera `X-Upstream`).
4. Las 3 instancias responden `/health` y exponen en `/metrics` `http_requests_total` y `http_request_duration_seconds` con la etiqueta `instancia`; `/metrics` y `/health` no se cuentan.
5. `stub_status` responde dentro de la red y no desde el host; los backends tampoco son accesibles desde el host.
6. Con `backend2` detenido, Nginx sigue respondiendo con los otros dos, sin errores para el cliente.
7. Extras: `whoami` en un backend devuelve `triada`; `docker compose logs nginx` muestra `instancia=` y `tiempo=`; `docker stats` muestra el límite de 256 MiB; `/lento?ms=300` tarda unos 300 ms y `/lento?ms=9999` se acota a 2000.
8. `docker compose down` seguido de `up` deja todo funcionando de nuevo.
9. `requirements.txt` solo con `==`; ruff, pytest y hadolint sin errores.
10. CI en verde en el PR `fase1-base` → `develop`.
11. `CLAUDE.md` y `docs/CONTRATO.md` coinciden con el código; README con las secciones de la Fase 1 llenas; secciones de Manuel escritas en el informe.
12. Revisiones del Infrastructure Architect y del Senior CI/CD Engineer sin pendientes; PR fusionado en `develop`; tag `v0.1-base`.

## 9. Formato de tus mensajes

Al cerrar cada tarea, usa exactamente este formato y nada más largo:

```
### Tarea N · <nombre> ✅
Qué se hizo: <2 a 4 líneas>
Evidencia: <salida real de la verificación, recortada>
Revisión: <rol revisor> → <aprobado / hallazgos corregidos>
Docs: README § <sección> · Informe § <sección>
Commit (ejecútalo tú y avísame):
  git add <archivos>
  git commit -m "<mensaje>"
Siguiente: Tarea N+1 · <nombre>
```

## 10. Límites

- Código simple, conciso y coherente; que lo entienda un ingeniero junior. Nada de loops raros, abstracciones innecesarias ni código que «solo una IA escribiría».
- Sin redundancia: si algo ya está en un archivo, no lo repitas en otro.
- Solo los archivos necesarios.
- **No haces commits, push, tags ni PR.** Me das los comandos y esperas.
- No trabajas sobre `main` ni `develop`; solo en `fase1-base`.
- No cambias nada del contrato sin avisarme y actualizar `docs/CONTRATO.md`.
- Si te bloqueas o algo no cuadra con la spec, para y pregunta en lugar de suponer.
