# BuscaVuelo

Busca fines de semana largos (jueves → domingo / viernes → lunes) al mejor precio en **millas** y en **pesos** en Aerolíneas Argentinas.

**Web:** https://diegogagliardi92.github.io/buscaVuelo/

## Uso

- **Web:** `index.html` corre todo en el navegador (la API de Aerolíneas permite CORS), sin servidor. Localmente: doble clic en `BuscaVuelo.bat`.
- **Consola** (Python 3 + `requests`): `python buscavuelo.py BUE BRC 2026-11 2026-12 --finde --pax 3`. Guarda cada búsqueda en `historial.csv`.

Precios por adulto.

## Sumar otra aerolínea

Una función con la firma de `aerolineas(origen, destino, mes, millas)` agregada a `FUENTES`, en `index.html` (JS) y/o `buscavuelo.py`.
