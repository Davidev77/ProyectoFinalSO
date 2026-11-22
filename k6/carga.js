import http from "k6/http";
import { check, sleep } from "k6";
import { Counter } from "k6/metrics";

// Parámetros desde la terminal: -e ESCENARIO=normal|pico  -e VUS_PICO=100  -e BASE_URL=...
const BASE_URL = __ENV.BASE_URL || "http://localhost:8080";
const ESCENARIO = __ENV.ESCENARIO || "normal";
const VUS_PICO = Number(__ENV.VUS_PICO || 100);

// Un contador por instancia: cuenta cuántas respuestas llegaron de cada una
const instancia1 = new Counter("peticiones_instancia1");
const instancia2 = new Counter("peticiones_instancia2");
const instancia3 = new Counter("peticiones_instancia3");

// Cada escenario define su forma (etapas) y la pausa del usuario entre peticiones
const escenarios = {
  normal: {
    pausa: 1,
    etapas: [
      { duration: "1m", target: 20 }, // subida gradual
      { duration: "3m", target: 20 }, // carga sostenida
      { duration: "30s", target: 0 }, // bajada
    ],
  },
  pico: {
    pausa: 0.2,
    etapas: [
      { duration: "1m", target: 20 }, // calentamiento
      { duration: "1m", target: VUS_PICO }, // subida rápida
      { duration: "2m", target: VUS_PICO }, // sostiene el pico
      { duration: "1m", target: 0 }, // bajada
    ],
  },
};

if (!escenarios[ESCENARIO]) {
  throw new Error(`ESCENARIO debe ser "normal" o "pico", no "${ESCENARIO}"`);
}

const escenario = escenarios[ESCENARIO];

export const options = {
  stages: escenario.etapas,
  // Criterios de aprobación de la prueba de carga
  thresholds: {
    http_req_duration: ["p(95)<500"], // p95 menor a 500 ms
    http_req_failed: ["rate<0.01"], // errores menores a 1 %
    checks: ["rate>0.99"], // los checks fallidos también reprueban la prueba
  },
  summaryTrendStats: ["avg", "min", "med", "max", "p(90)", "p(95)", "p(99)"],
};

export default function () {
  // 1 de cada 5 peticiones es lenta: ocupa un hilo del backend 200 ms
  const lenta = Math.random() < 0.2;
  const url = lenta ? `${BASE_URL}/lento?ms=200` : `${BASE_URL}/`;

  const res = http.get(url, { headers: { Accept: "application/json" } });

  check(res, { "estado 200": (r) => r.status === 200 });

  // Tanto / como /lento devuelven {"instancia": "1" | "2" | "3", ...}
  if (res.status === 200) {
    const quien = res.json("instancia");
    if (quien === "1") instancia1.add(1);
    if (quien === "2") instancia2.add(1);
    if (quien === "3") instancia3.add(1);
  }

  sleep(escenario.pausa);
}
