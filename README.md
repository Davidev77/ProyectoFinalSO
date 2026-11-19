<div align="center">

# Tríada

**Tres backends Flask detrás de Nginx, con balanceo de carga y monitoreo con Prometheus y Grafana, todo en Docker.**

![CI](https://github.com/Davidev77/ProyectoFinalSO/actions/workflows/ci.yml/badge.svg?branch=develop)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3-000000?logo=flask&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-1.27-009639?logo=nginx&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-monitoreo-E6522C?logo=prometheus&logoColor=white)
![Grafana](https://img.shields.io/badge/Grafana-dashboards-F46800?logo=grafana&logoColor=white)

Proyecto final de Sistemas Operativos · Universidad Autónoma de Occidente (UAO) · 2026

</div>

---

## Qué hace

1. Nginx recibe las peticiones en `http://localhost:8080` y las reparte en turnos (round robin) entre tres instancias del backend.
2. Cada instancia responde con su número, así se ve a cuál fue cada petición.
3. Cada instancia expone `/metrics` con la cantidad de peticiones y su duración.
4. Prometheus recolecta esas métricas, las de Nginx y las de cada contenedor; Grafana las muestra en un dashboard.

## Estado del proyecto

| Pieza | Fase | Estado |
| --- | --- | --- |
| Backends Flask con métricas | 1 · Manuel | ⏳ en curso |
| Nginx con balanceo y `stub_status` | 1 · Manuel | ⏳ en curso |
| `docker-compose.yml` base y CI | 1 · Manuel | ⏳ en curso |
| Prometheus, exporter, cAdvisor y Grafana | 2 · Christian | ⏳ pendiente |
| Pruebas de carga con k6 | 3 · Eddie | ⏳ pendiente |

## Arquitectura

> Pendiente · Fase 1 (Manuel): diagrama mermaid del flujo host → Nginx → backends y explicación corta.

## Puesta en marcha

### Requisitos

> Pendiente · Fase 1 (Manuel): Docker Desktop, Git y lo necesario para correr las pruebas.

### 1. Clonar el repositorio

```powershell
git clone https://github.com/Davidev77/ProyectoFinalSO.git
cd ProyectoFinalSO
```

### 2. Levantar la infraestructura

> Pendiente · Fase 1 (Manuel).

### 3. Verificar que todo funciona

> Pendiente · Fase 1 (Manuel).

## URLs de acceso

| Servicio | URL | Credenciales |
| --- | --- | --- |
| Aplicación (Nginx) | http://localhost:8080 | — |
| Prometheus | Pendiente · Fase 2 | — |
| Grafana | Pendiente · Fase 2 | Pendiente · Fase 2 |
| cAdvisor | Pendiente · Fase 2 | — |

## Verificar el balanceo de carga

> Pendiente · Fase 1 (Manuel): comando para ver el reparto entre instancias, la cabecera `X-Upstream` y el log de Nginx.

## Monitoreo

> Pendiente · Fase 2 (Christian): cómo revisar los targets de Prometheus y abrir el dashboard «Infraestructura SO».

## Pruebas de carga

> Pendiente · Fase 3 (Eddie): instalar k6, comando para correr la prueba y cómo leer el resultado.

## Comandos

> Pendiente · Fase 1 (Manuel): tabla de comandos de uso diario.

## Integración continua

> Pendiente · Fase 1 (Manuel): qué revisa el pipeline en cada pull request.

## Estructura

```
backend/            app Flask, Dockerfile y pruebas
nginx/              nginx.conf
monitoring/         Prometheus y Grafana (Fase 2)
k6/                 pruebas de carga (Fase 3)
docs/               CONTRATO.md y documentos de diseño
.github/workflows/  CI
docker-compose.yml
```

## Flujo de trabajo

- `main` solo recibe la entrega final; el trabajo se integra en `develop`.
- Cada fase trabaja en su rama (`fase1-base`, `fase2-monitoreo`, `fase3-carga`) y abre un pull request hacia `develop`.
- El CI debe estar en verde para fusionar.
- Los nombres compartidos entre fases (servicios, puertos, métricas) están en [`docs/CONTRATO.md`](docs/CONTRATO.md).

## Documentación

| Documento | Contenido |
| --- | --- |
| [`docs/CONTRATO.md`](docs/CONTRATO.md) | Servicios, puertos, rutas y métricas que comparten las fases |
| [Informe (Google Docs)](https://docs.google.com/document/d/1MPO4G44Ge-d0srosCop8E2RMMqkFC38_iHEAW0BXBCg/edit) | Informe del proyecto en formato APA 7 |

## Autores

Eddie Santiago Delgado Campo · Christian David Home Acero · Manuel Betancurt Pérez

## Licencia

Proyecto académico (Sistemas Operativos, UAO, 2026). Sin licencia definida.
